"""Bounded same-origin HTML enrichment of opportunities. Never archive page/PDF contents."""
import re
from urllib.parse import urlparse, urljoin, urldefrag
from datetime import date, datetime, timezone
from bs4 import BeautifulSoup
from classify import parse_deadline
from pdf_dates import pdf_deadline_from_documents
from pdf_evidence import official_pdf_evidence
from structured import structured_facts
from evidence import official_evidence

DEADLINE_PATTERN = re.compile(r"(?i)(?:scadenza|termine (?:di |per (?:la )?)?(?:presentazione|candidatur|domand)|deadline|apply by)\s*[:–-]?\s*(\d{1,2}[./-]\d{1,2}[./-]20\d{2})")
EUR_PATTERN = re.compile(r"(?i)(?:contributo massimo|finanziamento massimo|importo massimo|dotazione finanziaria|budget complessivo)\s*[:–-]?\s*(?:€|euro|eur)?\s*([\d.]+(?:,\d{2})?)\s*(?:€|euro|eur)?")
DOC_PATTERN = re.compile(r"(?i)\b(bando|avviso|faq|frequently asked|allegat|modulistic|domanda|regolamento|linee guida|document|application)\b")
BENEFICIARY_LABEL = re.compile(r"(?i)^(?:beneficiari|destinatari|soggetti ammissibili|chi può partecipare|eligible applicants)\s*[:–-]?")
# Field-specific headings avoid interpreting unrelated prose as eligibility rules.
# A heading alone never proves that an applicant or expense is eligible.
EVIDENCE_HEADINGS = (
    ("programme_objectives_excerpt", re.compile(r"(?i)^(?:obiettivi|obiettivo|finalit[aà]|purpose|aims?|priorit[aà]|objectives?|scope del (?:programma|bando))\b")),
    ("funded_activities_excerpt", re.compile(r"(?i)^(?:attivit[aà]|interventi|progetti|spese|costi)\s+(?:ammissibil|finanziabil|sostenut|eleggibil)|^eligible activities\b|^supported activities\b")),
    ("beneficiaries_excerpt", re.compile(r"(?i)^(?:beneficiari|destinatari|soggetti ammessi|soggetti ammissibili|chi pu[oò] partecipare|eligible applicants|who can apply)\b")),
    ("requirements_excerpt", re.compile(r"(?i)^(?:requisiti|condizioni|criteri di ammissibilit[aà]|eligibility criteria|mandatory partners|obblighi di partenariato|cofinanziamento)\b")),
)
EVIDENCE_INLINE = (
    ("programme_objectives_excerpt", re.compile(r"(?i)^(?:il (?:bando|programma|progetto) (?:ha (?:lo scopo|l.obiettivo)|mira a)|l.obiettivo (?:del bando|è))\b")),
    ("funded_activities_excerpt", re.compile(r"(?i)^(?:sono (?:finanziabili|ammissibili|sostenute) le (?:seguenti )?(?:attivit[aà]|spese)|(?:il bando|il contributo) finanzia\b|eligible activities include\b)")),
    ("beneficiaries_excerpt", re.compile(r"(?i)^(?:possono (?:presentare domanda|partecipare|candidarsi)|sono ammessi (?:a partecipare|alla candidatura)|eligible applicants include\b)")),
    ("requirements_excerpt", re.compile(r"(?i)^(?:è (?:obbligatorio|richiesto|necessario) (?:un |il )?(?:partenariato|cofinanziamento)|(?:i candidati|i richiedenti) devono\b|applicants must\b)")),
)

def _evidence_field(value, patterns):
    normalized = " ".join(value.split()).strip(" :–-")
    return next((field for field, pattern in patterns if pattern.search(normalized)), None)

def extract_assessment_evidence(main, page_url):
    """Extract factual text only from a labeled section or explicit assertion.

    A stray mention of 'partnership', 'requirements' or 'activities' in
    unrelated text is not enough to fill an evidence field.
    """
    found = {}
    active_field = None
    for node in main.select("h2, h3, h4, p, li, dt, dd"):
        snippet = " ".join(node.stripped_strings)
        if not snippet or len(snippet) > 3000:
            continue
        tag = node.name.lower()
        heading = _evidence_field(snippet, EVIDENCE_HEADINGS)
        if tag in ("h2", "h3", "h4", "dt"):
            active_field = heading
            continue
        if tag == "dd" and node.find_previous_sibling("dt"):
            active_field = _evidence_field(node.find_previous_sibling("dt").get_text(" ", strip=True), EVIDENCE_HEADINGS)
        if len(snippet) < 35:
            continue
        inline = _evidence_field(snippet, EVIDENCE_INLINE) or _evidence_field(snippet, EVIDENCE_HEADINGS)
        field = inline or active_field
        if not field or field in found:
            continue
        # Require the actual explanation rather than a heading or navigation.
        if len(snippet.split()) < 7:
            continue
        found[field] = snippet[:700]
        if len(found) == len(EVIDENCE_HEADINGS):
            break
    if found:
        found["assessment_evidence_source"] = page_url
    return found

MAX_DETAIL_LINKS = 8
MAX_HTML_BYTES = 1_000_000
DETAIL_SCHEMA_VERSION = 9

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
    facts=official_evidence(html,page_url)
    assessment_evidence=extract_assessment_evidence(main,page_url)
    matched_beneficiaries = beneficiaries or facts["beneficiaries_excerpt"] or assessment_evidence.get("beneficiaries_excerpt")
    return {**assessment_evidence,"deadline":deadline,"amount":amount or facts["amount"],
            "beneficiaries_excerpt":matched_beneficiaries,
            "beneficiaries_source":page_url if matched_beneficiaries else None,
            "amount_kind":facts["amount_kind"],"amount_source":facts["amount_source"] if facts["amount"] else (page_url if amount else None),
            "rolling_guidance":facts["rolling_guidance"],
            "rolling_guidance_source":facts["rolling_guidance_source"],
            "documents":documents,"detail_checked":True,
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
        pdf_facts = official_pdf_evidence([{"url":url}], url, session, eligible_to_fetch)
        for key, value in pdf_facts.items():
            item[key] = value
        if pdf_facts:
            item["detail_checked"] = True
            item["detail_checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            item["detail_version"] = DETAIL_SCHEMA_VERSION
            item["detail_basis"] = "Contenuti estratti dal documento PDF ufficiale"
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
        pdf_facts = official_pdf_evidence(parsed["documents"], url, session, eligible_to_fetch)
        pdf_sources = pdf_facts.get("assessment_field_sources") or {}
        for key, value in pdf_facts.items():
            if key in ("assessment_evidence_source", "assessment_field_sources"):
                continue
            if not parsed.get(key):
                parsed[key] = value
                if key in pdf_sources:
                    parsed.setdefault("assessment_field_sources", {})[key] = pdf_sources[key]
        if pdf_facts and not parsed.get("assessment_evidence_source"):
            parsed["assessment_evidence_source"] = pdf_facts.get("assessment_evidence_source")
        parsed["detail_checked_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
        parsed["detail_version"]=DETAIL_SCHEMA_VERSION
        for key in ("amount","beneficiaries_excerpt","beneficiaries_source","amount_kind","amount_source","rolling_guidance","rolling_guidance_source","documents","detail_checked","detail_basis","detail_checked_at","detail_version","programme_objectives_excerpt","funded_activities_excerpt","requirements_excerpt","assessment_evidence_source","assessment_field_sources"):
            if parsed.get(key) is not None or key not in item:
                item[key] = parsed.get(key)
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
