"""Fair queue and factual coverage reporting for grant verification."""
from datetime import datetime, timezone, timedelta

PROJECT_TYPES={"finanziamento potenziale","call progettuale da verificare"}
SCHEMA_VERSION=7

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

def classify_informational_page(record):
    """Keep programme guidance and award notices without treating them as grants."""
    from urllib.parse import urlparse
    record=classify_crt_information(record)
    source=record.get("source_id")
    title=(record.get("title") or "").lower()
    path=urlparse(record.get("url") or "").path.lower()
    is_information=False
    if source=="alcotra":
        is_information=(path in ("/it/bandi","/it/bandi-0") or
                        "come-depositare" in path or "prodotti-dei-progetti" in path or
                        "progetti-finanziati" in path or "ciclo-di-vita" in path or
                        "presentazione-generale" in path)
    if source=="mic":
        is_information=(
            "assegnazione contribut" in title or
            "consuntiv" in title or "rendicont" in title or
            "concessione dei contributi" in title or
            "consuntiv" in path or
            "assegnazione-contribut" in path or
            "contributi-fnsv-fondo-nazionale" in path or
            "news-avvisi" in path or
            "category/" in path or
            "contributi-extra-fus" in path or
            "progetti-speciali" in path or
            path.strip("/") in ("contributi-extra-fus","contributi-fus"))
    if source=="erasmusitalia":
        # The national agency index mixes application calls with guides, forms,
        # historical allocation decisions and navigation pages.
        is_information=(
            path.endswith((".pdf", ".doc", ".docx")) or
            any(fragment in path for fragment in ("/esiti/", "/come-fare-domanda/", "/opportunita-erasmus/")) or
            any(term in title for term in ("linee guida", "disposizioni nazionali",
                                           "assegnazione del budget", "moduli di candidatura",
                                           "fondi comunitari destinati", "nota congiunta"))
        )
    if source=="sanpaolo":
        # Institutional project showcases do not accept new applications.
        is_information=path.startswith("/it/i-progetti/")
    if source=="piemonte":
        # Pre-information is an announcement, not an application that can be submitted.
        is_information=(path.rstrip("/") in ("/contributi-finanziamenti", "/crowdfunding")
                        or path.startswith("/pre-informazione-fondi-ue/"))
    if source=="eucreative":
        # Thematic funding overview is a guide, not a specific call for proposals.
        is_information=path.rstrip("/") in ("/cultural-heritage/funding-opportunities-for-cultural-heritage",)
    if source=="erasmusitalia" and path.rstrip("/") in ("/istruzione_superiore/partenariati-strategici-ka2-3",):
        is_information=True
    if source=="volto":
        is_information=(path.rstrip("/") in ("/progetti-volto","/progetti-servizio-civile"))
    if source=="torino":
        is_information=("linee-guida-concessione-lerogazione-contributi-ordinari-altri-benefici-economici-lanno-2027" in path or
                        "approvazione contributo" in title or
                        "contributo in servizi all" in title or
                        path.lower().endswith((".pdf",".docx")))
    if is_information:
        record["opportunity_type"]="altro avviso"
        record["type_reason"]="Pagina informativa, esito di contributo o documento, non una nuova candidatura"
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
            "dated":0,"dated_with_source":0,"detail_checked":0,"reachable":0,
            "candidate_unverified":0,"informational_unverified":0,
            "candidate_missing_deadline":0}
    by_source={}
    for row in rows:
        sid=row.get("source_id","unknown")
        entry=by_source.setdefault(sid,{"total":0,"open":0,"unverified":0,"dated":0,"dated_with_source":0,"detail_checked":0,
                                        "candidate_unverified":0,"informational_unverified":0,"candidate_missing_deadline":0})
        entry["total"]+=1
        state=row.get("funding_status","DA VERIFICARE")
        bucket={"APERTO":"open","CHIUSO":"closed","IN ARRIVO":"upcoming"}.get(state,"unverified")
        totals[bucket]+=1
        if bucket in ("open","unverified"):entry[bucket]+=1
        candidate=row.get("opportunity_type") in PROJECT_TYPES
        if bucket=="unverified":
            key="candidate_unverified" if candidate else "informational_unverified"
            totals[key]+=1
            entry[key]+=1
        if candidate and not row.get("deadline"):
            totals["candidate_missing_deadline"]+=1
            entry["candidate_missing_deadline"]+=1
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
