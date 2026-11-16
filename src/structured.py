"""Extract dated application windows from official structured funding detail pages."""
import re
from datetime import date, datetime
from bs4 import BeautifulSoup
from classify import parse_deadline

DATE_TOKEN = r"(?:[A-Za-zÀ-ÿ]{3,12},?\s*)?(\d{1,2})[./-](\d{1,2})[./-](20\d{2})"
DEADLINE = re.compile(r"(?i)(?:^|\b)(?:scadenza|termine (?:per |di )?(?:la )?(?:presentazione|candidatura|domande)|deadline|apply by)\s*[:–-]?\s*"+DATE_TOKEN)
OPENING = re.compile(r"(?i)(?:domande dal|candidature dal|apertura (?:del |delle )?(?:bando|domande|candidature)|presentazione domande dal)\s*[:–-]?\s*"+DATE_TOKEN)
STATUS = re.compile(r"(?i)\bstato\s*[:–-]?\s*(aperto|aperta|attivo|attiva|chiuso|chiusa|scaduto|scaduta)\b")
BENEFICIARIES = re.compile(r"(?i)\b(?:rivolto a|chi può partecipare|soggetti beneficiari|beneficiari)\s*[:–-]?\s*(.{8,260})")

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
    state=STATUS.search(txt)
    source_open=bool(state and state.group(1).lower() in ("aperto","aperta","attivo","attiva"))
    source_closed=bool(state and state.group(1).lower() in ("chiuso","chiusa","scaduto","scaduta"))
    beneficiaries=BENEFICIARIES.search(txt)
    return {
      "deadline":deadline,"opening_date":opening,"source_open_confirmed":source_open,
      "closure_confirmed":source_closed,
      "opening_evidence":url if opening else None,
      "deadline_source":url if deadline else None,
      "status_evidence":url if state else None,
      "beneficiaries_excerpt":beneficiaries.group(0).strip()[:270] if beneficiaries else None
    }
