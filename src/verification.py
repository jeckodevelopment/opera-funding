"""Fair queue and factual coverage reporting for grant verification."""
from datetime import datetime, timezone, timedelta

PROJECT_TYPES={"finanziamento potenziale","call progettuale da verificare","non classificato"}
SCHEMA_VERSION=8

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
    """New and never-inspected records ahead of routine refreshes; archive included."""
    now=now or datetime.now(timezone.utc)
    attempted=_when(item.get("detail_attempted_at"))
    state=item.get("funding_status") or ""
    deadline=str(item.get("deadline") or "")
    expired=bool(deadline and deadline[:10]<now.date().isoformat())
    closed=expired or state=="CHIUSO" or item.get("status")=="chiuso"
    project=item.get("opportunity_type") in PROJECT_TYPES
    if not item.get("_already_indexed"):
        tier=0
    elif attempted is None:
        tier=1 if project and not closed else 2
    elif project and not closed:
        tier=3
    elif project:
        tier=4
    else:
        tier=5
    return (tier, attempted.isoformat() if attempted else "",
            -int(item.get("relevance") or 0), item.get("id") or item.get("url") or "")


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
            "assegnazione dei contributi" in title or
            "assegnazione-dei-contributi" in path or
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
                        or path.startswith("/pre-informazione-fondi-ue"))
        is_information=is_information or path.rstrip("/") in ("/bandi-pnrr-per-enti-locali",)
    if source=="eucreative":
        # Thematic funding overview is a guide, not a specific call for proposals.
        is_information=path.rstrip("/") in ("/cultural-heritage/funding-opportunities-for-cultural-heritage",)
    if source=="erasmusitalia" and path.rstrip("/") in ("/istruzione_superiore/partenariati-strategici-ka2-3",):
        is_information=True
    if source=="volto":
        is_information=(path.rstrip("/") in ("/progetti-volto","/progetti-servizio-civile"))
    if source=="erasmus":
        is_information=path.rstrip("/") in ("/opportunities",)
    if source=="torino":
        is_information=(path.rstrip("/")=="" or "linee-guida-concessione-lerogazione-contributi-ordinari-altri-benefici-economici-lanno-2027" in path or
                        "approvazione contributo" in title or
                        "contributo in servizi all" in title or
                        path.lower().endswith((".pdf",".docx")))
    if is_information:
        record["opportunity_type"]="altro avviso"
        record["type_reason"]="Pagina informativa, esito di contributo o documento, non una nuova candidatura"
    return record

def backlog_candidates(existing, source_id, discovered_ids):
    """Every retained historical record is eventually inspected, not just open calls.

    Individually generated application windows are evaluated via their official
    parent page and kept as records; don't fetch synthetic #window URLs.
    """
    return [dict(item) for item in existing.values()
            if item.get("source_id")==source_id
            and item.get("id") not in discovered_ids
            and not item.get("parent_id")]


def pick_for_review(found, existing, limit, now=None):
    """Fair bounded queue across all kinds, with new records first."""
    now=now or datetime.now(timezone.utc)
    eligible=[]
    seen=set()
    for item in found:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        old=existing.get(item["id"],{})
        combined={**old,**item,"_already_indexed":bool(old)}
        for key in ("detail_checked","detail_checked_at","detail_version",
                    "detail_attempted_at","funding_status"):
            if key in old:
                combined[key]=old[key]
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
