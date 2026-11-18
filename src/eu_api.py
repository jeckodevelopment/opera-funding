"""European Commission public Funding & Tenders API (documented SEDIA endpoint).

No login, proxy, browser spoofing or robots bypass. A failed API request does
not produce an empty successful scan.
"""
import json
import re
from datetime import date
from urllib.parse import quote
from classify import classify
from status import annotate
from fit import explain

API="https://api.tech.ec.europa.eu/search-api/prod/rest/search"
CREATIVE_EUROPE="43251814"
STATUSES=("31094501","31094502","31094503")
TOPIC=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,160}$")
DATE=re.compile(r"^(20\d{2}-\d{2}-\d{2})")
OPEN_LABELS=("open","open for submission","forthcoming","31094501","31094502")

def first(meta,*names):
    for name in names:
        val=meta.get(name)
        if isinstance(val,list) and val:val=val[0]
        if isinstance(val,(str,int,float)) and str(val).strip():return str(val).strip()
    return None

def iso(value):
    m=DATE.match(value or "")
    if not m:return None
    try:return date.fromisoformat(m.group(1)).isoformat()
    except ValueError:return None

def metadata_evidence(meta):
    """Use only explicitly named EU API fields, never infer applicant rules."""
    fields={
        "programme_objectives_excerpt":("topicDescription","description","objectives"),
        "funded_activities_excerpt":("eligibleActivities","scope","supportedActivities"),
        "beneficiaries_excerpt":("eligibleApplicants","applicantType","eligibleEntities"),
        "requirements_excerpt":("eligibilityConditions","applicationConditions","requirements"),
    }
    evidence={}
    for dest,names in fields.items():
        value=first(meta,*names)
        if not value or len(value)<35:
            continue
        clean=re.sub(r"<[^>]*>"," ",value)
        clean=" ".join(clean.split())[:700]
        if len(clean)>=35:
            evidence[dest]=clean
    return evidence

def api_result_to_opportunity(record,source,now):
    if not isinstance(record,dict):return None
    meta=record.get("metadata") or {}
    if not isinstance(meta,dict):return None
    title=first(meta,"title","name","topicTitle")
    topic=first(meta,"topicAbbreviation","topicIdentifier","callIdentifier")
    if not title or not topic or not TOPIC.fullmatch(topic):return None
    url="https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/"+quote(topic,safe="")
    opening=iso(first(meta,"openingDate","startDate","publicationDate"))
    deadline=iso(first(meta,"deadlineDate","submissionDeadline","nextDeadline","deadline"))
    published_status=(first(meta,"status","topicStatus") or "").lower()
    is_open=published_status in OPEN_LABELS and bool(deadline and deadline>=now[:10])
    classification=classify(title,title)
    result={
        "id":url.lower(),"title":title,**classification,
        "issuer":"European Commission – Creative Europe",
        "source_id":source["id"],"source_url":source["url"],"url":url,
        "documents":[{"label":"Scheda ufficiale UE","url":url}],
        "amount":None,"eligibility":"da verificare","project_potential":"da valutare",
        "first_seen":now,"last_seen":now,"verified":False,
        "detail_checked":False,
        "source_open_confirmed":is_open,
        "status":"aperto (metadati ufficiali UE)" if is_open else "non verificato",
        "status_evidence":url if published_status else None,
        "status_basis":"Metadati del portale ufficiale Funding & Tenders",
        "deadline":deadline,"deadline_source":url if deadline else None,
        "opening_date":opening,"opening_evidence":url if opening else None,
        "link_status":"non verificato"
    }
    evidence=metadata_evidence(meta)
    if evidence:
        result.update(evidence)
        result["assessment_evidence_source"]=url
        result["detail_basis"]="Metadati espliciti dell'API ufficiale UE"
    return explain(annotate(result))

def fetch_creative_europe(session,source,now):
    query={"bool":{"must":[
        {"terms":{"type":["1","2","8"]}},
        {"terms":{"status":list(STATUSES)}},
        {"terms":{"frameworkProgramme":[CREATIVE_EUROPE]}}
    ]}}
    params={"apiKey":"SEDIA","text":"*","pageSize":100,"pageNumber":1}
    data={
        "query":("query.json",json.dumps(query),"application/json"),
        "languages":("languages.json",'["en"]',"application/json"),
        "displayLanguage":(None,"en")
    }
    response=session.post(API,params=params,files=data,timeout=30,headers={"Accept":"application/json"})
    response.raise_for_status()
    payload=response.json()
    if not isinstance(payload,dict) or not isinstance(payload.get("results"),list):
        raise ValueError("Risposta API Funding & Tenders non valida")
    rows=[]
    for record in payload["results"]:
        opportunity=api_result_to_opportunity(record,source,now)
        if opportunity is not None:rows.append(opportunity)
    return rows
