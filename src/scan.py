#!/usr/bin/env python3
"""Conservative index-page discovery; no invented award details."""
import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from classify import classify
from detail import enrich, DETAIL_SCHEMA_VERSION
from quality import check_link, reconcile_status
from status import annotate
from fit import explain
from catalog_changes import track_changes
from public_ids import assign_public_ids, attach_public_aliases
from priority import check_priority
from verification import pick_for_review, coverage, backlog_candidates, classify_crt_information, classify_informational_page
from crt_windows import guidance_for_window
from source_alternatives import delegated_source_status
from eu_api import fetch_creative_europe, fetch_topic_evidence
from catalog import deduplicate_catalog, reconcile_official_equivalents
from issuer_sources import apply_issuer_evidence
from reviewed_official import apply_reviewed_facts
from assessment_reviews import apply_assessment_reviews
from assessment_coverage import annotate_assessment_coverage, assessment_coverage
from adequacy import apply_adequacy
from eligibility_conditions import annotate_conditions
from eligibility_specific import annotate_specific_requirements
from applicant_comparison import load_applicant_profile, annotate_applicant_comparison
from open_review_queue import build_open_review_queue
from operational_assessment import annotate_operational_assessment
from catalog_reconciliation import (summarize_catalog_reconciliation, reconcile_catalog_assessments,
                                    annotate_requirement_coverage, summarize_requirement_coverage)
from catalog_audit import load_retired_sources, mark_retired_source, audit_catalog
from funder_registry import load_registry, link_opportunities, public_monitoring
from programme_monitor import check_programmes, load_programme_state, public_status
from programme_ingest import ingest_programme_calls

ROOT = Path(__file__).resolve().parents[1]
AGENT = "OperaFundingBot/0.1 (+https://github.com/jeckodevelopment/opera-funding)"
INCLUDE = re.compile(r"bando|bandi|call|contribut|finanziament|avvis|grant|funding|progett|candidatur|partnership|opportunit", re.I)
IGNORE = re.compile(r"privacy|cookie|login|accesso|newsletter|contatt|instagram|facebook|linkedin|youtube|lavora con|whatsapp", re.I)
TOPICS = [
    (re.compile(r"cultur|patrimon|heritage|\\barts?\\b|artistic|creative|muse|bibliotec",re.I),
     35,"cultura e patrimonio"),
    (re.compile(r"formazion|education|educazion|learning|student|scuol|giovan|youth|pcto|\\bpon\\b|fse\\+|erasmus",re.I),
     25,"educazione, scuola e giovani"),
    (re.compile(r"comunit|territor|inclus|accessib|partecip|rigeneraz|coesion|citizenship",re.I),
     20,"partecipazione culturale e comunità"),
    (re.compile(r"music|liric|opera|spettacol|artist|festival|theatr|laborator|workshop|masterclass",re.I),
     20,"arti performative e laboratori"),
    (re.compile(r"adult|lifelong|apprendimento permanente|invecchiamento attivo",re.I),
     15,"formazione culturale per adulti"),
    (re.compile(r"digit|innova|video|audiovis|media|podcast",re.I),
     15,"contenuti culturali digitali")
]

def eligible_to_fetch(url, session):
    """Respect robots.txt, retrieving it at most once per origin in a scan.

    Cache all responses only within this scan session, including access denial:
    retrying an unavailable robots endpoint for every PDF would turn a failed
    source into hundreds of redundant requests. Per-path allow rules still
    use RobotFileParser.can_fetch on every individual URL.
    """
    parts = urlparse(url)
    if parts.scheme!="https" or not parts.hostname:
        return False
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    cache=getattr(session,"_funding_robots_cache",None)
    if not isinstance(cache,dict):
        cache={}
        setattr(session,"_funding_robots_cache",cache)
    key=(parts.scheme,parts.netloc)
    if key not in cache:
        try:
            response=session.get(robots_url,timeout=12)
            if response.status_code==404:
                cache[key]=(True,"")
            elif response.status_code!=200:
                cache[key]=(False,f"robots.txt: risposta HTTP {response.status_code}; verifica automatica non disponibile")
            else:
                parser=RobotFileParser()
                parser.parse(response.text.splitlines())
                cache[key]=(parser,"")
        except requests.RequestException:
            cache[key]=(False,"robots.txt non raggiungibile; verifica automatica non disponibile")
    policy, diagnostic=cache[key]
    permitted = policy if isinstance(policy,bool) else policy.can_fetch(AGENT,url)
    if not permitted:
        diagnostics=getattr(session,"_funding_robots_diagnostics",None)
        if not isinstance(diagnostics,dict):
            diagnostics={}
            setattr(session,"_funding_robots_diagnostics",diagnostics)
        diagnostics[key]=diagnostic or "Accesso alla pagina non consentito dalle regole robots.txt"
    return permitted

