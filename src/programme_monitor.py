"""Monitor publisher-owned programme pages without inventing grant availability.

Fetch is gated by the shared robots policy. Fingerprints are computed from
visible main content and selected official candidate links, not volatile HTML.
Baseline is silent; a changed page is a review signal, not an open call.
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
import requests

CALL_TERMS = re.compile(r"\\b(?:band[oi]|avvis[oi]|call|contribut[oi]|liberalit[aà]|candidatur[ae]|finanziament[oi])\\b", re.I)
SKIP_PATH = re.compile(r"(?:privacy|cookie|faq|contatti|login|accedi|registrazione|rendicontazione)", re.I)

def _snapshot(html, official_url):
    soup=BeautifulSoup(html,"html.parser")
    for part in soup(["script","style","nav","footer","header","noscript"]):
        part.decompose()
    body=soup.select_one("main") or soup.select_one("article") or soup.body or soup
    text=" ".join(body.stripped_strings)
    text=re.sub(r"\\s+"," ",text).strip()[:80000]
    origin=urlparse(official_url).hostname
    links=[]
    for a in body.select("a[href]"):
        target,_=urldefrag(urljoin(official_url,a["href"]))
        parsed=urlparse(target)
        label=" ".join(a.stripped_strings).strip()
        if parsed.scheme!="https" or parsed.hostname!=origin or SKIP_PATH.search(parsed.path):
            continue
        if not CALL_TERMS.search(label+" "+parsed.path):
            continue
        links.append({"title":label[:180] or "Programma", "url":target})
    links=sorted({p["url"]:p for p in links}.values(),key=lambda x:x["url"])[:50]
    payload=json.dumps({"text":text,"links":links},ensure_ascii=False,sort_keys=True)
    return {"digest":hashlib.sha256(payload.encode("utf-8")).hexdigest(),"candidate_links":links}

def check_programmes(registry, previous, session, eligible_to_fetch, now):
    results={}
    for p in registry["programs"]:
        if p.get("monitoring")!="direct":
            continue
        url=p.get("url")
        if not url:
            results[p["id"]]={"status":"not_configured","last_checked_at":None}
            continue
        old=previous.get(p["id"],{})
        if not eligible_to_fetch(url,session):
            results[p["id"]]={"status":"error","error":"robots.txt: verifica automatica non consentita",
                              "last_checked_at":now,"last_success_at":old.get("last_success_at"),
                              "digest":old.get("digest"),"candidate_links":old.get("candidate_links",[])}
            continue
        response=None
        try:
            response=session.get(url,timeout=18,stream=True,allow_redirects=True)
            response.raise_for_status()
            target=urlparse(response.url)
            if target.scheme!="https" or target.hostname!=urlparse(url).hostname or target.port not in (None,443):
                raise ValueError("Redirect fuori dal dominio ufficiale")
            if "text/html" not in response.headers.get("Content-Type",""):
                raise ValueError("Risposta non HTML")
            size=0
            content=[]
            for block in response.iter_content(32768):
                size+=len(block)
                if size>1_000_000:raise ValueError("Pagina oltre il limite di sicurezza")
                content.append(block)
            encoding=response.encoding or "utf-8"
            snap=_snapshot(b"".join(content).decode(encoding,errors="replace"),response.url)
            had_baseline=bool(old.get("digest"))
            results[p["id"]]={"status":"ok","last_checked_at":now,"last_success_at":now,
                              "digest":snap["digest"],"candidate_links":snap["candidate_links"],
                              "changed":bool(had_baseline and old["digest"]!=snap["digest"]),
                              "baseline_created":not had_baseline}
        except (requests.RequestException,ValueError,UnicodeError) as exc:
            results[p["id"]]={"status":"error","error":str(exc)[:180],
                              "last_checked_at":now,"last_success_at":old.get("last_success_at"),
                              "digest":old.get("digest"),"candidate_links":old.get("candidate_links",[])}
        finally:
            if response is not None:response.close()
    return results

def load_programme_state(path):
    file=Path(path)
    return json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}

def public_status(state):
    """Never expose internal content hashes or past page bodies to clients."""
    return {key:{field:value for field,value in entry.items()
                 if field in ("status","error","changed","baseline_created","last_checked_at","last_success_at",
                              "candidate_links")}
            for key,entry in state.items()}
