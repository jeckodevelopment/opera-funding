"""Distinct application windows for the annual Fondazione CRT Ordinarie call.

Only extract explicitly labelled application periods from the official call page.
Keep each deadline, application type and edition identifiable across annual renewals.
"""
import re
from datetime import date
from bs4 import BeautifulSoup

ORDINARIE_PATH="/bandi-progetti/arte-cultura-ordinarie/"
DATE=r"(\d{1,2}/\d{1,2}/20\d{2})"
WINDOW=re.compile(r"(?i)\b(prima|seconda|unica)\s+scadenza\s*:\s*tra il\s*"+DATE+r"\s+e il\s*"+DATE)
TYPE=re.compile(r"(?i)(progetto|sostegno\s+attivit[àa])\s*[–-]\s*bando\s+ordinarie\s+(20\d{2})")
TYPE_LABEL={"progetto":"Progetto","sostegno attività":"Sostegno attività","sostegno attivita":"Sostegno attività"}
ORDINAL={"prima":1,"seconda":2,"unica":1}

def _iso(text):
    d,m,y=map(int,text.split("/"))
    return date(y,m,d).isoformat()

def extract_ordinarie_windows(html,url):
    if ORDINARIE_PATH not in url.lower():return []
    soup=BeautifulSoup(html,"html.parser")
    for node in soup(["script","style","nav","footer","header"]):node.decompose()
    body=soup.select_one("main") or soup.body or soup
    text=" ".join(body.stripped_strings)
    matches=list(TYPE.finditer(text))
    # CRT exposes its edition as "In corso" beside the call heading.
    active_banner=bool(re.search(r"(?i)\\bin corso\\b",text[:450]))
    results=[]
    for window in WINDOW.finditer(text):
        nearest=next((m for m in reversed(matches) if m.start()<window.start()),None)
        if nearest is None:continue
        kind=TYPE_LABEL.get(nearest.group(1).lower().strip())
        if not kind:continue
        year=int(nearest.group(2))
        opening=_iso(window.group(2))
        closing=_iso(window.group(3))
        if opening>closing or closing[:4]!=str(year):continue
        ordinal=ORDINAL[window.group(1).lower()]
        label=f"{kind} · {window.group(1).capitalize()} scadenza"
        key=f"{year}-{kind.lower().replace(' ','-')}-{ordinal}-{closing}"
        results.append({"window_key":key,"window_label":label,"application_type":kind,
                        "edition_year":year,"opening_date":opening,"deadline":closing,
                        "deadline_source":url,"opening_evidence":url,
                        "official_in_progress":active_banner})
    # Avoid duplicated on-page mobile/desktop sections, but don't merge distinct deadlines.
    return list({r["window_key"]:r for r in results}.values())

def guidance_for_window(application_type):
    """Editorial ideas only, not a statement of eligibility or award conditions."""
    if application_type=="Sostegno attività":
        ideas=[
            "Consolidamento delle attività continuative di divulgazione musicale di Opera+",
            "Sviluppo di contenuti e strumenti didattici accessibili per il pubblico"
        ]
    else:
        ideas=[
            "Produzione di videolezioni e contenuti digitali di divulgazione dell'opera",
            "Laboratori extrascolastici di ascolto e cultura musicale per giovani e adulti"
        ]
    return {
      "project_ideas": ideas,
      "funding_scope_note": (
          "Il bando Ordinarie esclude le iniziative di spettacolo dal vivo, "
          "indirizzate da Fondazione CRT a NoteSipari e Orizzonti L.I.V.E. "
          "Gli spunti proposti non costituiscono conferma di ammissibilità."
      )
    }