def score(title):
    themes = [name for pattern, _, name in TOPICS if pattern.search(title)]
    value = 20 + sum(weight for pattern, weight, name in TOPICS if name in themes)
    # Page-index snippet only: this is an initial relevance hint, not confirmed suitability.
    return min(100, value), themes

def discover(source, session, now):
    url = source["url"]
    if not eligible_to_fetch(url, session):
        parsed=urlparse(url)
        reason=getattr(session,"_funding_robots_diagnostics",{}).get((parsed.scheme,parsed.netloc))
        raise RuntimeError(reason or "Regole robots.txt non verificabili; fonte non aggiornata")
    response = session.get(url, timeout=20)
    response.raise_for_status()
    if "text/html" not in response.headers.get("Content-Type", ""):
        raise RuntimeError("source does not return HTML")
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for a in soup.select("a[href]"):
        snippet = " ".join(a.get_text(" ", strip=True).split())[:600]
        if len(snippet) < 12 or not INCLUDE.search(snippet) or IGNORE.search(snippet):
            continue
        target, _ = urldefrag(urljoin(response.url, a["href"]))
        parsed = urlparse(target)
        if parsed.scheme != "https" or not parsed.netloc:
            continue
        if target.rstrip("/") == response.url.rstrip("/"):
            continue
        result = classify(snippet, snippet)
        if len(result["title"]) < 12 or result["title"].strip().lower() in ("scopri il bando", "leggi il bando", "consulta il bando"):
            continue
        rows.append({
            "id": target.lower().rstrip("/"), **result,
            "issuer": source["name"], "source_id": source["id"],
            "source_url": url, "url": target,
            "documents": [{"label":"Fonte da verificare", "url":target}],
            "amount": None, "eligibility":"da verificare",
            "project_potential":"valutazione al censimento",
            "first_seen":now, "last_seen":now, "verified":False, "detail_checked":False
        })
    return rows

