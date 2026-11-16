"""Bounded same-origin HTML enrichment of opportunities. Never archive page/PDF contents."""
import re
from urllib.parse import urlparse, urljoin, urldefrag
from datetime import date
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
    if not safe_same_origin(url, source["url"]) or url.lower().split("?")[0].endswith((".pdf",".doc",".docx",".zip")):
        return item
    if not eligible_to_fetch(url, session):
        return item
    try:
        response = session.get(url, timeout=12, stream=True)
        response.raise_for_status()
        if not safe_same_origin(response.url, source["url"]):
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
        for key in ("opening_date","opening_evidence","source_open_confirmed","closure_confirmed","status_evidence"):
            if structured.get(key) is not None:
                item[key] = structured[key]
        if structured.get("beneficiaries_excerpt") and not parsed["beneficiaries_excerpt"]:
            parsed["beneficiaries_excerpt"] = structured["beneficiaries_excerpt"]
        if not parsed["deadline"] and parsed["documents"] and not item.get("deadline"):
            deadline, document_url = pdf_deadline_from_documents(parsed["documents"], source["url"], session, eligible_to_fetch)
            if deadline:
                parsed["deadline"] = deadline
                parsed["deadline_source"] = document_url
        for key in ("amount","beneficiaries_excerpt","documents","detail_checked","detail_basis"):

            item[key] = parsed[key]
        if structured.get("source_open_confirmed"):
            item["status"] = "aperto (pagina ufficiale)"
            item["status_basis"] = "Stato aperto esplicito nella scheda ufficiale"
        if structured.get("closure_confirmed"):
            item["status"] = "chiuso"
            item["status_basis"] = "Stato chiuso esplicito nella scheda ufficiale"
        if parsed["deadline"] and not item.get("deadline"):
            item["deadline"] = parsed["deadline"]
            item["deadline_source"] = parsed.get("deadline_source") or response.url
            item["deadline_verified_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")
            if parsed["deadline"] < date.today().isoformat():
                item["status"] = "chiuso"
                item["status_basis"] = "scadenza esplicita della scheda trascorsa"
        return item
    except Exception:
        return item
    finally:
        if "response" in locals():
            response.close()
