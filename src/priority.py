"""Recheck a very small curated list of official call pages on every scan.

An entry is not considered open until its own page yields dated evidence.
"""
from datetime import datetime, timezone
from urllib.parse import urlparse
from structured import structured_facts
from classify import classify
from status import annotate
from fit import explain
from crt_windows import extract_ordinarie_windows
from detail import extract

def official_alternative_facts(item, source, session, eligible):
    """Try explicitly curated same-host official page variants only when needed."""
    original=urlparse(item["url"])
    for alternative in item.get("official_alternative_urls", []):
        target=urlparse(alternative)
        if (target.scheme!="https" or target.hostname!=original.hostname
                or target.port not in (None,443) or target.username or target.password
                or not eligible(alternative,session)):
            continue
        response=None
        try:
            response=session.get(alternative,timeout=16,stream=True,allow_redirects=True)
            response.raise_for_status()
            final=urlparse(response.url)
            if (final.scheme!="https" or final.hostname!=original.hostname
                    or final.port not in (None,443)
                    or "text/html" not in response.headers.get("Content-Type","")):
                continue
            content=bytearray()
            for chunk in response.iter_content(32768):
                content.extend(chunk)
                if len(content)>1_200_000:break
            if len(content)>1_200_000:continue
            response._content=bytes(content)
            facts=structured_facts(response.text,response.url)
            if facts.get("deadline") and facts.get("source_open_confirmed"):
                return facts
        except Exception:
            continue
        finally:
            if response is not None:response.close()
    return None

def check_priority(item, source, session, eligible, now, previous=None):
    url=item["url"]
    if urlparse(url).hostname!=urlparse(source["url"]).hostname or not eligible(url,session):
        return None
    response=None
    try:
        response=session.get(url,timeout=16,stream=True,allow_redirects=True)
        response.raise_for_status()
        if urlparse(response.url).hostname!=urlparse(source["url"]).hostname:return None
        if "text/html" not in response.headers.get("Content-Type",""):return None
        content=bytearray()
        for chunk in response.iter_content(32768):
            content.extend(chunk)
            if len(content)>1200000:return None
        response._content=bytes(content)
        facts=structured_facts(response.text,response.url)
        if not (facts.get("deadline") and facts.get("source_open_confirmed")):
            verified_alternative=official_alternative_facts(item,source,session,eligible)
            if verified_alternative is not None:
                facts=verified_alternative
        details=extract(response.text,response.url)
        period_windows=extract_ordinarie_windows(response.text,response.url)
        base=classify(item["title"],"")
        result={
         "id":url.lower().rstrip("/"),**base,"title":item["title"],
         "issuer":source["name"],"source_id":source["id"],"source_url":source["url"],"url":url,
         "documents":details["documents"],
         "amount":details["amount"],"eligibility":"da verificare","project_potential":"da valutare",
         "verified":False,"detail_checked":True,"detail_basis":"Pagina ufficiale verificata con evidenze strutturate",
         "first_seen":(previous or {}).get("first_seen",now),"last_seen":now,
         "link_status":"raggiungibile","resolved_url":response.url,"link_checked_at":now,
         "link_http_status":200
        }
        if details.get("beneficiaries_excerpt"):
            result["beneficiaries_excerpt"]=details["beneficiaries_excerpt"]
        for k,v in facts.items():
            if v is not None:
                result[k]=v
        if period_windows:result["individual_windows"]=period_windows
        if facts["deadline"]:result["deadline_verified_at"]=now
        if facts["source_open_confirmed"]:
            result["status"]="aperto (pagina ufficiale)"
            result["status_basis"]="Stato aperto esplicito nella scheda ufficiale"
        if facts["closure_confirmed"]:
            result["status"]="chiuso"
            result["status_basis"]="Stato chiuso esplicito nella scheda ufficiale"
        return explain(annotate(result))
    except Exception:
        return None
    finally:
        if response is not None:response.close()