# Trigger the configured main-branch scan after assessment reconciliation PR #140.
def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default=str(ROOT / "config/sources.json"))
    parser.add_argument("--output", default=str(ROOT / "data/opportunities.json"))
    parser.add_argument("--report", default=str(ROOT / "data/scan-status.json"))
    parser.add_argument("--history-backfill", action="store_true",
                        help="Inspect all pending historical records in one bounded sweep")
    args = parser.parse_args()
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    output = Path(args.output)
    existing = json.loads(output.read_text(encoding="utf-8")) if output.exists() else []
    retired_sources=load_retired_sources(ROOT / "config/retired_sources.json")
    # Preserve historic cards/IDs, but never carry an unverified old OPEN badge.
    indexed = {row["id"]: classify_informational_page(
        mark_retired_source(row,retired_sources)) for row in existing}
    priority_pages = json.loads((ROOT / "config/priority_pages.json").read_text(encoding="utf-8"))
    issuer_checks = json.loads((ROOT / "config/issuer_checks.json").read_text(encoding="utf-8"))
    reviewed_facts = json.loads((ROOT / "config/reviewed_official_facts.json").read_text(encoding="utf-8"))
    assessment_reviews = json.loads((ROOT / "config/assessment_reviews.json").read_text(encoding="utf-8"))
    statuses = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with requests.Session() as session:
        session.headers.update({"User-Agent":AGENT, "Accept":"text/html"})
        for source in sources:
            # Desk Italia does not permit reliable automated crawling. Treat
            # its official European Commission coverage as a delegated channel,
            # not as a successful request to the inaccessible Italian website.
            if source.get("official_alternative_source_id"):
                statuses.append(delegated_source_status(source,statuses,now))
                continue
            try:
                found = (fetch_creative_europe(session,source,now)
                         if source.get("discovery_mode")=="creative_europe_sedia_api"
                         else discover(source,session,now))
                # Prioritize candidate funding calls over general archive entries.
                checked_count = 0
                current_ids={item["id"] for item in found}
                backlog=backlog_candidates(indexed,source["id"],current_ids)
                review_limit = (max(250,len(found)+len(backlog)) if args.history_backfill
                                else 16 if source["id"] in ("volto","torino","mic")
                                else 12 if source.get("tier")=="high" else 10)
                found=[classify_informational_page(item) for item in found]
                backlog=[classify_informational_page(item) for item in backlog]
                # Every newly found opportunity is sent for official-document
                # inspection in its discovery scan, not merely classified by title.
                new_ids={item["id"] for item in found if item["id"] not in indexed}
                review_ids=pick_for_review(found+backlog,indexed,review_limit)
                review_ids.update(new_ids)
                if source["id"]=="eufunding":
                    # The F&T Portal is a dynamic SPA. Drain every EU topic that
                    # has never been queried through the official per-topic API
                    # in this scan, rather than making the archive wait for
                    # several daily batches of ten.
                    review_ids.update(item["id"] for item in found+backlog
                                      if indexed.get(item["id"],{}).get("assessment_review_status")=="NON ESAMINATA")
                if args.history_backfill:
                    # Revisit every incomplete historic record even if a prior
                    # partial HTML/PDF extraction was performed recently.
                    review_ids.update(item["id"] for item in found+backlog
                                      if indexed.get(item["id"],{}).get("assessment_review_status")
                                      not in ("REVISIONE DOCUMENTALE","EVIDENZE RACCOLTE"))
                    print(f"BACKFILL {source['id']}: {len(review_ids)} historical pages queued", flush=True)
                found.sort(key=lambda x: (x.get("opportunity_type") not in ("finanziamento potenziale","call progettuale da verificare","non classificato"),
                                          "2026" not in x.get("title","") and "2027" not in x.get("title",""),
                                          -x.get("relevance",0)))
                for item in found:
                    if item["id"] in indexed:
                        previous = indexed[item["id"]]
                        item["first_seen"] = previous.get("first_seen", now)
                        item["source_open_confirmed"] = item.get("status","").startswith("aperto")
                        # The verified detail page is stronger than an index snippet.
                        if previous.get("status_evidence") and source["id"]!="eufunding":
                            item["source_open_confirmed"] = previous.get("source_open_confirmed",False)
                            item["closure_confirmed"] = previous.get("closure_confirmed",False)
                            item["status_evidence"] = previous["status_evidence"]
                        # preserve data verified by future, dedicated detail-page extractors
                        for key in ("deadline", "amount", "eligibility", "project_potential", "verified", "status", "status_basis", "documents", "detail_checked", "detail_basis", "detail_checked_at", "detail_version", "detail_attempted_at", "beneficiaries_excerpt", "beneficiaries_source", "amount_kind", "amount_source", "rolling_guidance", "rolling_guidance_source", "summary", "programme_objectives_excerpt", "funded_activities_excerpt", "requirements_excerpt", "assessment_evidence_source", "assessment_field_sources", "assessment_document_diagnostics", "assessment_document_discrepancies", "deadline_source", "deadline_verified_at", "application_windows", "opening_date", "opening_evidence", "status_evidence", "closure_confirmed", "link_status", "link_http_status", "link_checked_at", "resolved_url"):
                            if (previous.get("verified") or (previous.get("detail_checked") and key in ("deadline", "amount", "documents", "detail_checked", "detail_basis", "detail_checked_at", "detail_version", "beneficiaries_excerpt", "beneficiaries_source", "amount_kind", "amount_source", "rolling_guidance", "rolling_guidance_source", "summary", "programme_objectives_excerpt", "funded_activities_excerpt", "requirements_excerpt", "assessment_evidence_source", "assessment_field_sources", "assessment_document_diagnostics", "assessment_document_discrepancies", "deadline_source", "deadline_verified_at", "application_windows", "opening_date", "opening_evidence", "status_evidence", "closure_confirmed")) or key in ("detail_attempted_at", "link_status", "link_http_status", "link_checked_at", "resolved_url")) and key in previous:
                                item[key] = previous[key]
                    if "source_open_confirmed" not in item:
                        item["source_open_confirmed"] = item.get("status","").startswith("aperto")
                    if item["id"] in review_ids:
                        item = (fetch_topic_evidence(item,session,now) if source["id"]=="eufunding"
                                else enrich(item, source, session, eligible_to_fetch))
                        # Record every attempt, even when access is blocked, to avoid
                        # starving the rest of the queue on subsequent scans.
                        if source["id"]!="eufunding" or item.get("detail_attempted_at"):
                            item["detail_attempted_at"] = now
                    if not item.get("link_checked_at") and checked_count < 8:
                        item = check_link(item, session, now)
                        checked_count += 1
                    indexed[item["id"]] = explain(annotate(reconcile_status(classify_informational_page(item))))
                # Revisit persisted calls dropped from current index navigation.
                # These are bounded by the same per-source review quota.
                for old in backlog:
                    if old["id"] not in review_ids:
                        continue
                    old=(fetch_topic_evidence(old,session,now) if source["id"]=="eufunding"
                         else enrich(old,source,session,eligible_to_fetch))
                    if old.get("detail_attempted_at") or source["id"]!="eufunding":
                        old["detail_attempted_at"]=now
                    indexed[old["id"]]=explain(annotate(reconcile_status(classify_informational_page(old))))
                # Small curated set of official call pages, rechecked every run.
                for target in (p for p in priority_pages if p["source_id"] == source["id"]):
                    key=target["url"].lower().rstrip("/")
                    verified=check_priority(target,source,session,eligible_to_fetch,now,indexed.get(key))
                    if verified is not None:
                        periods=verified.pop("individual_windows",[])
                        if periods:
                            # One persisted result per distinct official application window.
                            # The older page-level record is superseded to avoid a duplicate.
                            indexed.pop(key,None)
                            for period in periods:
                                row={**verified,**period}
                                row["id"]=key+"#window="+period["window_key"]
                                row["parent_id"]=key
                                row["title"]=target["title"]+" — "+period["window_label"]+" "+str(period["edition_year"])
                                row["summary"]=(
                                    "Contributo per "+("progetti culturali" if period["application_type"]=="Progetto" else "il sostegno delle attività culturali")+
                                    ". Finestra di candidatura "+period["opening_date"]+" – "+period["deadline"]+"."
                                )
                                row["closure_confirmed"]=False
                                row["source_open_confirmed"]=bool(
                                    (verified.get("source_open_confirmed") or period.pop("official_in_progress",False)) and
                                    period["opening_date"]<=now[:10]<=period["deadline"]
                                )
                                row["status"]="aperto (finestra ufficiale)" if row["source_open_confirmed"] else "non verificato"
                                row["status_basis"]="Finestra di candidatura riportata nella pagina ufficiale"
                                previous=indexed.get(row["id"],{})
                                row["first_seen"]=previous.get("first_seen",now)
                                row=explain(annotate(row))
                                hints=guidance_for_window(period["application_type"])
                                row.update(hints)
                                row["curated_project_ideas"]=hints["project_ideas"]
                                indexed[row["id"]]=row
                        else:
                            indexed[key]=verified
                statuses.append({"source_id":source["id"],"source_name":source["name"],"source_url":source["url"],"ok":True,"discovered":len(found),"checked_at":now})
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                failure={"source_id":source["id"],"source_name":source["name"],"source_url":source["url"],"ok":False,"discovered":0,"checked_at":now,"error":str(exc)[:240]}
                if source.get("institutional_reference_url"):
                    failure["institutional_reference_url"]=source["institutional_reference_url"]
                    failure["institutional_reference_label"]=source.get("institutional_reference_label","Fonte istituzionale integrativa")
                    failure["coverage_note"]="Storico conservato; la fonte integrativa non sostituisce la scansione ufficiale non riuscita."
                statuses.append(failure)
    # Check official company pages; only verified specific calls enter the catalog.
    registry_funders=load_registry(ROOT / 'config/funders.json')
    programme_state_path=ROOT / "data/programme-monitoring.json"
    previous_programmes=load_programme_state(programme_state_path)
    with requests.Session() as programme_session:
        programme_session.headers.update({"User-Agent":AGENT,"Accept":"text/html"})
        programme_state=check_programmes(registry_funders,previous_programmes,programme_session,eligible_to_fetch,now)
        programme_entries=[{**p,"funder_name":next((f["name"] for f in registry_funders["funders"] if f["id"]==p["funder_id"]),p["name"])} for p in registry_funders["programs"]]
        programme_ingestion=ingest_programme_calls(programme_entries,programme_state,indexed,programme_session,eligible_to_fetch,now)

    # Reconcile retained historical links too; do not keep outdated open flags.
    for entry in indexed.values():
        explain(annotate(reconcile_status(entry)))
    rows=reconcile_official_equivalents(deduplicate_catalog(list(indexed.values())))
    # Independent primary-source checks for a few recurring aggregator grants.
    # This cannot assume the aggregator listing itself confirms a live application.
    with requests.Session() as issuer_session:
        issuer_session.headers.update({"User-Agent":AGENT,"Accept":"text/html"})
        for row in rows:
            if row.get("source_id")=="volto":
                apply_issuer_evidence(row,None,issuer_checks,issuer_session,eligible_to_fetch,now)
                explain(annotate(reconcile_status(row)))

    # Reconcile the last five source-verified records with time-bounded evidence.
    # The factual deadline is durable; a historical OPEN assertion expires.
    apply_reviewed_facts(rows,reviewed_facts,now)
    for row in rows:
        explain(annotate(reconcile_status(row)))

    ids_path=ROOT / "data/opportunity-ids.json"
    registry=json.loads(ids_path.read_text(encoding="utf-8"))
    rows=assign_public_ids(rows, registry)
    rows=attach_public_aliases(rows, registry)
    rows=apply_assessment_reviews(rows, assessment_reviews)
    applicant_profile = load_applicant_profile()
    for row in rows:
        annotate_assessment_coverage(row)
        annotate_conditions(row)
        annotate_specific_requirements(row)
        annotate_applicant_comparison(row, applicant_profile, now[:10])
        apply_adequacy(row)
    assessment_fallback_count=reconcile_catalog_assessments(rows)
    for row in rows:
        annotate_requirement_coverage(row)
        annotate_operational_assessment(row)
    rows=link_opportunities(rows, registry_funders)
    rows=track_changes(rows, existing, now)
    catalogue_audit=audit_catalog(rows,retired_sources)
    programme_state_path.write_text(json.dumps(programme_state,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    ids_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    output.write_text(json.dumps(sorted(rows, key=lambda o:(-o.get("relevance",0),o["title"])), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    Path(args.report).write_text(json.dumps({"checked_at":now,"sources":statuses,"coverage":coverage(rows,statuses),"assessment_coverage":assessment_coverage(rows),
                                        "open_eligibility_review":build_open_review_queue(rows,now[:10]),
                                        "catalog_reconciliation":summarize_catalog_reconciliation(rows),
                                        "requirement_reconciliation":summarize_requirement_coverage(rows),
                                        "catalog_audit":catalogue_audit,
                                        "funder_monitoring":public_monitoring(registry_funders,statuses,now,public_status(programme_state)),
                                        "programme_ingestion":programme_ingestion},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Saved {len(rows)} opportunity links; sources OK {sum(s['ok'] for s in statuses)}/{len(statuses)}")

if __name__ == "__main__":
    run()
