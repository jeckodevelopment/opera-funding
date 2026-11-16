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
from priority import check_priority
from verification import pick_for_review, coverage
from crt_windows import guidance_for_window

ROOT = Path(__file__).resolve().parents[1]
AGENT = "OperaFundingBot/0.1 (+https://github.com/jeckodevelopment/opera-funding)"
INCLUDE = re.compile(r"bando|bandi|call|contribut|finanziament|avvis|grant|funding|progett|candidatur|partnership|opportunit", re.I)
IGNORE = re.compile(r"privacy|cookie|login|accesso|newsletter|contatt|instagram|facebook|linkedin|youtube|lavora con|whatsapp", re.I)
TOPICS = [
    (re.compile(r"cultur|cultural|musica|music|opera|liric|spettacol|artist|festival|theatr", re.I), 35, "cultura e spettacolo"),
    (re.compile(r"formazion|education|educazion|learning|student|scuol|giovan|youth", re.I), 25, "formazione e giovani"),
    (re.compile(r"digit|innova|video|audiovis|media|podcast", re.I), 20, "innovazione e contenuti digitali"),
    (re.compile(r"accessibil|inclusio|partecip|comunit|pubblic|audience", re.I), 20, "accessibilità e partecipazione")
]

def eligible_to_fetch(url, session):
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        response = session.get(robots_url, timeout=12)
        if response.status_code == 404:
            return True
        if response.status_code != 200:
            return False  # conservative
        robot = RobotFileParser()
        robot.parse(response.text.splitlines())
        return robot.can_fetch(AGENT, url)
    except requests.RequestException:
        return False

def score(title):
    themes = [name for pattern, _, name in TOPICS if pattern.search(title)]
    value = 20 + sum(weight for pattern, weight, name in TOPICS if name in themes)
    # Page-index snippet only: this is an initial relevance hint, not confirmed suitability.
    return min(100, value), themes

def discover(source, session, now):
    url = source["url"]
    if not eligible_to_fetch(url, session):
        raise RuntimeError("robots.txt unavailable/disallows access")
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
            "project_potential":"da valutare",
            "first_seen":now, "last_seen":now, "verified":False, "detail_checked":False
        })
    return rows

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default=str(ROOT / "config/sources.json"))
    parser.add_argument("--output", default=str(ROOT / "data/opportunities.json"))
    parser.add_argument("--report", default=str(ROOT / "data/scan-status.json"))
    args = parser.parse_args()
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    output = Path(args.output)
    existing = json.loads(output.read_text(encoding="utf-8")) if output.exists() else []
    indexed = {row["id"]: row for row in existing}
    priority_pages = json.loads((ROOT / "config/priority_pages.json").read_text(encoding="utf-8"))
    statuses = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with requests.Session() as session:
        session.headers.update({"User-Agent":AGENT, "Accept":"text/html"})
        for source in sources:
            try:
                found = discover(source, session, now)
                # Prioritize candidate funding calls over general archive entries.
                checked_count = 0
                review_limit = 6 if source.get("tier")=="high" else 3
                review_ids = pick_for_review(found,indexed,review_limit)
                found.sort(key=lambda x: (x.get("opportunity_type") not in ("finanziamento potenziale","call progettuale da verificare"),
                                          "2026" not in x.get("title","") and "2027" not in x.get("title",""),
                                          -x.get("relevance",0)))
                for item in found:
                    if item["id"] in indexed:
                        previous = indexed[item["id"]]
                        item["first_seen"] = previous.get("first_seen", now)
                        item["source_open_confirmed"] = item.get("status","").startswith("aperto")
                        # The verified detail page is stronger than an index snippet.
                        if previous.get("status_evidence"):
                            item["source_open_confirmed"] = previous.get("source_open_confirmed",False)
                            item["closure_confirmed"] = previous.get("closure_confirmed",False)
                            item["status_evidence"] = previous["status_evidence"]
                        # preserve data verified by future, dedicated detail-page extractors
                        for key in ("deadline", "amount", "eligibility", "project_potential", "verified", "status", "status_basis", "documents", "detail_checked", "detail_basis", "detail_checked_at", "detail_version", "detail_attempted_at", "beneficiaries_excerpt", "summary", "deadline_source", "deadline_verified_at", "application_windows", "opening_date", "opening_evidence", "status_evidence", "closure_confirmed", "link_status", "link_http_status", "link_checked_at", "resolved_url"):
                            if (previous.get("verified") or (previous.get("detail_checked") and key in ("deadline", "amount", "documents", "detail_checked", "detail_basis", "detail_checked_at", "detail_version", "beneficiaries_excerpt", "summary", "deadline_source", "deadline_verified_at", "application_windows", "opening_date", "opening_evidence", "status_evidence", "closure_confirmed")) or key in ("detail_attempted_at", "link_status", "link_http_status", "link_checked_at", "resolved_url")) and key in previous:
                                item[key] = previous[key]
                    if "source_open_confirmed" not in item:
                        item["source_open_confirmed"] = item.get("status","").startswith("aperto")
                    if item["id"] in review_ids:
                        item = enrich(item, source, session, eligible_to_fetch)
                        # Record every attempt, even when access is blocked, to avoid
                        # starving the rest of the queue on subsequent scans.
                        item["detail_attempted_at"] = now
                    if not item.get("link_checked_at") and checked_count < 8:
                        item = check_link(item, session, now)
                        checked_count += 1
                    indexed[item["id"]] = explain(annotate(reconcile_status(item)))
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
                statuses.append({"source_id":source["id"],"source_name":source["name"],"source_url":source["url"],"ok":False,"discovered":0,"checked_at":now,"error":str(exc)[:240]})
    # Reconcile retained historical links too; do not keep outdated open flags.
    for entry in indexed.values():
        explain(annotate(reconcile_status(entry)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sorted(indexed.values(), key=lambda o:(-o.get("relevance",0),o["title"])), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    Path(args.report).write_text(json.dumps({"checked_at":now,"sources":statuses,"coverage":coverage(list(indexed.values()),statuses)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Saved {len(indexed)} opportunity links; sources OK {sum(s['ok'] for s in statuses)}/{len(statuses)}")

if __name__ == "__main__":
    run()
