"""Extract dated application windows from official structured funding detail pages."""
import re
from datetime import date, datetime
from bs4 import BeautifulSoup
from classify import parse_deadline

DATE_TOKEN = r"(?:[A-Za-zÀ-ÿ]{3,12},?\s*)?(\d{1,2})[./-](\d{1,2})[./-](20\d{2})"
DEADLINE = re.compile(r"(?i)(?:^|\b)(?:data scadenza|scadenza|termine (?:per |di )?(?:la )?(?:presentazione|candidatura|domande)|deadline|apply by)\s*[:–-]?\s*"+DATE_TOKEN)
OPENING = re.compile(r"(?i)(?:domande dal|candidature dal|apertura (?:del |delle )?(?:bando|domande|candidature)|presentazione domande dal)\s*[:–-]?\s*"+DATE_TOKEN)
STATUS = re.compile(r"(?i)\b(?:stato|opportunity status|status)\s*[:–-]?\s*(in corso|aperto|aperta|attivo|attiva|open|chiuso|chiusa|scaduto|scaduta|closed)\b")
# Turin detail pages encode an active application window with dal/al dates.
TURIN_WINDOW=re.compile(r"(?i)\battivo\b\s*dal\s*[:–-]?\s*"+DATE_TOKEN+
                         r"\s*al\s*[:–-]?\s*"+DATE_TOKEN)
BENEFICIARIES = re.compile(r"(?i)\b(?:rivolto a|chi può partecipare|soggetti beneficiari|beneficiari)\s*[:–-]?\s*(.{8,260})")

MONTHS={"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
EN_DATE=r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})"
EN_DEADLINE=re.compile(r"(?i)\bdeadline\s*[:–-]?\s*"+EN_DATE)
EN_OPENING=re.compile(r"(?i)\bopening date\s*[:–-]?\s*"+EN_DATE)
def _english_date(match):
    if not match:return None
    try:return date(int(match.group(3)),MONTHS[match.group(2).lower()],int(match.group(1))).isoformat()
    except (ValueError,KeyError):return None

IT_MONTHS={"gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,"giugno":6,"luglio":7,"agosto":8,"settembre":9,"ottobre":10,"novembre":11,"dicembre":12}
CRT_TEXT_DEADLINE=re.compile(r"(?i)(?:\d+[°ªa]?\s+|prima\s+|seconda\s+|unica\s+)?scadenza\b.{0,35}?\b(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(20\d{2})")
CRT_WINDOW_DEADLINE=re.compile(r"(?i)scadenza\s*[:–-]?\s*tra il\s*\d{1,2}[./-]\d{1,2}[./-]20\d{2}\s+e il\s*(\d{1,2})[./-](\d{1,2})[./-](20\d{2})")
def _crt_dates(text):
    dates=[]
    for match in CRT_TEXT_DEADLINE.finditer(text):
        try:dates.append(date(int(match.group(3)),IT_MONTHS[match.group(2).lower()],int(match.group(1))).isoformat())
        except (ValueError,KeyError):pass
    for match in CRT_WINDOW_DEADLINE.finditer(text):
        datestr=_date(match)
        if datestr:dates.append(datestr)
    return max(dates) if dates else None

def _date(match):
    if not match:return None
    try:return date(int(match.group(3)),int(match.group(2)),int(match.group(1))).isoformat()
    except ValueError:return None

def structured_facts(html,url):
    """Only label-adjacent facts. Keep URL for provenance; never assert eligibility."""
    soup=BeautifulSoup(html,"html.parser")
    for node in soup(["script","style","nav","footer","header"]):node.decompose()
    # Drupal themes may render status and application dates outside <main>/<article>.
    # Read the complete body, after removing navigational noise.
    main=soup.body or soup
    txt=" ".join(main.stripped_strings)[:50000]
    # Avoid matching 'Scadenza' in an unrelated phrase by requiring the date nearby.
    deadline=_date(DEADLINE.search(txt))
    opening=_date(OPENING.search(txt))
    if not deadline:deadline=_english_date(EN_DEADLINE.search(txt))
    if not opening:opening=_english_date(EN_OPENING.search(txt))
    if "www.fondazionecrt.it" in url:
        crt_deadline=_crt_dates(txt)
        if crt_deadline:deadline=crt_deadline
    window=TURIN_WINDOW.search(txt) if "bandi.comune.torino.it" in url else None
    if window:
        opening=_date(window)
        try:
            deadline=date(int(window.group(6)),int(window.group(5)),int(window.group(4))).isoformat()
        except ValueError:
            pass
    state=STATUS.search(txt)
    source_open=bool((state and state.group(1).lower() in ("in corso","aperto","aperta","attivo","attiva","open")) or window)
    source_closed=bool(state and state.group(1).lower() in ("chiuso","chiusa","scaduto","scaduta","closed"))
    beneficiaries=BENEFICIARIES.search(txt)
    return {
      "deadline":deadline,"opening_date":opening,"source_open_confirmed":source_open,
      "closure_confirmed":source_closed,
      "opening_evidence":url if opening else None,
      "deadline_source":url if deadline else None,
      "status_evidence":url if state else None,
      "beneficiaries_excerpt":beneficiaries.group(0).strip()[:270] if beneficiaries else None
    }
