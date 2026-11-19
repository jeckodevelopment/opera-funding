"""Actionable, comparable catalog metrics for editorial reconciliation.

The audit counts missing evidence without pretending that legal eligibility
has been verified. It never changes editorial assessment or deadline status.
"""
from collections import Counter
from open_review_queue import review_tasks

FIELD_LABELS=(
    ("programme_objectives_excerpt","finalita"),
    ("funded_activities_excerpt","attivita_finanziabili"),
    ("beneficiaries_excerpt","beneficiari"),
    ("requirements_excerpt","requisiti"),
)


def summarize_catalog_reconciliation(rows):
    all_rows=list(rows)
    open_rows=[r for r in all_rows if r.get("funding_status")=="APERTO"]
    candidates=[r for r in open_rows if r.get("adequacy_label") in ("ALTA","MEDIA")]
    coverage={}
    for label,records in (("catalogo",all_rows),("aperte",open_rows),
                          ("aperte_alta_media",candidates)):
        missing={name:sum(not isinstance(r.get(field),str) or not r[field].strip()
                          for r in records) for field,name in FIELD_LABELS}
        coverage[label]={
            "total":len(records),
            "adequacy_counts":dict(sorted(Counter(
                str(r.get("adequacy_label") or "NON VALUTATA") for r in records).items())),
            "missing_documentation":missing,
            "with_document_issues":sum(bool(r.get("assessment_document_issues")) for r in records),
            "with_unresolved_applicant_checks":sum(any(
                isinstance(c,dict) and c.get("status") in ("da_verificare","potenzialmente_incompatibile")
                for c in (r.get("applicant_requirement_comparison") or [])) for r in records),
            "source_not_attributed":sum(not (r.get("assessment_source") or
                                             r.get("assessment_evidence_source")) for r in records),
        }
    return {
        "coverage":coverage,
        "priority_open_ids":[r.get("public_id") for r in candidates
                             if isinstance(r.get("public_id"),int) and r["public_id"]>0],
        "notes":"I conteggi indicano copertura delle evidenze, non ammissibilità certificata.",
    }


VALID_ADEQUACY = {"ALTA", "MEDIA", "BASSA", "INFORMATIVA"}
FALLBACK_REASON = (
    "Valutazione prudenziale BASSA: al censimento mancano elementi sufficienti "
    "per motivare un giudizio più favorevole; l'opportunità resta in catalogo "
    "e i requisiti di candidatura devono essere verificati."
)

def reconcile_catalog_assessments(rows):
    """Assign a reasoned conservative rating without dropping or blocking records.

    A fallback indicates limited evidence, never a finding of ineligibility.
    Preserve valid assessed rows unchanged and preserve informational notices.
    """
    fallbacks=0
    for row in rows:
        valid=(row.get("adequacy_label") in VALID_ADEQUACY
               and str(row.get("adequacy_reason") or "").strip()
               and str(row.get("assessment_reason") or "").strip())
        if valid:
            continue
        informational=(row.get("opportunity_type")=="altro avviso"
                       or row.get("adequacy_label")=="INFORMATIVA")
        if informational:
            row["adequacy_label"]="INFORMATIVA"
            row["adequacy_level"]=0
            row["adequacy_reason"]=row.get("adequacy_reason") or (
                "Contenuto informativo, non una candidatura diretta.")
            row["assessment_reason"]=row.get("assessment_reason") or (
                "Avviso informativo conservato nel catalogo.")
        else:
            row["adequacy_label"]="BASSA"
            row["adequacy_level"]=1
            row["adequacy_reason"]=FALLBACK_REASON
            row["assessment_reason"]=FALLBACK_REASON
            row["assessment_label"]="BASSA AFFINITÀ"
            row["adequacy_basis"]="Valutazione prudenziale al censimento"
        row["assessment_fallback"]=True
        fallbacks+=1
    return fallbacks

def validate_catalog_assessments(rows):
    """Backward-compatible non-blocking reconciliation entry point."""
    reconcile_catalog_assessments(rows)
    return len(rows)

# Documented evidence accounting never infers eligibility or deletes records.
REQUIREMENT_STATUSES=("compatibile","potenzialmente_incompatibile","da_verificare")
REQUIREMENT_COVERAGE=("confronti_documentati","ostacolo_documentato",
                      "senza_requisiti_confrontabili","avviso_informativo")

def annotate_requirement_coverage(row):
    checks=[c for c in (row.get("applicant_requirement_comparison") or [])
            if isinstance(c,dict) and c.get("status") in REQUIREMENT_STATUSES
            and str(c.get("requirement") or "").strip()
            and str(c.get("source") or "").startswith("https://")]
    blocker=bool(str(row.get("direct_application_blocker") or "").strip())
    if row.get("opportunity_type")=="altro avviso":
        status="avviso_informativo"
    elif checks:
        status="confronti_documentati"
    elif blocker:
        status="ostacolo_documentato"
    else:
        status="senza_requisiti_confrontabili"
    row["requirement_coverage_status"]=status
    row["requirement_evidence_count"]=len(checks)
    return row

def summarize_requirement_coverage(rows):
    """Measure full-catalog documentable requirements and actionable open gaps."""
    records=list(rows)
    groups=(
        ("catalogo",records),
        ("aperte",[r for r in records if r.get("funding_status")=="APERTO"]),
        ("aperte_alta_media",[r for r in records if r.get("funding_status")=="APERTO"
                             and r.get("adequacy_label") in ("ALTA","MEDIA")]),
    )
    coverage={}
    for name,subset in groups:
        counts=Counter(r.get("requirement_coverage_status") for r in subset)
        comparisons=[c for r in subset for c in
                     (r.get("applicant_requirement_comparison") or []) if isinstance(c,dict)]
        coverage[name]={
            "total":len(subset),
            "coverage_status_counts":{s:counts[s] for s in REQUIREMENT_COVERAGE},
            "requirements_compared":len(comparisons),
            "comparison_status_counts":{s:sum(c.get("status")==s for c in comparisons)
                                        for s in REQUIREMENT_STATUSES},
            "with_explicit_direct_blocker":sum(bool(str(
                r.get("direct_application_blocker") or "").strip()) for r in subset),
        }
    missing=[r for r in groups[1][1]
             if r.get("requirement_coverage_status")=="senza_requisiti_confrontabili"]
    missing.sort(key=lambda r:(
        0 if r.get("adequacy_label") in ("ALTA","MEDIA") else 1,
        str(r.get("deadline") or "9999-12-31"),int(r.get("public_id") or 0)))
    return {
        "coverage":coverage,
        "open_without_comparable_requirements":[
            {"public_id":r.get("public_id"),"adequacy":r.get("adequacy_label"),
             "has_requirements_excerpt":bool(str(r.get("requirements_excerpt") or "").strip()),
             "has_beneficiaries_excerpt":bool(str(r.get("beneficiaries_excerpt") or "").strip()),
             "has_attributed_assessment_source":bool(
                 r.get("assessment_source") or r.get("assessment_evidence_source"))}
            for r in missing],
        "notes":("Nessun requisito rilevato non equivale a requisito assente o soddisfatto. "
                 "La copertura non certifica ammissibilità e non esclude opportunità."),
    }
