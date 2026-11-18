"""Apply documented case-by-case assessments without changing official status."""
from urllib.parse import urlparse

REVIEW_FIELDS = ("assessment_label", "assessment_reason", "programme_objectives_excerpt",
                 "funded_activities_excerpt", "beneficiaries_excerpt", "requirements_excerpt",
                 "assessment_gaps")

def apply_assessment_reviews(rows, reviews):
    index = {(v.get("source_id"), urlparse(v.get("url", "")).path.rstrip("/").lower()):v
             for v in reviews}
    # Public numeric IDs are stable across official/aggregator URL aliases.
    # Require source agreement to avoid accidentally applying another issuer's review.
    by_id = {(v.get("source_id"), v.get("public_id")):v for v in reviews
             if isinstance(v.get("public_id"),int)}
    for row in rows:
        key=(row.get("source_id"),urlparse(row.get("url", "")).path.rstrip("/").lower())
        review=index.get(key)
        if not review or urlparse(row.get("url","")).hostname != urlparse(review.get("url","")).hostname:
            review=by_id.get((row.get("source_id"),row.get("public_id")))
        if not review:
            continue
        # Generic publisher buttons are not meaningful catalog titles.
        if str(row.get("title") or "").strip().upper() in ("SCOPRI IL BANDO", "LEGGI IL BANDO") and review.get("catalog_title"):
            row["title"]=review["catalog_title"]
        for field in REVIEW_FIELDS:
            if field in review:
                row[field]=review[field]
        row["assessment_basis"]="Revisione documentale della fonte indicata nella scheda"
        row["assessment_confidence"]="documentale — fonte consultata; ammissibilità da verificare"
        row["assessment_source"]=review.get("evidence_url") or review["url"]
        row["assessment_evidence_source"]=review.get("evidence_url") or review["url"]
        row["assessment_reviewed_at"]=review["reviewed_at"]
        if review.get("direct_application_blocker"):
            row["direct_application_blocker"]=review["direct_application_blocker"]
        row["assessment_opening_note"]="Valutazione di pertinenza indipendente dallo stato di apertura ufficiale."
    return rows
