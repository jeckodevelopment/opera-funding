"""Single presentation-grade adequacy decision for Opera+.

This is not a percentage, legal-eligibility certification, or forecast of award.
The editorial documentary review is primary; missing applicant/activity evidence
and explicit constraints limit the grade rather than creating false certainty.
"""
import re

RANK={"BASSA AFFINITÀ":1,"MEDIA AFFINITÀ":2,"ALTA AFFINITÀ":3}
NAMES={1:"BASSA",2:"MEDIA",3:"ALTA"}
INDIVIDUAL_ONLY=re.compile(
    r"(?i)(?:solo|esclusivamente|only)\\s+(?:persone fisiche|singoli artisti|individual artists|individual applicants)"
)
FIRMS_ONLY=re.compile(
    r"(?i)(?:solo|esclusivamente|only)\\s+(?:imprese|società commerciali|companies|businesses|for-profit)"
)
PARTNERS_ALLOWED=re.compile(
    r"(?i)partner ammessi|partenariato ammesso|scuole e associazioni|associazioni.*partner|"
    r"partner organisations|non.?profit.*partners|eligible partners"
)
PARTNERS_REQUIRED=re.compile(
    r"(?i)partenariato obbligatorio|partner obbligatori|mandatory partners|"
    r"consortium required|consorzio obbligatorio"
)

def apply_adequacy(row):
    kind=row.get("opportunity_type") or ""
    editorial=row.get("assessment_label") or ""
    if kind=="altro avviso" or editorial=="INFORMATIVA":
        row.update(adequacy_label="INFORMATIVA",adequacy_level=0,
                   adequacy_reason="Contenuto informativo, non una candidatura diretta.",
                   adequacy_basis="Tipologia del record")
        return row

    level=RANK.get(editorial,1)
    reasons=[]
    evidence=any(row.get(f) for f in (
        "programme_objectives_excerpt","funded_activities_excerpt",
        "beneficiaries_excerpt","requirements_excerpt"))
    manual=bool(row.get("assessment_reviewed_at"))
    source=bool(row.get("assessment_source") or row.get("assessment_evidence_source"))
    if not evidence or not source:
        if level>2:
            level=2
        reasons.append("La documentazione non è sufficiente a confermare un'adeguatezza alta")
    if not row.get("funded_activities_excerpt") or not row.get("beneficiaries_excerpt"):
        level=min(level,2)
        reasons.append("Attività finanziabili o beneficiari non documentati in modo completo")

    beneficiaries=str(row.get("beneficiaries_excerpt") or "")
    requirements=str(row.get("requirements_excerpt") or "")
    terms=beneficiaries+" "+requirements
    if INDIVIDUAL_ONLY.search(terms) or FIRMS_ONLY.search(terms):
        level=min(level,1)
        reasons.append("Il testo disponibile limita i destinatari a soggetti diversi da un'associazione culturale")
    elif PARTNERS_REQUIRED.search(terms):
        reasons.append("È necessario verificare il partenariato richiesto")
    elif ("scuol" in beneficiaries.lower() or "school" in beneficiaries.lower()) and not PARTNERS_ALLOWED.search(terms):
        reasons.append("Verificare se Opera+ può partecipare come partner di un ente scolastico")

    row["adequacy_label"]=NAMES[level]
    row["adequacy_level"]=level
    row["adequacy_reason"]="; ".join(reasons) if reasons else (
        row.get("assessment_reason") or
        "Coerenza progettuale da confrontare con attività ammissibili e requisiti")
    row["adequacy_basis"]=(
        "Revisione documentale individuale" if manual else
        "Evidenze di fonte" if evidence and source else
        "Valutazione preliminare con evidenze limitate"
    )
    return row
