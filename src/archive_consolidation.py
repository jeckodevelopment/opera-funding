"""Bounded, explicit dispositions for the 39 archival PDF diagnostics.

A review based on procedural type and publisher metadata must never be
presented as verification of PDF contents. Preserve original diagnostic data;
an altered URL or new diagnostic invalidates the specific archival decision.
"""
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

NON_FUNDING="riferimento_non_finanziamento"
HISTORICAL="bando_storico_con_limiti_documentali"
VALID={NON_FUNDING,HISTORICAL}


def _signatures(row):
    return sorted("|".join(str(issue.get(k) or "") for k in ("reason","source","field"))
                  for issue in (row.get("assessment_document_issues") or [])
                  if isinstance(issue,dict))


def load_archive_reviews(path):
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("version")!=1 or not isinstance(payload.get("cases"),list):
        raise ValueError("Invalid archival review registry")
    reviews=payload["cases"]
    seen=set()
    for review in reviews:
        ident=review.get("public_id")
        if (type(ident) is not int or ident<1 or ident in seen
                or review.get("disposition") not in VALID
                or not isinstance(review.get("url"),str)
                or not review["url"].startswith("https://")
                or not isinstance(review.get("motive"),str)
                or len(review["motive"].strip())<25
                or not isinstance(review.get("observed_issue_signatures"),list)
                or not review["observed_issue_signatures"]):
            raise ValueError("Invalid or duplicate archival review entry")
        seen.add(ident)
    return reviews


def apply_archive_reviews(rows,reviews,review_date):
    """Attach an honest decision to matching historical records only.

    A previously closed call that reopens or gains new documents must undergo
    normal current screening, never rely on a stale archival disposition.
    """
    index={r["public_id"]:r for r in reviews}
    for row in rows:
        review=index.get(row.get("public_id"))
        if not review:
            continue
        valid_identity=(row.get("source_id")==review["source_id"] and
                        row.get("url","").rstrip("/")==review["url"].rstrip("/"))
        unchanged=_signatures(row)==review["observed_issue_signatures"]
        historical=row.get("funding_status") in ("CHIUSO","INFORMATIVO")
        if not (valid_identity and unchanged and historical):
            row["archive_case_review"]={
                "disposition":"riesame_necessario","review_date":review_date,
                "reason":"Fonte, stato o diagnostiche modificati: la decisione precedente non è più applicabile"}
            continue
        row["archive_case_review"]={
            "disposition":review["disposition"],
            "review_date":review_date,
            "reason":review["motive"],
            "evidence_level":"metadati_e_natura_del_procedimento",
            "pdf_contents_verified":False,
            "original_diagnostics_preserved":True
        }
        if review["disposition"]==NON_FUNDING:
            row["opportunity_type"]="altro avviso"
            row["type_reason"]=review["motive"]
        if (review.get("catalog_title") and
                str(row.get("title") or "").strip().upper() in ("SCOPRI IL BANDO","LEGGI IL BANDO")):
            row["title"]=review["catalog_title"]
    return rows


def archive_review_summary(rows,reviews):
    expected={r["public_id"] for r in reviews}
    reviewed=[r for r in rows if r.get("public_id") in expected]
    decisions=Counter((r.get("archive_case_review") or {}).get("disposition","non_applicata")
                      for r in reviewed)
    unlisted=[r.get("public_id") for r in rows
              if r.get("assessment_document_issues") and r.get("public_id") not in expected]
    return {
        "registry_total":len(reviews),
        "matching_catalog_records":len(reviewed),
        "by_disposition":dict(sorted(decisions.items())),
        "new_unreviewed_ids":sorted(unlisted),
        "missing_registry_ids":sorted(expected-{r.get("public_id") for r in reviewed}),
        "known_raw_diagnostic_count":sum(len(r.get("assessment_document_issues") or [])
                                          for r in reviewed),
        "note":"39 casi storici con decisione esplicita; gli allegati non letti non sono attestati come verificati."
    }
