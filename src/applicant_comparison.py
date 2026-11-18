"""Compare source-backed grant constraints with an evidence-controlled applicant profile.

A declaration is not verification. Unknown or ambiguous conditions remain open.
The output is advisory and must never silently certify legal eligibility.
"""
import json
import re
from datetime import date
from pathlib import Path

DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "config/applicant_profile.json"
CATEGORIES = ("territorio", "natura_giuridica", "anzianita",
              "condizioni_economiche", "partenariato")
REGIONS = (
    "piemonte", "lombardia", "liguria", "valle d'aosta", "veneto",
    "emilia-romagna", "toscana", "lazio", "puglia", "campania", "sicilia",
    "sardegna", "umbria", "marche", "abruzzo", "molise", "basilicata",
    "calabria", "friuli-venezia giulia", "trentino-alto adige"
)
AGE_PATTERN = re.compile(r"(?i)\b(?:almeno|minimo|non meno di)\s+(\d{1,2})\s+ann[io]\s+di\s+(?:attivit[àa]|costituzione)|\bcostituit[ioe]\s+da\s+almeno\s+(\d{1,2})\s+ann[io]")
RUNTS_PATTERN = re.compile(r"(?i)\b(?:iscritt[ioe]|registrat[ioe])\s+(?:al|nel|alla|all')\s*runts\b")
REGION_PATTERN = re.compile(r"(?i)\bsede\s+(?:legale|operativa)\s+(?:in|nel|nella)\s+(?:regione\s+)?([a-zàèéìòù' -]+)")
MAX_SUMMARY_LENGTH = 240


def load_applicant_profile(path=DEFAULT_PROFILE):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    fields = raw.get("profile_fields")
    if not isinstance(fields, dict):
        raise ValueError("Profilo richiedente privo di campi")
    for name, record in fields.items():
        if (not isinstance(record, dict) or
            record.get("verification") not in ("non_verificato", "dichiarato", "documentato") or
            (record["verification"] == "documentato" and
             (record.get("value") is None or not record.get("source")))):
            raise ValueError("Campo profilo non valido: " + name)
    return raw


def _profile_value(profile, key):
    value = profile.get("profile_fields", {}).get(key) or {}
    if value.get("verification") != "documentato" or value.get("value") is None:
        return None
    return value["value"]


def _safe_compare(condition, profile, as_of):
    category = condition.get("category")
    excerpt = str(condition.get("excerpt") or "")
    if category == "natura_giuridica" and RUNTS_PATTERN.search(excerpt):
        registered = _profile_value(profile, "runts_registration")
        if isinstance(registered, bool):
            return ("compatibile" if registered else "potenzialmente_incompatibile",
                    "Iscrizione RUNTS confrontata con dato documentato del richiedente")
    if category == "anzianita":
        age = AGE_PATTERN.search(excerpt)
        established = _profile_value(profile, "constitution_date")
        if age and isinstance(established, str):
            try:
                born = date.fromisoformat(established)
                years = int(next(x for x in age.groups() if x))
                if years <= 0 or born > as_of:
                    return None
                reached = (as_of.year-born.year -
                           ((as_of.month, as_of.day) < (born.month, born.day)))
                return ("compatibile" if reached >= years else "potenzialmente_incompatibile",
                        "Anzianità confrontata con la data costitutiva documentata alla data del controllo")
            except (ValueError, StopIteration):
                pass
    # A region mention can be ambiguous (legal or operational seat, multiple
    # regions, partner location). Do not derive a legal conclusion from it.
    return None


def compare_applicant_requirements(row, profile, as_of=None):
    as_of = as_of or date.today()
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)
    results = []
    for item in row.get("eligibility_specific_requirements") or []:
        if not isinstance(item, dict) or item.get("category") not in CATEGORIES:
            continue
        outcome = _safe_compare(item, profile, as_of)
        if outcome:
            status, reason = outcome
        else:
            status, reason = ("da_verificare",
                              "Confronto non conclusivo: requisito, profilo o documentazione insufficienti")
        results.append({
            "category": item["category"],
            "status": status,
            "reason": reason,
            "requirement": str(item.get("excerpt") or "")[:380],
            "source": item.get("source"),
        })
    return results


def annotate_applicant_comparison(row, profile, as_of=None):
    results = compare_applicant_requirements(row, profile, as_of)
    row["applicant_requirement_comparison"] = results
    row["applicant_comparison_counts"] = {
        status: sum(x["status"] == status for x in results)
        for status in ("compatibile", "potenzialmente_incompatibile", "da_verificare")
    }
    # This is not applicant eligibility, nor a reason to hide the opportunity.
    return row
