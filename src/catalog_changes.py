"""User-facing, evidence-based change events for actual amendments to calls.

A scanner enriching old descriptions, attachments or beneficiary snippets is NOT
a new official call revision. Tracking version 2 starts a clean baseline.
"""
import hashlib
import json

TRACKING_VERSION = 3
# Only application terms whose updates materially affect a candidate's action.
TRACKED_FIELDS = (
    "deadline", "opening_date", "application_windows",
    "rolling_confirmed", "rolling_guidance",
)

def _verified(row, field):
    # Structured dates require a cited source. Do not issue update badges for
    # guessed or uncited values from a generic index snippet.
    if field == "deadline":
        return row.get("deadline") if row.get("deadline_source") else None
    if field == "opening_date":
        return row.get("opening_date") if row.get("opening_evidence") else None
    if field == "application_windows":
        return row.get("application_windows") if row.get("deadline_source") else None
    if field in ("rolling_confirmed","rolling_guidance"):
        return row.get(field) if row.get("rolling_evidence") or row.get("rolling_guidance_source") else None
    return None

def fingerprint(row):
    facts = {field:_verified(row, field) for field in TRACKED_FIELDS}
    payload = json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def track_changes(rows, previous, now):
    """Keep new events, clear old noisy updates and start V2 baseline safely."""
    prior = {r["id"]:dict(r) for r in previous if isinstance(r,dict) and r.get("id")}
    # The historical rows may be reused in-place by the scanner. Snapshot their
    # previous tracking fields before changing current records.
    has_baseline = any(p.get("catalog_tracking_version")==TRACKING_VERSION
                       for p in prior.values())
    for row in rows:
        old=prior.get(row["id"])
        current=fingerprint(row)
        row["catalog_tracking_version"]=TRACKING_VERSION
        row["catalog_fingerprint"]=current
        row.pop("catalog_updated_at",None)
        # Existing new tags represent actual discovery, and are preserved.
        if old and old.get("catalog_new_at"):
            row["catalog_new_at"]=old["catalog_new_at"]
        # Never copy obsolete labels from v1/v2. Nor compare incompatible hashes.
        if old and old.get("catalog_tracking_version")==TRACKING_VERSION:
            if old.get("catalog_updated_at"):
                row["catalog_updated_at"]=old["catalog_updated_at"]
            if old.get("catalog_fingerprint") and old["catalog_fingerprint"]!=current:
                row["catalog_updated_at"]=now
        elif not old and has_baseline:
            row["catalog_new_at"]=now
    return rows
