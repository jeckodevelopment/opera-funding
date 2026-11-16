"""Fair queue and factual coverage reporting for grant verification."""
from datetime import datetime, timezone, timedelta

PROJECT_TYPES={"finanziamento potenziale","call progettuale da verificare"}
SCHEMA_VERSION=4

def _when(raw):
    try:
        moment=datetime.fromisoformat(str(raw))
        return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None

def needs_review(item, now=None):
    now=now or datetime.now(timezone.utc)
    if item.get("detail_version")!=SCHEMA_VERSION or not item.get("detail_checked"):
        return True
    last=_when(item.get("detail_checked_at"))
    return last is None or last < now-timedelta(days=3)

def queue_key(item, now=None):
    """Unvisited first; avoid repeating failed candidates every scan."""
    attempted=_when(item.get("detail_attempted_at"))
    now=now or datetime.now(timezone.utc)
    deadline=str(item.get("deadline") or "")
    expired=bool(deadline and deadline[:10]<now.date().isoformat())
    closed=expired or item.get("funding_status")=="CHIUSO" or item.get("status")=="chiuso"
    project=item.get("opportunity_type") in PROJECT_TYPES
    # First unattempted funding calls, then least recently checked, then archives.
    return (
        0 if project and not closed else 1 if project else 2,
        0 if attempted is None else 1,
        attempted.isoformat() if attempted else "",
        -int(item.get("relevance") or 0),
        item.get("id") or item.get("url") or ""
    )

def classify_crt_information(record):
    """Exclude CRT press articles from grant candidates, without falsifying status."""
    from urllib.parse import urlparse
    if (record.get("source_id")=="crt"
            and not urlparse(record.get("url") or "").path.startswith("/bandi-progetti/")):
        record["opportunity_type"]="altro avviso"
        record["type_reason"]="Articolo informativo CRT, non una scheda di candidatura"
    return record

def backlog_candidates(existing, source_id, discovered_ids):
    """Revisit persisted opportunities no longer linked from the current index.

    Do not waste the document budget on confirmed closed calls, parent records
    superseded by individual funding windows, or informational notices.
    """
    return [dict(item) for item in existing.values()
            if item.get("source_id")==source_id
            and item.get("id") not in discovered_ids
            and not item.get("parent_id")
            and item.get("funding_status")!="CHIUSO"
            and item.get("opportunity_type") in PROJECT_TYPES]

def pick_for_review(found, existing, limit, now=None):
    now=now or datetime.now(timezone.utc)
    eligible=[]
    for item in found:
        if item.get("opportunity_type") not in PROJECT_TYPES:
            continue
        old=existing.get(item["id"],{})
        combined={**old,**item}
        # Preserve actual review metadata when source index rediscovery resets it.
        for k in ("detail_checked","detail_checked_at","detail_version","detail_attempted_at","funding_status"):
            if k in old:combined[k]=old[k]
        if needs_review(combined,now):
            eligible.append(combined)
    eligible.sort(key=lambda x:queue_key(x,now))
    return {x["id"] for x in eligible[:limit]}

def coverage(rows, sources):
    totals={"all":len(rows),"open":0,"closed":0,"upcoming":0,"unverified":0,
            "dated":0,"dated_with_source":0,"detail_checked":0,"reachable":0}
    by_source={}
    for row in rows:
        sid=row.get("source_id","unknown")
        entry=by_source.setdefault(sid,{"total":0,"open":0,"unverified":0,"dated":0,"dated_with_source":0,"detail_checked":0})
        entry["total"]+=1
        state=row.get("funding_status","DA VERIFICARE")
        bucket={"APERTO":"open","CHIUSO":"closed","IN ARRIVO":"upcoming"}.get(state,"unverified")
        totals[bucket]+=1
        if bucket in ("open","unverified"):entry[bucket]+=1
        for key,yes in (("dated",bool(row.get("deadline"))),
                        ("dated_with_source",bool(row.get("deadline") and row.get("deadline_source"))),
                        ("detail_checked",bool(row.get("detail_checked_at"))),
                        ("reachable",row.get("link_status")=="raggiungibile")):
            if yes:
                totals[key]+=1
                if key in entry:entry[key]+=1
    return {"totals":totals,"by_source":by_source,
            "sources_ok":sum(1 for x in sources if x.get("ok")),
            "sources_total":len(sources)}
