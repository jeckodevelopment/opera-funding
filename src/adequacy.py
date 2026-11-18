"""Single presentation-grade adequacy decision for Opera+.

This is not a percentage, legal-eligibility certification, or forecast of award.
The editorial documentary review is primary; missing applicant/activity evidence
and explicit constraints limit the grade rather than creating false certainty.
"""
import re

RANK={"BASSA AFFINITÀ":1,"MEDIA AFFINITÀ":2,"ALTA AFFINITÀ":3}
NAMES={1:"BASSA",2:"MEDIA",3:"ALTA"}
INDIVIDUAL_ONLY=re.compile(
    r"(?i)(?:solo|esclusivamente|only)\s+(?:persone fisiche|singoli artisti|individual artists|individual applicants)"
)
FIRMS_ONLY=re.compile(
    r"(?i)(?:solo|esclusivamente|only)\s+(?:imprese|società commerciali|companies|businesses|for-profit)"
)
PARTNERS_ALLOWED=re.compile(
    r"(?i)partner ammessi|partenariato ammesso|scuole e associazioni|associazioni.*partner|"
    r"partner organisations|non.?profit.*partners|eligible partners"
)
PARTNERS_REQUIRED=re.compile(
    r"(?i)partenariato obbligatorio|partner obbligatori|mandatory partners|"
    r"consortium required|consorzio obbligatorio"
)

def restricted_applicants(terms):
    """Only explicit exclusive applicant rules, not 'not only X' statements."""
    for pattern in (INDIVIDUAL_ONLY, FIRMS_ONLY):
        for match in pattern.finditer(terms):
            prefix=terms[max(0,match.start()-12):match.start()].lower()
            if re.search(r"(?:non|not)\s+$",prefix):
                continue
            return True
    return False


def unresolved_eligibility_documents(row):
    """Different excerpts are a review signal, not proven legal conflicts."""
    relevant={"beneficiaries_excerpt","requirements_excerpt"}
    return [
        entry for entry in (row.get("assessment_document_discrepancies") or [])
        if isinstance(entry,dict) and entry.get("field") in relevant
        and entry.get("first_source") and entry.get("other_source")
        and entry["first_source"]!=entry["other_source"]
    ]


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
    row["adequacy_verification_flags"]=[]
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
    if restricted_applicants(terms):
        level=min(level,1)
        row["adequacy_verification_flags"].append("beneficiari_esclusivi")
        reasons.append("Il testo disponibile sembra limitare i destinatari a soggetti diversi da un'associazione culturale: verificare eventuale ammissione come partner")
    elif PARTNERS_REQUIRED.search(terms):
        reasons.append("È necessario verificare il partenariato richiesto")
    elif ("scuol" in beneficiaries.lower() or "school" in beneficiaries.lower()) and not PARTNERS_ALLOWED.search(terms):
        reasons.append("Verificare se Opera+ può partecipare come partner di un ente scolastico")

    territorial_risk=any(
        x.get("category")=="territorio" and x.get("status")=="potenzialmente_incompatibile"
        for x in (row.get("applicant_requirement_comparison") or []) if isinstance(x,dict)
    )
    if territorial_risk:
        level=min(level,1)
        row["adequacy_verification_flags"].append("sede_territoriale_potenzialmente_esclusa")
        reasons.append("Requisito territoriale apparentemente incompatibile con la sede dichiarata; non considerare la candidatura diretta ammissibile senza prova di eccezioni")
    discrepancies=unresolved_eligibility_documents(row)
    if discrepancies:
        # A higher assessment must not depend on applicant rules that differ
        # between two inspected official documents. These passages might be
        # complementary rather than legally conflicting, so cap at MEDIUM.
        level=min(level,2)
        row["adequacy_verification_flags"].append("fonti_requisiti_da_confrontare")
        reasons.append("I documenti riportano formulazioni differenti su beneficiari o requisiti: confronto delle fonti necessario")
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
