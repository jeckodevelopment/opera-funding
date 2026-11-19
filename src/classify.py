"""Explainable preliminary classification from source index text, not grant eligibility."""
import re
from datetime import date, datetime

THEMES = [
    (r"cultur|cultural|musica|music|opera|liric|spettacol|artist|festival|theatr", 35, "cultura e spettacolo"),
    (r"formazion|education|educazion|learning|student|scuol|giovan|youth", 25, "formazione e giovani"),
    (r"digit|innova|video|audiovis|media|podcast", 20, "innovazione e contenuti digitali"),
    (r"accessibil|inclusio|partecip|comunit|pubblic|audience", 20, "accessibilità e partecipazione"),
]
# Category is distinct from relevance: people/job calls can be culturally relevant, yet not fund projects.
NON_GRANT = re.compile(
    r"selezion[ei] (?:di |per |pubblica |n[.]? ?\d|n[.]? ?[0-9])|"
    r"graduatori[ea]|conferimento di incarich|ricerca (?:di |per )personale|"
    r"assunzion|posizion[ei] lavorativ|personale amministrativ|"
    r"avviso (?:di |pubblico per la )?selezione|"
    r"avviso di gara|assegnazione in affitto|locazione di fondi rustici|"
    r"indagine di mercato|affidamento (?:di |del |dei |della )|"
    r"fornitura di |acquisizione (?:di |della )|"
    r"concorso pubblico|procedura (?:di |aperta |negoziata )|"
    r"avviso di sponsorizzazion|ricerca per il reperimento di sponsorizzazion",
    re.I,
)
FINANCING = re.compile(
    r"contribut|finanziament|sovvenzion|grant|funding|"
    r"bando (?:per |a sostegno|a supporto)|sostegn[oi] (?:a |per |di )|"
    r"erogazion|voucher|donazion|beneficiari|cofinanziament",
    re.I,
)
PROJECT_CALL = re.compile(
    r"manifestazione di interesse|call for|progett[oi]|festival|"
    r"partnership|partenariat|cooperazion|avviso pubblico",
    re.I,
)
DATE_RE = re.compile(r"(?i)scadenza\s*[:–-]?\s*(\d{1,2})[./-](\d{1,2})[./-](20\d{2})(?:\s+([0-2]?\d)[:.]([0-5]\d))?")
STATUS_RE = re.compile(r"(?i)\b(attivo|aperto|aperta|chiuso|chiusa|scaduto|scaduta)\b")
PUB_RE = re.compile(r"(?i)pubblicat[oa] il")

def parse_deadline(snippet):
    """Only explicit labeled deadlines; never treat publication date as deadline."""
    match = DATE_RE.search(snippet)
    if not match:
        return None
    day, month, year = map(int, match.group(1, 2, 3))
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None

def parse_status(snippet):
    # Only explicit status next to a publication or deadline marker.
    match = STATUS_RE.search(snippet)
    if not match:
        return "non verificato"
    suffix = snippet[match.end():]
    if not (PUB_RE.search(suffix[:45]) or re.search(r"(?i)scadenza", suffix[:45])):
        return "non verificato"
    return "chiuso" if match.group(1).lower() in {"chiuso","chiusa","scaduto","scaduta"} else "aperto"

def clean_title(raw):
    raw = " ".join(raw.split())
    # Remove status and metadata usually appended to anchor text in source listings.
    raw = re.split(r"(?i)\s+(?:Chiuso|Chiusa|Attivo|Aperto|Aperta)\s+Pubblicat[oa] il\b",raw,maxsplit=1)[0]
    raw = re.split(r"(?i)\s+Pubblicat[oa] il\s+\d{1,2}[./-]\d{1,2}[./-]20\d{2}",raw,maxsplit=1)[0]
    return raw[:220].strip(" –-")

def classify(title, snippet=""):
    """Preliminary topical match and funding type from short page-index text."""
    title = clean_title(title)
    theme_names = [label for regex, _, label in THEMES if re.search(regex, title, re.I)]
    relevance = min(100, 20 + sum(weight for regex, weight, _ in THEMES if re.search(regex,title,re.I)))
    if NON_GRANT.search(title):
        kind = "altro avviso"
        explanation = "Selezione, incarico, appalto o sponsorizzazione: non è evidenziato un finanziamento a progetti"
    elif FINANCING.search(title):
        kind = "finanziamento potenziale"
        explanation = "Il titolo contiene indicatori di contributo o finanziamento; verifica necessaria"
    elif PROJECT_CALL.search(title):
        kind = "call progettuale da verificare"
        explanation = "Possibile iniziativa progettuale; condizioni economiche da verificare"
    else:
        kind = "non classificato"
        explanation = "Informazioni insufficienti per determinare la tipologia"
    deadline = parse_deadline(snippet)
    explicit = parse_status(snippet)
    if deadline and deadline < date.today().isoformat():
        status = "chiuso"
        status_basis = "scadenza esplicita trascorsa nell'indice"
    elif explicit == "chiuso":
        status = "chiuso"
        status_basis = "stato esplicito nella fonte indice"
    elif explicit == "aperto" and (deadline is None or deadline >= date.today().isoformat()):
        status = "aperto (fonte indice)"
        status_basis = "stato esplicito nella fonte indice; da ricontrollare"
    else:
        status = "non verificato"
        status_basis = "stato non confermato"
    return {
        "title": title, "relevance": relevance, "themes": theme_names,
        "relevance_basis": "corrispondenza tematica preliminare sul titolo",
        "opportunity_type": kind, "type_reason": explanation,
        "deadline": deadline, "status": status, "status_basis": status_basis,
    }
