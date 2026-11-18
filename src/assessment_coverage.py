"""Evidence completeness metadata for every funding opportunity.

A thematic fit is assigned to every record, but completeness is never inferred
from a score, a headline, or the mere presence of an accessible HTML page.
"""
from urllib.parse import urlparse

REQUIRED = (
    ("programme_objectives_excerpt", "Finalità del programma"),
    ("funded_activities_excerpt", "Attività finanziabili"),
    ("beneficiaries_excerpt", "Beneficiari ammessi"),
    ("requirements_excerpt", "Vincoli e requisiti"),
)

def annotate_assessment_coverage(row):
    present = [label for field, label in REQUIRED
               if isinstance(row.get(field), str) and row[field].strip()]
    missing = [label for field, label in REQUIRED if label not in present]
    checked = bool(row.get("detail_attempted_at") or row.get("detail_checked_at") or
                   row.get("assessment_reviewed_at"))
    # Manually reviewed source snapshots are not a substitute for reading every
    # attachment and confirming the applicant's formal legal eligibility.
    manual = bool(row.get("assessment_reviewed_at"))
    has_source = bool(row.get("assessment_evidence_source") or
                      (row.get("detail_checked") and row.get("url")))
    if manual:
        stage = "REVISIONE DOCUMENTALE"
    elif len(present) == len(REQUIRED) and has_source:
        stage = "EVIDENZE RACCOLTE"
    elif present and has_source:
        stage = "PARZIALE"
    elif checked:
        stage = "FONTE NON SUFFICIENTE"
    else:
        stage = "NON ESAMINATA"
    row["assessment_review_status"] = stage
    row["assessment_evidence_count"] = len(present)
    row["assessment_missing_fields"] = missing
    row["assessment_checked_at"] = (
        row.get("assessment_reviewed_at") or
        row.get("detail_attempted_at") or row.get("detail_checked_at")
    )
    row["assessment_method"] = (
        "revisione individuale della fonte" if manual else
        "estrazione automatica di evidenze" if has_source and present else
        "valutazione preliminare con evidenze insufficienti"
    )
    return row

def assessment_coverage(rows):
    status = {}
    for row in rows:
        stage=row.get("assessment_review_status") or "NON ESAMINATA"
        status[stage]=status.get(stage,0)+1
    return {
        "total":len(rows),
        "with_editorial_label":sum(bool(r.get("assessment_label")) for r in rows),
        "by_review_status":status,
        "completely_verified_applicability":0,  # legal eligibility never certified
        "open_without_individual_review":sum(
            r.get("funding_status")=="APERTO"
            and r.get("assessment_review_status")!="REVISIONE DOCUMENTALE"
            for r in rows),
        "new_pending":sum(
            r.get("assessment_review_status")=="NON ESAMINATA" for r in rows),
    }
