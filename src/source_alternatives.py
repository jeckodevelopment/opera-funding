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
