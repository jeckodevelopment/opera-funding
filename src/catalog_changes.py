"""Conservative catalog change detection with an explicit first-run baseline.

Only changes to user-facing official facts generate "Aggiornata". Routine scans,
timestamps, score explanations and transient health/status checks do not.
"""
import hashlib
import json

TRACKING_VERSION = 1
TRACKED_FIELDS = (
    "title", "issuer", "opportunity_type", "deadline", "opening_date",
    "application_windows", "amount", "amount_kind", "beneficiaries_excerpt",
    "summary", "rolling_guidance", "documents", "application_type",
    "window_label", "edition_year",
)

def fingerprint(row):
    facts = {key: row.get(key) for key in TRACKED_FIELDS}
    # Document order is not meaningful; a changed document URL or label is.
    docs = facts.get("documents")
    if isinstance(docs, list):
        facts["documents"] = sorted(
            ({"label": d.get("label"), "url": d.get("url")}
             for d in docs if isinstance(d, dict)),
            key=lambda d: (str(d["url"]), str(d["label"])),
        )
    payload = json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def track_changes(rows, previous, now):
    """Annotate, never filter; establish baseline without retroactive novelty."""
    prior = {r["id"]: r for r in previous if isinstance(r, dict) and r.get("id")}
    has_baseline = any(p.get("catalog_tracking_version") == TRACKING_VERSION
                       for p in prior.values())
    for row in rows:
        old = prior.get(row["id"])
        current = fingerprint(row)
        row["catalog_tracking_version"] = TRACKING_VERSION
        row["catalog_fingerprint"] = current
        if old:
            for key in ("catalog_new_at", "catalog_updated_at"):
                if old.get(key):
                    row[key] = old[key]
            old_fp = old.get("catalog_fingerprint")
            if old_fp and old_fp != current:
                row["catalog_updated_at"] = now
        elif has_baseline:
            row["catalog_new_at"] = now
    return rows
