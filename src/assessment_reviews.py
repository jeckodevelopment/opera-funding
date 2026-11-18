"""Apply documented case-by-case assessments without changing official status."""
from urllib.parse import urlparse

REVIEW_FIELDS = ("assessment_label", "assessment_reason", "programme_objectives_excerpt",
                 "funded_activities_excerpt", "beneficiaries_excerpt", "requirements_excerpt",
                 "assessment_gaps")

def apply_assessment_reviews(rows, reviews):
    index = {(v.get("source_id"), urlparse(v.get("url", "")).path.rstrip("/").lower()):v
             for v in reviews}
    for row in rows:
        key=(row.get("source_id"),urlparse(row.get("url", "")).path.rstrip("/").lower())
        review=index.get(key)
        if not review:
            continue
        if row.get("url", "").split("/")[2].lower() != review["url"].split("/")[2].lower():
            continue
        for field in REVIEW_FIELDS:
            if field in review:
                row[field]=review[field]
        row["assessment_basis"]="Revisione documentale delle condizioni pubblicate dall'ente promotore"
        row["assessment_confidence"]="documentale — fonte ufficiale consultata; ammissibilità da verificare"
        row["assessment_source"]=review["url"]
        row["assessment_evidence_source"]=review["url"]
        row["assessment_reviewed_at"]=review["reviewed_at"]
        row["assessment_opening_note"]="Valutazione di pertinenza indipendente dallo stato di apertura ufficiale."
    return rows
