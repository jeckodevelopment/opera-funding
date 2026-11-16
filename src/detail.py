"""Bounded same-origin HTML enrichment of opportunities. Never archive page/PDF contents."""
import re
from urllib.parse import urlparse, urljoin, urldefrag
from datetime import date, datetime, timezone
from bs4 import BeautifulSoup
from classify import parse_deadline
from pdf_dates import pdf_deadline_from_documents
from structured import structured_facts

DEADLINE_PATTERN = re.compile(r"(?i)(?:scadenza|termine (?:di |per (?:la )?)?(?:presentazione|candidatur|domand)|deadline|apply by)\s*[:–-]?\s*(\d{1,2}[./-]\d{1,2}[./-]20\d{2})")
EUR_PATTERN = re.compile(r"(?i)(?:contributo massimo|finanziamento massimo|importo massimo|dotazione finanziaria|budget complessivo)\s*[:–-]?\s*(?:€|euro|eur)?\s*([\d.]+(?:,\d{2})?)\s*(?:€|euro|eur)?")
DOC_PATTERN = re.compile(r"(?i)\b(bando|avviso|faq|frequently asked|allegat|modulistic|domanda|regolamento|linee guida|document|application)\b")
BENEFICIARY_LABEL = re.compile(r"(?i)^(?:beneficiari|destinatari|soggetti ammissibili|chi può partecipare|eligible applicants)\s*[:–-]?")
MAX_DETAIL_LINKS = 8
MAX_HTML_BYTES = 1_000_000
DETAIL_SCHEMA_VERSION = 5

def safe_same_origin(link, origin):
    u = urlparse(link)
    root = urlparse(origin)
    return u.scheme == "https" and u.hostname == root.hostname and u.port in (None,443) and not u.username and not u.password

def extract(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "nav", "footer", "header"]):
        node.decompose()
    main = soup.select_one("main, article, .entry-content, .node__content") or soup.body or soup
    text = " ".join(main.stripped_strings)[:18000]
    match = DEADLINE_PATTERN.search(text)
    deadline = parse_deadline("Scadenza " + match.group(1)) if match else None
    amount = None
    match = EUR_PATTERN.search(text)
    if match:
        amount = "€ " + match.group(1) + " (da verificare)"
    beneficiaries = None
    for node in main.select("p, li"):
        candidate = " ".join(node.stripped_strings)[:450]
        if BENEFICIARY_LABEL.search(candidate) and len(candidate) > 20:
            beneficiaries = candidate
            break
    documents = [{"label":"Pagina del bando", "url":page_url}]
    seen = {page_url}
    for a in main.select("a[href]"):
        label = " ".join(a.stripped_strings)[:90]
        link, _ = urldefrag(urljoin(page_url, a["href"]))
        if link in seen or not safe_same_origin(link, page_url):
            continue
        if not (DOC_PATTERN.search(label) or link.lower().split("?")[0].endswith(".pdf")):
            continue
        documents.append({"label":label or "Documento ufficiale","url":link})
        seen.add(link)
        if len(documents) >= MAX_DETAIL_LINKS:
            break
    return {"deadline":deadline,"amount":amount,"beneficiaries_excerpt":beneficiaries,"documents":documents,"detail_checked":True,
            "detail_basis":"HTML della scheda; non include verifica di PDF o FAQ"}

def enrich(item, source, session, eligible_to_fetch):
    """Failure must not cause an opportunity to disappear from the dashboard."""
    url = item["url"]
    parsed_url=urlparse(url)
    allowed_hosts={urlparse(source["url"]).hostname,*(source.get("approved_detail_hosts") or [])}
    if (parsed_url.scheme!="https" or parsed_url.hostname not in allowed_hosts
            or parsed_url.port not in (None,443) or parsed_url.username or parsed_url.password):
        return item
    if urlparse(url).path.lower().endswith(".pdf"):
        # Some source indexes point directly to a PDF rather than an HTML page.
        deadline, pdf_url = pdf_deadline_from_documents(
            [{"label":"Documento ufficiale","url":url}],
            url, session, eligible_to_fetch, include_first=True
        )
        if deadline:
            item["deadline"]=deadline
            item["deadline_source"]=pdf_url
            item["deadline_verified_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
            item["documents"]=[{"label":"Documento ufficiale","url":pdf_url}]
            item["detail_checked"]=True
            item["detail_checked_at"]=item["deadline_verified_at"]
            item["detail_version"]=DETAIL_SCHEMA_VERSION
            item["detail_basis"]="Scadenza esplicita nel documento PDF ufficiale"
        return item
    if urlparse(url).path.lower().endswith((".doc",".docx",".zip")):
        return item
    if not eligible_to_fetch(url, session):
        return item
    try:
        response = session.get(url, timeout=12, stream=True)
        response.raise_for_status()
        if not safe_same_origin(response.url, url):
            return item
        if "text/html" not in response.headers.get("Content-Type",""):
            return item
        content = bytearray()
        for chunk in response.iter_content(chunk_size=32768):
            content.extend(chunk)
            if len(content)>MAX_HTML_BYTES:
                return item
        response._content = bytes(content)
        parsed = extract(response.text, response.url)
        structured = structured_facts(response.text, response.url)
        if structured["deadline"]:
            parsed["deadline"] = structured["deadline"]
            parsed["deadline_source"] = structured["deadline_source"]
        for key in ("opening_date","opening_evidence","source_open_confirmed","closure_confirmed","status_evidence","application_windows","summary"):
            if structured.get(key) is not None:
                item[key] = structured[key]
        if structured.get("beneficiaries_excerpt") and not parsed["beneficiaries_excerpt"]:
            parsed["beneficiaries_excerpt"] = structured["beneficiaries_excerpt"]
        if not parsed["deadline"] and parsed["documents"]:
            deadline, document_url = pdf_deadline_from_documents(parsed["documents"], url, session, eligible_to_fetch)
            if deadline:
                parsed["deadline"] = deadline
                parsed["deadline_source"] = document_url
        parsed["detail_checked_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
        parsed["detail_version"]=DETAIL_SCHEMA_VERSION
        for key in ("amount","beneficiaries_excerpt","documents","detail_checked","detail_basis","detail_checked_at","detail_version"):
            item[key] = parsed[key]
        if structured.get("source_open_confirmed"):
            item["status"] = "aperto (pagina ufficiale)"
            item["status_basis"] = "Stato aperto esplicito nella scheda ufficiale"
        if structured.get("closure_confirmed"):
            item["status"] = "chiuso"
            item["status_basis"] = "Stato chiuso esplicito nella scheda ufficiale"
        if parsed["deadline"]:
            item["deadline"] = parsed["deadline"]
            item["deadline_source"] = parsed.get("deadline_source") or response.url
            item["deadline_verified_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            if parsed["deadline"] < date.today().isoformat():
                item["status"] = "chiuso"
                item["status_basis"] = "scadenza esplicita della scheda trascorsa"
        return item
    except Exception:
        return item
    finally:
        if "response" in locals():
            response.close()
