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
EN_VERIFIED_CALL_OPEN_UNTIL=re.compile(r"(?i)\\bthe\\s+call\\s+is\\s+open\\s+until\\s+"+EN_DATE)
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

CSP_FESTIVAL_PHASE=re.compile(r"(?i)le proposte dovranno pervenire entro il\s*(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(20\d{2})")
def _festival_windows(text):
    dates=[]
    for match in CSP_FESTIVAL_PHASE.finditer(text):
        try:dates.append(date(int(match.group(3)),IT_MONTHS[match.group(2).lower()],int(match.group(1))).isoformat())
        except (ValueError,KeyError):pass
    return sorted(set(dates))


# Source-specific official application date labels. These are not publication dates.
ITALIAN_DATE=r"(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(20\d{2})"
ALCOTRA_CLOSING=re.compile(r"(?i)\b(?:data\s+di\s+chiusura|chiusura)\s*[:–-]?\s*"+DATE_TOKEN)
ALCOTRA_OPENING=re.compile(r"(?i)\bdata\s+di\s+apertura\s*[:–-]?\s*"+DATE_TOKEN)
CSVNET_CLOSING=re.compile(r"(?i)\bscadenza(?:\s+del\s+bando)?\s*[:–-]?\s*(?:"+DATE_TOKEN+r"|"+ITALIAN_DATE+r")")
MIC_FORM_WINDOW=re.compile(
    r"(?i)\bdalle?\s+ore\s+\d{1,2}(?:[:.]\d{2})?\s+del\s+"+ITALIAN_DATE+
    r".{0,110}?\bfino\s+alle?\s+ore\s+\d{1,2}(?:[:.]\d{2})?\s+del\s+"+ITALIAN_DATE
)
PITER_LIST_CONTEXT=re.compile(r"(?i)candidature\s+nel\s+rispetto\s+di\s+3\s+date\s+predefinite\s*:")
def _piter_windows(text):
    marker=PITER_LIST_CONTEXT.search(text)
    if not marker:return []
    # Only the short list immediately after the official filing-dates label.
    excerpt=text[marker.end():marker.end()+140].split(".",1)[0]
    values=[]
    for m in re.finditer(ITALIAN_DATE,excerpt,re.I):
        parsed=_italian_date(m)
        if parsed:values.append(parsed)
    return sorted(set(values)) if len(set(values))==3 else []

ALCOTRA_EXPLICIT_CLOSED=re.compile(r"(?i)\bbando\s+chiuso\s+il\s+"+ITALIAN_DATE)
TORINO_APPLICATION_END=re.compile(r"(?i)\b(?:dal|dalle)\s+"+ITALIAN_DATE+r".{0,35}?\bal\s+"+ITALIAN_DATE+r"(?=\s|[.,;:]|$)")
TORINO_PROPOSAL_CLOSING=re.compile(
    r"(?i)\btermine\s+di\s+presentazione\s+delle\s+proposte\s+progettuali\s*:\s*"
    r"(?:ore\s+\d{1,2}(?:[.:]\d{2})?\s+)?(?:del\s+)?"+ITALIAN_DATE
)
TORINO_TEXTUAL_DEADLINE=re.compile(r"(?i)\b(?:scadenza(?:\s+(?:del\s+bando|delle\s+domande))?|termine\s+(?:di\s+)?presentazione\s+(?:(?:delle|delle\s+)?\s*)?(?:domande|candidature|proposte\s+progettuali))\s*[:–-]?\s*(?:entro\s+(?:il\s+)?)?"+ITALIAN_DATE)
TORINO_PUBLISHED_APPLICATION_PERIOD=re.compile(
    r"(?i)\bnel\s+periodo\s+compreso\s+tra\s+il\s+"+ITALIAN_DATE+
    r"\s+e\s+il\s+"+ITALIAN_DATE+
    r"(?=.{0,180}?\b(?:presentare\s+(?:istanza|domanda|richiesta)|presentazione\s+(?:di\s+)?(?:istanze|domande|richieste))\b)"
)
TORINO_NUMERIC_END=re.compile(r"(?i)\b(?:richiest[ae]|domand[ae]|candidatur[ae]|propost[ae]).{0,100}?\b(?:entro|al)\s*(?:il\s+)?"+DATE_TOKEN)
def _italian_date(match,start=1):
    if not match:return None
    try:return date(int(match.group(start+2)),IT_MONTHS[match.group(start+1).lower()],int(match.group(start))).isoformat()
    except (ValueError,KeyError,TypeError):return None
def _csvnet_deadline(txt):
    match=CSVNET_CLOSING.search(txt)
    if not match:return None
    if match.group(1):
        try:return date(int(match.group(3)),int(match.group(2)),int(match.group(1))).isoformat()
        except ValueError:return None
    return _italian_date(match,4)

def _date(match):
    if not match:return None
    try:return date(int(match.group(3)),int(match.group(2)),int(match.group(1))).isoformat()
    except ValueError:return None

