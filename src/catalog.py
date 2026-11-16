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

# Explicitly checked identity: the syndication notice and the municipal
# application page describe the same Circoscrizione 7 / 2027 call, not two calls.
OFFICIAL_EQUIVALENTS={
    "https://infobandi.csvnet.it/culture-moves-europe-bando-per-la-mobilita-individuale-di-artisti-e-professionisti-della-cultura-2":
    "https://culture.ec.europa.eu/culture-moves-europe/call-for-individual-mobility",
    "https://volontariatotorino.it/bandi/circoscrizione-7-invito-a-presentare-progetti-per-iniziative-varie-anno-2027":
    "https://bandi.comune.torino.it/avviso/invito-presentare-progetti-iniziative-varie-anno-2027-circoscrizione-7"
}

def reconcile_official_equivalents(rows):
    """Coalesce only curated official/aggregator pairs with matching deadline.

    Retain the original syndicated URL as an alias; never merge different
    editions, missing deadlines, or mismatched confirmed windows.
    """
    by_url={_path(r.get("url")):r for r in rows}
    discard=set()
    for syndicated_url, official_url in OFFICIAL_EQUIVALENTS.items():
        syndicated=by_url.get(_path(syndicated_url))
        official=by_url.get(_path(official_url))
        if not syndicated or not official or syndicated is official:
            continue
        if syndicated.get("source_id")!="volto" or official.get("source_id") not in ("torino","eucreative"):
            continue
        if not syndicated.get("deadline") or syndicated["deadline"]!=official.get("deadline"):
            continue
        # Only propagate an authoritative, currently verified state if present.
        alternatives=set(official.get("alternative_urls") or [])
        alternatives.add(syndicated["url"])
        alternatives.update(syndicated.get("alternative_urls") or [])
        official["alternative_urls"]=sorted(alternatives-{official.get("url")})
        official["first_seen"]=min(official.get("first_seen") or "9999",syndicated.get("first_seen") or "9999")
        discard.add(id(syndicated))
    return [row for row in rows if id(row) not in discard]
