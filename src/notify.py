#!/usr/bin/env python3
"""Send one restrained Resend digest for newly OPEN, relevant calls.

A public state ledger stores only opportunity identifiers/statuses, never email
addresses or credentials. The first run bootstraps silently (no old alerts).
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PROJECT_TYPES={"finanziamento potenziale","call progettuale da verificare"}
FROM_ADDRESS="Opera+ Funding <notifiche@updates.opera.plus>"
DASHBOARD="https://jeckodevelopment.com/dev/funding/"
MAX_DAILY=10
MAX_MONTHLY=100
MAX_ITEMS=12
MIN_RELEVANCE=50

def is_open(row):
    return (row.get("funding_status")=="APERTO" and
            row.get("opportunity_type") in PROJECT_TYPES and
            row.get("source_open_confirmed") is True and
            row.get("link_status")=="raggiungibile" and
            int(row.get("relevance") or 0)>=MIN_RELEVANCE)

def identity(row):
    # IDs are canonicalized by catalog reconciliation. No broad title matching:
    # different call editions must not be merged.
    return str(row.get("id") or row.get("url") or "").strip()

def snapshot(rows):
    return {identity(r): ("APERTO" if is_open(r) else "ALTRO")
            for r in rows if identity(r)}

def candidates(rows, previous, alerted):
    out=[]
    seen=set()
    for r in rows:
        key=identity(r)
        if (not key or key in seen or key in alerted or
                not is_open(r) or previous.get(key)=="APERTO"):
            continue
        link=r.get("url")
        parsed=urlparse(link or "")
        if parsed.scheme!="https" or not parsed.hostname:
            continue
        seen.add(key)
        out.append(r)
    return sorted(out,key=lambda r:(-int(r.get("relevance") or 0),str(r.get("deadline") or ""),r.get("title") or ""))

def make_message(items):
    displayed=items[:MAX_ITEMS]
    count=len(items)
    subject=f"Opera+ Funding — {count} {'nuova opportunità aperta' if count==1 else 'nuove opportunità aperte'}"
    opening=f"Sono state rilevate {count} nuove opportunità aperte e potenzialmente pertinenti ai progetti culturali o formativi. L'ammissibilità deve essere verificata sui bandi ufficiali."
    html_items=[]
    lines=[]
    for row in displayed:
        title=str(row.get("title") or "Opportunità")
        issuer=str(row.get("issuer") or "Ente da verificare")
        deadline=str(row.get("deadline") or "Da verificare")
        url=row["url"]
        html_items.append(
            "<li><strong>"+escape(title)+"</strong><p>Fonte: "+escape(issuer)+
            " · Scadenza: "+escape(deadline)+"</p><a href=\""+escape(url,quote=True)+
            "\">Consulta la scheda originale</a></li>"
        )
        lines.append(f"- {title} | {issuer} | Scadenza: {deadline}\n  {url}")
    more=(f"\nAltre {count-MAX_ITEMS} opportunità nella dashboard." if count>MAX_ITEMS else "")
    body_html=(
        "<!doctype html><html lang=\"it\"><body style=\"font-family:Arial,sans-serif;"
        "max-width:640px;margin:24px auto;color:#17212b\">"
        "<h2>Opera+ Funding</h2><p>"+escape(opening)+"</p><ol>"+
        "".join(html_items)+"</ol>"+
        ("<p>"+escape(more.strip())+"</p>" if more else "")+
        "<p><a href=\""+DASHBOARD+"\">Apri la dashboard</a></p>"+
        "<p style=\"font-size:12px;color:#607080\">Notifica automatica informativa; "
        "verifica sempre requisiti, scadenze e disponibilità sui siti degli enti.</p>"
        "</body></html>"
    )
    text_body=opening+"\n\n"+"\n".join(lines)+more+"\n\nDashboard: "+DASHBOARD
    return subject,body_html,text_body

def post_resend(key,recipient,subject,html,text_body,idempotency):
    payload=json.dumps({"from":FROM_ADDRESS,"to":[recipient],"subject":subject,
                        "html":html,"text":text_body},ensure_ascii=False).encode("utf-8")
    request=Request("https://api.resend.com/emails",data=payload,method="POST",headers={
        "Authorization":"Bearer "+key,
        "Content-Type":"application/json",
        "Idempotency-Key":idempotency,
    })
    try:
        with urlopen(request,timeout=20) as response:
            if response.status!=200 and response.status!=201:
                raise RuntimeError("Invio non confermato dal provider")
            result=json.load(response)
    except (HTTPError,URLError,TimeoutError) as err:
        raise RuntimeError("Resend non ha confermato l'invio (controllare log e configurazione)") from err
    if not isinstance(result,dict) or not result.get("id"):
        raise RuntimeError("Resend non ha restituito un identificativo di invio")
    return result["id"]

def run(rows,state_path,now,api_key=None,recipient=None,sender=post_resend):
    current=snapshot(rows)
    stored=json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if stored is None:
        state={"version":1,"statuses":current,"alerted_ids":[],
               "sent_days":{},"sent_months":{}}
        state_path.parent.mkdir(parents=True,exist_ok=True)
        state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("Notifiche: prima esecuzione; catalogo iniziale registrato senza inviare email")
        return "bootstrapped"
    if stored.get("version")!=1:
        raise RuntimeError("Versione del registro notifiche non supportata")
    alerted=set(stored.get("alerted_ids") or [])
    found=candidates(rows,stored.get("statuses") or {},alerted)
    day=now[:10]
    month=day[:7]
    has_config=bool(api_key and recipient)
    # Maintain current snapshot even if notifications are disabled. It prevents
    # retrospectively emailing historical entries after configuring the secrets.
    if not has_config:
        stored["statuses"]=current
        state_path.write_text(json.dumps(stored,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("Notifiche disattivate: servono RESEND_API_KEY e FUNDING_ALERT_RECIPIENT")
        return "disabled"
    if len(found)==0:
        stored["statuses"]=current
        state_path.write_text(json.dumps(stored,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("Notifiche: nessuna nuova opportunità aperta")
        return "no-news"
    if (stored.get("sent_days",{}).get(day,0)>=MAX_DAILY or
            stored.get("sent_months",{}).get(month,0)>=MAX_MONTHLY):
        # Preserve old status so pending alerts can be sent on a later scan.
        print("Notifiche: raggiunto il limite di sicurezza gratuito, nessuna email inviata")
        return "quota"
    subject,html,text_body=make_message(found)
    event_ids=sorted(identity(r) for r in found)
    digest=sha256((recipient.lower().strip()+"|"+",".join(event_ids)).encode("utf-8")).hexdigest()[:40]
    sender(api_key,recipient,subject,html,text_body,"opera-funding-"+digest)
    stored["statuses"]=current
    alerted.update(event_ids)
    stored["alerted_ids"]=sorted(alerted)
    stored.setdefault("sent_days",{})[day]=stored.get("sent_days",{}).get(day,0)+1
    stored.setdefault("sent_months",{})[month]=stored.get("sent_months",{}).get(month,0)+1
    state_path.write_text(json.dumps(stored,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"Notifiche: riepilogo inviato per {len(found)} opportunità")
    return "sent"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--catalog",default="data/opportunities.json")
    parser.add_argument("--state",default="data/notification-state.json")
    parser.add_argument("--report",default="data/scan-status.json")
    args=parser.parse_args()
    rows=json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    report=json.loads(Path(args.report).read_text(encoding="utf-8"))
    sources=report.get("sources") or []
    if not sources or not all(source.get("ok") is True for source in sources):
        print("Notifiche non inviate: una o più fonti non sono state acquisite correttamente")
        return
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    run(rows,Path(args.state),now,os.getenv("RESEND_API_KEY"),os.getenv("FUNDING_ALERT_RECIPIENT"))

if __name__=="__main__":
    main()
