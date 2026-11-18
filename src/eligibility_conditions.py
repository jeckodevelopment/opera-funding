"""Conservative applicant-condition signals independent of funding status and adequacy.

Signals describe explicit source wording, never legal eligibility certification.
Do not infer applicant requirements from titles, themes or generic descriptions.
"""
import re
from adequacy import restricted_applicants, PARTNERS_REQUIRED, PARTNERS_ALLOWED

DIRECT_ASSOCIATION = re.compile(
    r"(?i)\\b(?:associazioni?\\s+culturali?|associazioni?\\s+senza\\s+scopo\\s+di\\s+lucro|"
    r"enti\\s+del\\s+terzo\\s+settore|organizzazioni?\\s+non[ -]?profit|"
    r"non[ -]?profit\\s+organisations?|cultural\\s+associations?)\\b"
)
ELIGIBILITY_CONTEXT = re.compile(
    r"(?i)\\b(?:beneficiari|destinatari|soggetti\\s+ammissibili|eligible\\s+applicants|"
    r"who\\s+can\\s+apply|possono\\s+(?:partecipare|candidarsi|presentare\\s+domanda)|"
    r"applicants?\\s+(?:must|may)|sono\\s+ammess[ie])\\b"
)
CONDITIONAL_REQUIREMENTS = re.compile(
    r"(?i)\\b(?:partenariato\\s+obbligatorio|partner\\s+obbligatori|mandatory\\s+partners?|"
    r"consortium\\s+required|consorzio\\s+obbligatorio|"
    r"cofinanziamento\\s+(?:obbligatorio|richiesto)|"
    r"mandatory\\s+co[ -]?financing)\\b"
)
NEGATION = re.compile(r"(?i)\\b(?:non|not|senza|without)\\s+$")


def condition_signals(row):
    """Four mutually exclusive review signals, not four legal verdicts."""
    if row.get("opportunity_type") == "altro avviso":
        return {"status":"non_applicabile","reason":"Contenuto informativo, non candidatura",
                "sources":[]}
    beneficiaries = str(row.get("beneficiaries_excerpt") or "").strip()
    requirements = str(row.get("requirements_excerpt") or "").strip()
    field_sources = row.get("assessment_field_sources") or {}
    if not isinstance(field_sources,dict):
        field_sources={}
    def source(field):
        return field_sources.get(field) or row.get("assessment_source") or row.get("assessment_evidence_source") or row.get("beneficiaries_source")
    candidates=[source("beneficiaries_excerpt"),source("requirements_excerpt")]
    sources=list(dict.fromkeys(x for x in candidates if isinstance(x,str) and x.startswith("https://")))
    if not beneficiaries and not requirements:
        return {"status":"informazioni_insufficienti","reason":"Destinatari e requisiti non documentati",
                "sources":[]}
    if not sources:
        return {"status":"informazioni_insufficienti","reason":"Manca una fonte documentale attribuibile ai requisiti",
                "sources":[]}
    # Strong exclusive wording is a reviewable restriction, including where a
    # partner role might still permit participation. Never certify exclusion.
    if restricted_applicants(beneficiaries) or (ELIGIBILITY_CONTEXT.search(requirements)
                                                   and restricted_applicants(requirements)):
        return {"status":"potenzialmente_incompatibile",
                "reason":"Fonte indica destinatari esclusivi diversi da associazioni culturali; verificare ruolo di partner",
                "sources":sources}
    mandatory=bool(CONDITIONAL_REQUIREMENTS.search(requirements))
    if mandatory:
        return {"status":"condizionata",
                "reason":"La fonte indica partenariato o cofinanziamento obbligatorio; condizioni concrete da verificare",
                "sources":sources}
    if beneficiaries and DIRECT_ASSOCIATION.search(beneficiaries) and (
        ELIGIBILITY_CONTEXT.search(beneficiaries) or row.get("assessment_reviewed_at")
    ):
        return {"status":"compatibilita_documentata",
                "reason":"I beneficiari citano associazioni/enti non profit; gli altri requisiti restano da verificare",
                "sources":sources}
    return {"status":"informazioni_insufficienti",
            "reason":"I documenti non consentono di determinare con certezza la categoria di partecipazione",
            "sources":sources}


def annotate_conditions(row):
    result=condition_signals(row)
    row["eligibility_condition_status"]=result["status"]
    row["eligibility_condition_reason"]=result["reason"]
    row["eligibility_condition_sources"]=result["sources"]
    return row
