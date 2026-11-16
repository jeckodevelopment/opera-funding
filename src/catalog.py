"""Conservative deduplication of identical CSVnet syndication entries.

Never merge separate editions, dated application windows or distinct grant
sources; retain an audit trail of alias URLs.
"""
from urllib.parse import urlparse

def _csvnet(row):
    return row.get("source_id")=="volto" and urlparse(row.get("url") or "").hostname=="infobandi.csvnet.it"

def _path(url):
    return urlparse(url or "").path.rstrip("/").lower()

def deduplicate_catalog(rows):
    merged={}
    remaining=[]
    for row in rows:
        if not (_csvnet(row) and row.get("deadline") and row.get("title") and not row.get("window_key") and not row.get("parent_id")):
            remaining.append(row)
            continue
        key=("volto",row["title"].strip().casefold(),row["deadline"])
        merged.setdefault(key,[]).append(row)
    for group in merged.values():
        if len(group)==1:
            remaining.extend(group)
            continue
        canonical=next((r for r in group if _path(r.get("url"))==_path(r.get("deadline_source"))),None)
        canonical=canonical or sorted(group,key=lambda r:(r.get("detail_checked_at") is None,r.get("url") or ""))[0]
        alternative=set(canonical.get("alternative_urls") or [])
        for other in group:
            if other is canonical:continue
            if other.get("url"):alternative.add(other["url"])
            alternative.update(other.get("alternative_urls") or [])
            if other.get("first_seen") and other["first_seen"]<canonical.get("first_seen","9999"):
                canonical["first_seen"]=other["first_seen"]
        canonical["alternative_urls"]=sorted(alternative-{canonical.get("url")})
        remaining.append(canonical)
    return remaining
