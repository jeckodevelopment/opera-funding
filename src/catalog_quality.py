"""Reproducible, conservative catalog data-quality cases.

Expose actual provenance and distinguish rolling applications from missing data.
No deadline is inferred, no history is dropped, and neither evidence nor
applicant eligibility is certified by this report.
"""
from collections import Counter
from urllib.parse import unquote, urlparse

CANDIDATE_TYPES={"finanziamento potenziale","call progettuale da verificare","non classificato"}
STATE_PRIORITY={"APERTO":0,"IN ARRIVO":1,"DA VERIFICARE":2,"CHIUSO":3,"INFORMATIVO":4}


def _identifier(row):
    return row.get("public_id")


def _deadline_class(row):
    if row.get("rolling_confirmed") is True and bool(row.get("rolling_evidence")):
        return "sportello_verificato"
    if row.get("funding_status")=="IN ARRIVO" and row.get("opening_evidence"):
        return "apertura_futura"
    return "scadenza_da_documentare"


def diagnostic_review_class(issue):
    """Suggest a review path without claiming the document is irrelevant."""
    reason=str(issue.get("reason") or "")
    path=unquote(urlparse(str(issue.get("source") or "")).path).casefold()
    # Award outcomes, rankings and application templates frequently lack the
    # sections searched for in a grant's operative call. This is not a clean bill.
    ancillary=any(token in path for token in (
        "graduatoria","esiti","selezionat","modulo","domanda-di-candidatura",
        "tutorial","determina","delibera"))
    if reason=="testi_diversi_da_verificare":
        return "confrontare_documenti_e_priorita"
    if reason=="testo_non_estratto":
        return "verifica_pdf_senza_testo"
    if reason=="nessuna_evidenza_estratta" and ancillary:
        return "verifica_allegato_potenzialmente_accessorio"
    if reason=="nessuna_evidenza_estratta":
        return "rivedere_sezioni_del_documento"
    return "verifica_tecnica_documento"


def catalog_quality(rows):
    """Return complete, stable queues, with no claims beyond source data."""
    document_cases=[]
    date_cases=[]
    reasons=Counter()
    review_classes=Counter()
    for row in rows:
        ident=_identifier(row)
        issues=[x for x in (row.get("assessment_document_issues") or [])
                if isinstance(x,dict)]
        if issues:
            for issue in issues:
                reasons[str(issue.get("reason") or "non_specificata")]+=1
                review_classes[diagnostic_review_class(issue)]+=1
            document_cases.append({
                "public_id":ident,
                "source_id":row.get("source_id"),
                "funding_status":row.get("funding_status"),
                "issues":[{"reason":str(x.get("reason") or "non_specificata"),
                           "source":x.get("source"),"field":x.get("field"),
                           "review_class":diagnostic_review_class(x)}
                          for x in issues],
            })
        if row.get("opportunity_type") in CANDIDATE_TYPES and not row.get("deadline"):
            date_cases.append({
                "public_id":ident,
                "source_id":row.get("source_id"),
                "funding_status":row.get("funding_status"),
                "classification":_deadline_class(row),
                "rolling_evidence":row.get("rolling_evidence")
                    if row.get("rolling_confirmed") is True else None,
                "opening_evidence":row.get("opening_evidence")
                    if row.get("funding_status")=="IN ARRIVO" else None,
                "url":row.get("url"),
            })
    document_cases.sort(key=lambda x:(STATE_PRIORITY.get(x["funding_status"],5),
                                      str(x["source_id"] or ""),
                                      str(x["public_id"])))
    date_cases.sort(key=lambda x:(STATE_PRIORITY.get(x["funding_status"],5),
                                  str(x["source_id"] or ""),
                                  str(x["public_id"])))
    return {
        "document_issues":{
            "total_records":len(document_cases),
            "total_diagnostics":sum(len(x["issues"]) for x in document_cases),
            "reasons":dict(sorted(reasons.items())),
            "review_classes":dict(sorted(review_classes.items())),
            "by_state":dict(sorted(Counter(x["funding_status"] for x in document_cases).items())),
            "cases":document_cases,
        },
        "missing_deadline":{
            "total":len(date_cases),
            "by_classification":dict(sorted(Counter(x["classification"] for x in date_cases).items())),
            "cases":date_cases,
        },
        "note":"Anomalie reali e lacune documentali: il report non inventa scadenze o requisiti e non certifica ammissibilità.",
    }
