"""Turn verified programme-owned calls into catalogue records.

Only distinct official candidate pages with actual grant evidence are admitted.
The shared enrichment, status, adequacy, public-ID, and notification pipeline
then evaluates the records. Generic donation instructions are not call editions.
"""
import re
from urllib.parse import urlparse
from classify import classify
from detail import enrich
from quality import check_link, reconcile_status
from status import annotate
from fit import explain

SPECIFIC_CALL=re.compile(r"(?i)\b(?:bando|bandi|call|avviso|avvisi|contribut[oi]\s+per|finanziament[oi]\s+per|sostegno\s+(?:a|di|per)\s+progett[oi])\b")
GENERIC_URL=re.compile(r"(?i)/(?:come-richiedere|contatti|faq|progetti-terzo-settore|supporto-presentazione-progetti-terzo-settore|beneficenza|bandi|contributi)/?$")
VERIFIABLE_FIELDS=("deadline","opening_date","beneficiaries_excerpt","funded_activities_excerpt",
                   "amount","requirements_excerpt","programme_objectives_excerpt")
MAX_PER_PROGRAMME=8

def qualified_candidate(candidate,programme):
    url=candidate.get("url","")
    label=" ".join(str(candidate.get("title") or "").split())
    target=urlparse(url)
    own=urlparse(programme.get("url") or "")
    if (target.scheme!="https" or not target.hostname or target.hostname!=own.hostname
            or target.port not in (None,443) or target.username or target.password
            or url.rstrip("/")==programme.get("url","").rstrip("/")):
        return False
    if GENERIC_URL.search(target.path):
        return False
    if len(label)<16 or not SPECIFIC_CALL.search(label+" "+target.path.replace("-"," ")):
        return False
    # The title must name a specific initiative, not a generic donation page.
    if label.casefold() in {"bandi e contributi","bandi aperti","scopri i bandi",
                            "richiedi un contributo","come richiedere un contributo"}:
        return False
    return True

def ingest_programme_calls(programmes,monitor_state,indexed,session,eligible,now):
    """Mutate indexed in place; return structured diagnostics, no fabricated openings."""
    stats=[]
    known={row.get("url","").lower().rstrip("/") for row in indexed.values()}
    for p in programmes:
        if p.get("monitoring")!="direct":
            continue
        state=monitor_state.get(p["id"],{})
        if state.get("status")!="ok":
            stats.append({"program_id":p["id"],"new":0,"existing":0,"rejected":0})
            continue
        added=existing=rejected=0
        source={"id":"programme:"+p["id"],"name":p.get("funder_name") or p["name"],
                "url":p["url"],"tier":"medium"}
        for candidate in state.get("candidate_links",[])[:MAX_PER_PROGRAMME]:
            if not qualified_candidate(candidate,p):
                rejected+=1
                continue
            url=candidate["url"]
            key=url.lower().rstrip("/")
            if key in known or key in indexed:
                existing+=1
                continue
            title=candidate["title"]
            inferred=classify(title,title)
            if inferred.get("opportunity_type")=="non classificato":
                inferred["opportunity_type"]="call progettuale da verificare"
                inferred["classification_reason"]="Titolo di bando specifico; finanziamento e beneficiari da confermare"
            if inferred.get("opportunity_type") not in (
                    "finanziamento potenziale","call progettuale da verificare"):
                rejected+=1
                continue
            row={"id":key,**inferred,"title":title,"issuer":source["name"],
                 "source_id":source["id"],"source_url":source["url"],"url":url,
                 "funder_id":p["funder_id"],"program_id":p["id"],
                 "documents":[{"label":"Scheda ufficiale","url":url}],
                 "eligibility":"da verificare","project_potential":"da valutare",
                 "first_seen":now,"last_seen":now,"verified":False,
                 "source_open_confirmed":False,"closure_confirmed":False}
            row=enrich(row,source,session,eligible)
            if not row.get("detail_checked") or not any(row.get(k) for k in VERIFIABLE_FIELDS):
                rejected+=1
                continue
            row=check_link(row,session,now)
            if row.get("link_status")!="raggiungibile":
                rejected+=1
                continue
            indexed[key]=explain(annotate(reconcile_status(row)))
            known.add(key)
            added+=1
        stats.append({"program_id":p["id"],"new":added,"existing":existing,"rejected":rejected})
    return stats
