"""Check a small curated set of issuer-owned call pages, not aggregator assertions.

Both the page and an explicit current submission window are necessary. An
unavailable issuer page leaves the previously conservative state unchanged.
"""
from datetime import date, datetime
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

MONTHS={"gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,"giugno":6,
        "luglio":7,"agosto":8,"settembre":9,"ottobre":10,"novembre":11,"dicembre":12}
DAY=r"(\d{1,2})\s+("+"|".join(MONTHS)+r")\s+(20\d{2})"
SPORT_START=re.compile(r"(?i)\bApertura\s+Piattaforma\s*:\s*"+DAY)
SPORT_END=re.compile(r"(?i)\bChiusura\s+Piattaforma\s*:\s*"+DAY)
CEPELL_FILING_END=re.compile(
    r"(?i)\bentro\s+e\s+non\s+oltre\s+(?:le\s+ore\s+\d{1,2}(?:[:.]\d{2})?\s+)?(?:del\s+giorno\s+|il\s+)?"+DAY
)
CATTOLICA=re.compile(r"(?i)\bdal\s+"+DAY+r"\s+al\s+"+DAY+r"\s+gli\s+Enti\s+interessati\s+potranno\s+candidare")
def _date(match,at=1):
    try:return date(int(match.group(at+2)),MONTHS[match.group(at+1).lower()],int(match.group(at))).isoformat()
    except (TypeError,ValueError,KeyError):return None

def parse_issuer_window(html,parser):
    soup=BeautifulSoup(html,"html.parser")
    for n in soup(["script","style","nav","footer","header"]):n.decompose()
    txt=" ".join((soup.body or soup).stripped_strings)[:90000]
    if parser=="sport":
        a,b=SPORT_START.search(txt),SPORT_END.search(txt)
        if not (a and b and re.search(r"(?i)\bcandidat(?:i|ure|ura|arsi)\b",txt)):return None
        start,end=_date(a),_date(b)
    elif parser=="cattolica":
        m=CATTOLICA.search(txt)
        if not m:return None
        start,end=_date(m),_date(m,4)
    elif parser=="cepell":
        m=CEPELL_FILING_END.search(txt)
        if not m or not re.search(r"(?i)\\b(?:proposte|domande|candidature)\\b",txt):return None
        start=None
        end=_date(m)
    else:return None
    if not end or (start and start>end):return None
    return {"opening_date":start,"deadline":end}

def apply_issuer_evidence(row,source,checks,session,eligible_to_fetch,now):
    if row.get("source_id")!="volto" or row.get("funding_status")=="CHIUSO":
        return row
    path=urlparse(row.get("url") or "").path.lower()
    check=next((c for c in checks if c["source_id"]==row.get("source_id")
                and path.startswith(c["match_path"])),None)
    if not check:return row
    url=check["official_url"]
    if not eligible_to_fetch(url,session):return row
    response=None
    try:
        response=session.get(url,timeout=16,stream=True,allow_redirects=True)
        response.raise_for_status()
        final=urlparse(response.url)
        if (final.scheme!="https" or final.hostname!=urlparse(url).hostname
                or final.port not in (None,443)
                or "text/html" not in response.headers.get("Content-Type","")):
            return row
        data=bytearray()
        for chunk in response.iter_content(32768):
            data.extend(chunk)
            if len(data)>1_000_000:return row
        response._content=bytes(data)
        window=parse_issuer_window(response.text,check["parser"])
        if not window:return row
        today=date.fromisoformat(now[:10])
        row.update(window)
        row["deadline_source"]=response.url
        if window["opening_date"]:row["opening_evidence"]=response.url
        row["status_evidence"]=response.url
        row["source_open_confirmed"]=bool(window["opening_date"] and window["opening_date"]<=today.isoformat()<=window["deadline"])
        row["closure_confirmed"]=window["deadline"]<today.isoformat()
        row["status_basis"]="Finestra di candidatura verificata presso l'ente erogatore"
        row["issuer_verified_at"]=now
        row["issuer_official_url"]=response.url
        docs=list(row.get("documents") or [])
        if not any(d.get("url")==response.url for d in docs):
            docs.append({"label":"Bando presso l'ente erogatore","url":response.url})
        row["documents"]=docs
        return row
    except Exception:
        return row
    finally:
        if response is not None:response.close()
