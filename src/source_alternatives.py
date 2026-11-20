"""Status for authorised official alternative sources, never bypass robots.txt."""
def delegated_source_status(source, checked_sources, now):
    alternative_id=source["official_alternative_source_id"]
    upstream=next((entry for entry in checked_sources if entry["source_id"]==alternative_id),None)
    ok=bool(upstream and upstream.get("ok"))
    result={
        "source_id":source["id"],
        "source_name":source["name"],
        "source_url":source["url"],
        "ok":ok,
        "discovered":upstream.get("discovered",0) if ok else 0,
        "checked_at":now,
        "coverage_mode":"official_alternative",
        "alternative_source_id":alternative_id,
        "alternative_url":upstream.get("source_url") if upstream else None,
        "coverage_note":source.get("official_alternative_note")
    }
    if not ok:
        result["error"]="Catalogo ufficiale alternativo non disponibile"
    return result

from datetime import datetime, timezone, timedelta

RATE_LIMIT_BACKOFF=timedelta(hours=72)

def rate_limit_due(previous, now):
    """Retry the direct thematic endpoint no sooner than 72h after HTTP 429."""
    if not isinstance(previous,dict) or previous.get("coverage_mode")!="official_alternative_partial":
        return True
    stamp=previous.get("direct_last_429_at")
    if not isinstance(stamp,str):
        return True
    try:
        past=datetime.fromisoformat(stamp.replace("Z","+00:00"))
        current=datetime.fromisoformat(now.replace("Z","+00:00"))
        if past.tzinfo is None or current.tzinfo is None:
            return True
        return current-past>=RATE_LIMIT_BACKOFF
    except ValueError:
        return True

def rate_limited_source_status(source,checked_sources,now,last_429):
    """Partial official EU API coverage, never silently claim direct access."""
    alternative_id=source["rate_limit_alternative_source_id"]
    upstream=next((entry for entry in checked_sources if entry["source_id"]==alternative_id),None)
    ok=bool(upstream and upstream.get("ok"))
    result={
        "source_id":source["id"],"source_name":source["name"],
        "source_url":source["url"],"ok":ok,
        "discovered":upstream.get("discovered",0) if ok else 0,
        "checked_at":now,"coverage_mode":"official_alternative_partial",
        "direct_source_ok":False,"direct_last_429_at":last_429,
        "alternative_source_id":alternative_id,
        "alternative_url":upstream.get("source_url") if upstream else None,
        "coverage_note":"La fonte tematica ha risposto HTTP 429. Copertura parziale tramite API ufficiale Funding & Tenders; bandi culturali non presenti nell'API non sono certificati come monitorati."
    }
    if not ok:result["error"]="HTTP 429 sulla fonte diretta e API ufficiale alternativa non disponibile"
    else:result["warning"]="HTTP 429 sulla fonte diretta; monitoraggio ufficiale alternativo parziale"
    return result
