#!/usr/bin/env python3
"""Send one restrained Resend digest for newly OPEN, relevant calls.

A public state ledger stores only opportunity identifiers/statuses, never email
addresses or credentials. The first run bootstraps silently (no old alerts).
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import re
from html import escape
import json
from email_template import make_message
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PROJECT_TYPES={"finanziamento potenziale","call progettuale da verificare","non classificato"}
FROM_ADDRESS="Opera+ Funding <notifiche@updates.opera.plus>"
DASHBOARD="https://jeckodevelopment.com/dev/funding/"
MAX_DAILY=10
MAX_MONTHLY=100
MAX_ITEMS=12
NOTIFIABLE_STATES={"APERTO","IN ARRIVO","DA VERIFICARE"}
ADEQUACY={"ALTA":0,"MEDIA":1,"BASSA":2}

def is_open(row):
    """Strict actual-open classification for backwards compatibility."""
    return (row.get("funding_status")=="APERTO" and
            row.get("opportunity_type") in PROJECT_TYPES)

def is_notifiable(row):
    """Include all newly tracked genuine calls, including BASSA and upcoming.

    A notice with unconfirmed opening is clearly described as TO VERIFY,
    never as an open call.
    """
    return (row.get("funding_status") in NOTIFIABLE_STATES and
            row.get("opportunity_type") in PROJECT_TYPES and
            row.get("adequacy_label") in ADEQUACY and
            row.get("link_status")!="non disponibile")

def identity(row):
    # Immutable canonical opportunity identity, independent of presentation ID.
    return str(row.get("id") or row.get("url") or "").strip()

def snapshot(rows):
    return {identity(r): (r.get("funding_status") if is_notifiable(r) else "ALTRO")
            for r in rows if identity(r)}

def candidates(rows, previous, alerted):
    out=[]
    seen=set()
    for r in rows:
        key=identity(r)
        if (not key or key in seen or key in alerted or
                not is_notifiable(r) or previous.get(key)==r.get("funding_status")):
            continue
        link=r.get("url")
        parsed=urlparse(link or "")
        if parsed.scheme!="https" or not parsed.hostname:
            continue
        seen.add(key)
        out.append(r)
    return sorted(out,key=lambda r:(
        ADEQUACY.get(r.get("adequacy_label"),99),
        0 if r.get("funding_status")=="APERTO" else 1,
        str(r.get("deadline") or "9999-12-31"),
        r.get("title") or ""))


def post_resend(key,recipient,subject,html,text_body,idempotency):
    payload=json.dumps({"from":FROM_ADDRESS,"to":[recipient],"subject":subject,
                        "html":html,"text":text_body},ensure_ascii=False).encode("utf-8")
    request=Request("https://api.resend.com/emails",data=payload,method="POST",headers={
        "Authorization":"Bearer "+key,
        "Content-Type":"application/json",
        "User-Agent":"OperaFunding/1.0 (https://github.com/jeckodevelopment/opera-funding)",
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

def parse_recipients(value):
    """Comma-, semicolon- or newline-separated addresses, with no duplicates."""
    addresses=[]
    for raw in re.split(r"[,;\n]+", value or ""):
        address=raw.strip()
        if not address:
            continue
        # Prevent header injection and invalid addresses before making API calls.
        if (not re.fullmatch(r"[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+",address)
                or len(address)>254):
            raise ValueError("FUNDING_ALERT_RECIPIENT contiene un indirizzo non valido")
        if address.casefold() not in {v.casefold() for v in addresses}:
            addresses.append(address)
    if len(addresses)>10:
        raise ValueError("Sono consentiti al massimo 10 destinatari")
    return addresses

def persist(state_path,stored):
    state_path.parent.mkdir(parents=True,exist_ok=True)
    state_path.write_text(json.dumps(stored,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def recipient_token(api_key,address):
    """HMAC avoids publishing email addresses or reversible plain hashes in git."""
    return hmac.new(api_key.encode("utf-8"),address.casefold().encode("utf-8"),"sha256").hexdigest()

def run(rows,state_path,now,api_key=None,recipient=None,sender=post_resend):
    current=snapshot(rows)
    stored=json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if stored is None:
        state={"version":2,"statuses":current,"alerted_ids":[],
               "sent_days":{},"sent_months":{}}
        persist(state_path,state)
        print("Notifiche: prima esecuzione; catalogo iniziale registrato senza inviare email")
        return "bootstrapped"
    if stored.get("version")==1:
        # Migrate the historical strict-OPEN baseline without treating all
        # previously indexed opportunities as newly discovered at rollout.
        previous=stored.get("statuses") or {}
        stored["statuses"]={
            ident: (current.get(ident) if ident in current else old)
            for ident,old in previous.items()
        }
        stored["version"]=2
        persist(state_path,stored)
    if stored.get("version")!=2:
        raise RuntimeError("Versione del registro notifiche non supportata")
    alerted=set(stored.get("alerted_ids") or [])
    found=candidates(rows,stored.get("statuses") or {},alerted)
    day=now[:10]
    month=day[:7]
    if not api_key or not recipient:
        print("Notifiche non inviate: mancano credenziali o destinatari; lo storico non avanza")
        return "disabled"
    recipients=parse_recipients(recipient)
    if not recipients:
        raise ValueError("FUNDING_ALERT_RECIPIENT non contiene destinatari")
    if not found:
        stored["statuses"]=current
        persist(state_path,stored)
        print("Notifiche: nessuna nuova opportunità aperta")
        return "no-news"

    # Each recipient gets a distinct email and never sees the others. Persist
    # confirmations after EACH successful send, so partial failures can retry
    # only the recipients/opportunities still awaiting delivery.
    delivered=stored.setdefault("delivered",{})
    sent=0
    for address in recipients:
        token=recipient_token(api_key,address)
        already=set(delivered.get(token,[]))
        pending=[r for r in found if identity(r) not in already]
        if not pending:
            continue
        if (stored.get("sent_days",{}).get(day,0)>=MAX_DAILY or
                stored.get("sent_months",{}).get(month,0)>=MAX_MONTHLY):
            print("Notifiche: limite gratuito raggiunto; invii restanti rinviati")
            return "quota"
        for offset in range(0,len(pending),MAX_ITEMS):
            batch=pending[offset:offset+MAX_ITEMS]
            if (stored.get("sent_days",{}).get(day,0)>=MAX_DAILY or
                    stored.get("sent_months",{}).get(month,0)>=MAX_MONTHLY):
                print("Notifiche: limite gratuito raggiunto; invii restanti rinviati")
                return "quota"
            subject,html,text_body=make_message(batch)
            event_ids=sorted(identity(r) for r in batch)
            digest=sha256((token+"|"+",".join(event_ids)).encode("utf-8")).hexdigest()[:40]
            sender(api_key,address,subject,html,text_body,"opera-funding-"+digest)
            already.update(event_ids)
            delivered[token]=sorted(already)
            stored.setdefault("sent_days",{})[day]=stored.get("sent_days",{}).get(day,0)+1
            stored.setdefault("sent_months",{})[month]=stored.get("sent_months",{}).get(month,0)+1
            persist(state_path,stored)
            sent+=1

    # Only mark the opportunities globally complete when every configured
    # destination has received them. Outstanding calls remain retryable.
    alerted.update(identity(r) for r in found)
    stored["alerted_ids"]=sorted(alerted)
    stored["statuses"]=current
    stored.pop("delivered",None)
    persist(state_path,stored)
    print(f"Notifiche: {sent} email individuali per {len(found)} opportunità")
    return "sent" if sent else "no-news"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--catalog",default="data/opportunities.json")
    parser.add_argument("--state",default="data/notification-state.json")
    parser.add_argument("--report",default="data/scan-status.json")
    args=parser.parse_args()
    rows=json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    report=json.loads(Path(args.report).read_text(encoding="utf-8"))
    sources=report.get("sources") or []
    if not sources:
        raise RuntimeError("Impossibile inviare notifiche senza report delle fonti")
    failed=[x.get("source_id") for x in sources if x.get("ok") is not True]
    if failed:
        print("Notifiche parziali: fonti non aggiornate "+
              ", ".join(str(x) for x in failed)+
              "; il digest usa le opportunità verificate nel catalogo")
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    run(rows,Path(args.state),now,os.getenv("RESEND_API_KEY"),os.getenv("FUNDING_ALERT_RECIPIENT"))

if __name__=="__main__":
    main()
