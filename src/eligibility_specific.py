"""Evidence-backed eligibility constraints, without assertions about applicant facts.

Only extract explicit requirement statements from the inspected official source
excerpts. A detected condition is not an applicant eligibility verdict.
"""
import re
from urllib.parse import urlparse

# Avoid interpreting the mere mention of an Italian city or a financial value
# as a mandatory grant condition. The trigger must denote a requirement.
PATTERNS = (
    ("territorio", re.compile(
        r"(?i)\b(?:sede\s+(?:legale|operativa)\s+(?:in|nel|nella|sul|situata|ubicata)|"
        r"residen[zt][ae]\s+(?:in|nel|nella)|(?:operare|operanti|essere\s+attivi)\s+(?:in|nel|nella)|"
        r"(?:ubicat[ioe]|localizzat[ioe])\s+(?:in|nel|nella)\s+(?:regione|comune|provincia)|"
        r"registered\s+(?:office|address)\s+in|established\s+in)\b")),
    ("natura_giuridica", re.compile(
        r"(?i)\b(?:(?:iscritt[ioe]|registrat[ioe])\s+(?:al|nel|alla|all')\s*(?:runts|registro|albo)|"
        r"(?:obbligatoria|richiesta)\s+l['’]iscrizione|"
        r"must\s+be\s+(?:registered|incorporated)|"
        r"legal\s+(?:status|form)\s+(?:required|must))\b")),
    ("anzianita", re.compile(
        r"(?i)\b(?:costituit[ioe]\s+da\s+almeno\s+\d+\s+ann[io]|"
        r"(?:almeno|minimo|non\s+meno\s+di)\s+\d+\s+ann[io]\s+di\s+(?:attivit[àa]|costituzione)|"
        r"(?:minimum|at\s+least)\s+\d+\s+years?\s+(?:of\s+)?(?:operation|existence|registration))\b")),
    ("condizioni_economiche", re.compile(
        r"(?i)\b(?:cofinanziamento\s+(?:obbligatorio|richiesto|almeno|pari\s+al)|"
        r"(?:obbligo|quota\s+minima)\s+di\s+cofinanziamento|"
        r"(?:budget|fatturato|bilancio)\s+(?:minimo|di\s+almeno|non\s+inferiore)|"
        r"(?:mandatory|minimum)\s+(?:co[ -]?funding|co[ -]?financing|turnover))\b")),
    ("partenariato", re.compile(
        r"(?i)\b(?:partenariato\s+(?:obbligatorio|richiesto)|"
        r"(?:partner|partenariati)\s+obbligatori|"
        r"(?:almeno|minimo)\s+\d+\s+partner|"
        r"(?:mandatory|required)\s+(?:partners?|consortium)|"
        r"consorzio\s+obbligatorio|consortium\s+required)\b")),
)
FIELDS = ("requirements_excerpt", "beneficiaries_excerpt")
# Negated mandatory requirements must not become hard eligibility constraints.
NEGATED = re.compile(r"(?i)\b(?:non|not|senza|without)\s+$")
MAX_EXCERPT = 380


def _evidence_source(row, field):
    field_sources = row.get("assessment_field_sources")
    if isinstance(field_sources, dict):
        candidate = field_sources.get(field)
        if isinstance(candidate, str) and urlparse(candidate).scheme == "https":
            return candidate
    for fieldname in ("assessment_source", "assessment_evidence_source",
                      "beneficiaries_source"):
        candidate = row.get(fieldname)
        if isinstance(candidate, str) and urlparse(candidate).scheme == "https":
            return candidate
    return None


def extract_specific_requirements(row):
    """Return attributable, explicitly worded requirements; no positive verdicts."""
    if row.get("opportunity_type") == "altro avviso":
        return []
    found = []
    for field in FIELDS:
        raw = row.get(field)
        if not isinstance(raw, str) or not raw.strip():
            continue
        source = _evidence_source(row, field)
        if not source:
            continue
        # Sentences reduce cross-paragraph false matches and keep source quotes short.
        passages = re.split(r"(?<=[.;!?])\s+|\n+", raw)
        for passage in passages:
            passage = " ".join(passage.split())
            if not passage:
                continue
            for category, pattern in PATTERNS:
                match = pattern.search(passage)
                if not match:
                    continue
                previous = passage[max(0, match.start()-16):match.start()]
                if NEGATED.search(previous):
                    continue
                if any(x["category"] == category for x in found):
                    continue
                found.append({
                    "category": category,
                    "status": "requisito_documentato_da_verificare",
                    "excerpt": passage[:MAX_EXCERPT],
                    "source": source,
                    "field": field,
                })
    return found


def annotate_specific_requirements(row):
    requirements = extract_specific_requirements(row)
    row["eligibility_specific_requirements"] = requirements
    row["eligibility_specific_unchecked"] = len(requirements)
    # No proof about Opera+'s registration, age, location, turnover or partner.
    return row
