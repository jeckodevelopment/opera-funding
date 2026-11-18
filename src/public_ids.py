"""Permanent numeric public IDs for opportunities.

Catalog identities (row['id']) remain URLs for discovery, deduplication and
existing watchlists. Numeric public IDs are allocated once, without reuse,
from a committed registry retaining retired identities.
"""
from __future__ import annotations

def assign_public_ids(rows, registry):
    mapping = dict(registry.get("ids") or {})
    used = set()
    for key, value in mapping.items():
        if not isinstance(key, str) or not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError("Invalid public ID registry")
        if value in used:
            raise ValueError("Duplicate public ID in registry")
        used.add(value)
    next_id = max(int(registry.get("next_id") or 1), max(used, default=0) + 1)
    # Recover existing row IDs when migrating from earlier records, but never
    # overwrite an entry already locked in the persistent registry.
    for row in rows:
        key = row["id"]
        prior = row.get("public_id")
        if key in mapping:
            if prior is not None and prior != mapping[key]:
                raise ValueError("Public ID changed for existing opportunity")
        elif isinstance(prior, int) and not isinstance(prior, bool) and prior > 0:
            if prior in used:
                raise ValueError("Public ID conflict while recovering registry")
            mapping[key] = prior
            used.add(prior)
            next_id = max(next_id, prior + 1)
    # Stable first allocation, independent of current relevance and ordering.
    for row in sorted(rows, key=lambda item: item["id"]):
        key = row["id"]
        if key not in mapping:
            while next_id in used:
                next_id += 1
            mapping[key] = next_id
            used.add(next_id)
            next_id += 1
        row["public_id"] = mapping[key]
    registry["ids"] = mapping
    registry["next_id"] = next_id
    registry["version"] = 1
    return rows