def structured_facts(html,url):
    """Only label-adjacent facts. Keep URL for provenance; never assert eligibility."""
    soup=BeautifulSoup(html,"html.parser")
    summary=None
    for meta in soup.select('meta[name="description"], meta[property="og:description"]'):
        content=" ".join((meta.get("content") or "").split())
        if 45 <= len(content) <= 600:
            summary=content[:260]
            break
    for node in soup(["script","style","nav","footer","header"]):node.decompose()
    # Drupal themes may render status and application dates outside <main>/<article>.
    # Read the complete body, after removing navigational noise.
    main=soup.body or soup
    txt=" ".join(main.stripped_strings)[:50000]
    # Avoid matching 'Scadenza' in an unrelated phrase by requiring the date nearby.
    deadline=_date(DEADLINE.search(txt))
    opening=_date(OPENING.search(txt))
    windows=_festival_windows(txt) if "festival-partecipativi-2027" in url and "compagniadisanpaolo.it" in url else []
    if windows:deadline=next((x for x in windows if x>=date.today().isoformat()),windows[-1])
    if not deadline:deadline=_english_date(EN_DEADLINE.search(txt))
    if not opening:opening=_english_date(EN_OPENING.search(txt))
    official_cme_announcement=(
        url.startswith("https://culture.ec.europa.eu/culture-moves-europe/whats-new/news/")
        and "new-call-for-" in url and url.rstrip("/").endswith("-2026-2027-open")
    )
    official_news_closing=EN_VERIFIED_CALL_OPEN_UNTIL.search(txt) if official_cme_announcement else None
    if official_news_closing and not deadline:
        deadline=_english_date(official_news_closing)

    if ("infobandi.csvnet.it" in url or "volontariatotorino.it" in url) and not deadline:
        deadline=_csvnet_deadline(txt)
    if "spettacolo.cultura.gov.it" in url and not deadline:
        match=MIC_FORM_WINDOW.search(txt)
        if match and re.search(r"(?i)(modulistica|piattaforma).{0,220}(domande|candidature)",txt[match.start():match.end()+350]):
            opening=_italian_date(match,1)
            deadline=_italian_date(match,4)
            mic_open_evidence=bool(opening and deadline)  # current validity checked by effective_status
        else:
            mic_open_evidence=False
    else:
        mic_open_evidence=False

    if "interreg-alcotra.eu" in url and "bando-la-selezione-dei-progetti-singoli-dei-piani-territoriali-integrati-piter-2021-2027" in url:
        piter_dates=_piter_windows(txt)
        if piter_dates:
            windows=piter_dates
            deadline=next((d for d in piter_dates if d>=date.today().isoformat()),piter_dates[-1])
    if "interreg-alcotra.eu" in url:
        if not deadline:deadline=_date(ALCOTRA_CLOSING.search(txt))
        if not opening:opening=_date(ALCOTRA_OPENING.search(txt))
        closed_alcotra=ALCOTRA_EXPLICIT_CLOSED.search(txt)
        if not deadline and closed_alcotra:
            deadline=_italian_date(closed_alcotra,1)
    else:
        closed_alcotra=None
    if "bandi.comune.torino.it" in url and not deadline:
        # Date range explicitly associated with filing requests, not generic project periods.
        match=TORINO_APPLICATION_END.search(txt)
        if match and re.search(r"(?i)(presentare\s+la\s+richiesta|presentare\s+(?:le\s+)?domande|presentazione\s+(?:di\s+)?progetti)",txt[max(0,match.start()-70):match.end()+100]):
            deadline=_italian_date(match,4)
            if not opening:opening=_italian_date(match,1)
        if not deadline:
            period=TORINO_PUBLISHED_APPLICATION_PERIOD.search(txt)
            if period:
                candidate_start=_italian_date(period,1)
                candidate_end=_italian_date(period,4)
                if candidate_start and candidate_end and candidate_start<=candidate_end:
                    deadline=candidate_end
                    if not opening:opening=candidate_start
        if not deadline:deadline=_italian_date(TORINO_TEXTUAL_DEADLINE.search(txt))
        if not deadline:deadline=_italian_date(TORINO_PROPOSAL_CLOSING.search(txt))
        if not deadline:deadline=_date(TORINO_NUMERIC_END.search(txt))
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
    source_open=bool((state and state.group(1).lower() in ("in corso","aperto","aperta","attivo","attiva","open")) or window or mic_open_evidence or (official_news_closing and deadline))
    source_closed=bool((state and state.group(1).lower() in ("chiuso","chiusa","scaduto","scaduta","closed")) or closed_alcotra)
    beneficiaries=BENEFICIARIES.search(txt)
    return {
      "deadline":deadline,"opening_date":opening,"application_windows":windows,"summary":summary,"source_open_confirmed":source_open,
      "closure_confirmed":source_closed,
      "opening_evidence":url if opening else None,
      "deadline_source":url if deadline else None,
      "status_evidence":url if (state or closed_alcotra or mic_open_evidence or official_news_closing) else None,
      "beneficiaries_excerpt":beneficiaries.group(0).strip()[:270] if beneficiaries else None
    }
