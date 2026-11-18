"""Bounded official PDF assessment evidence. No OCR and no document archive."""
import re
from io import BytesIO
from urllib.parse import urlparse
from pypdf import PdfReader

MAX_BYTES = 5_000_000
MAX_PAGES = 16
MAX_DOCUMENTS = 2

LABELS = (
    ("programme_objectives_excerpt", re.compile(r"(?i)obiettiv|finalit|purpose|aims|priorit")),
    ("funded_activities_excerpt", re.compile(r"(?i)attivit.{0,35}(?:ammissib|finanziab|sostenut)|interventi ammissibili|eligible activities|spese ammissibili|progetti finanziabili")),
    ("beneficiaries_excerpt", re.compile(r"(?i)beneficiar|destinatar|soggetti ammissibili|eligible applicants|who can apply")),
    ("requirements_excerpt", re.compile(r"(?i)requisit|condizion|partenariat|cofinanziament|eligibility criteria|mandatory partners")),
)

def pdf_extract_evidence(data):
    """Read only bounded searchable text, retaining compact provenance-ready quotes."""
    pdf = PdfReader(BytesIO(data), strict=False)
    found = {}
    for page in pdf.pages[:MAX_PAGES]:
        text = page.extract_text() or ""
        lines = [" ".join(x.split()) for x in text.splitlines()]
        for i, line in enumerate(lines):
            if len(line) < 8:
                continue
            # Capture the labelled paragraph and a little surrounding context.
            passage = " ".join(lines[i:i+4])[:650]
            if len(passage) < 45:
                continue
            for field, pattern in LABELS:
                if field not in found and pattern.search(line):
                    found[field] = passage
            if len(found) == len(LABELS):
                return found
    return found

def official_pdf_evidence(documents, source_url, session, allowed_to_fetch):
    host = urlparse(source_url).hostname
    inspected = 0
    best = {}
    for item in documents:
        url = item.get("url", "") if isinstance(item, dict) else ""
        address = urlparse(url)
        if (address.scheme != "https" or address.hostname != host
                or address.port not in (None, 443)
                or not address.path.lower().endswith(".pdf")):
            continue
        if inspected >= MAX_DOCUMENTS:
            break
        if not allowed_to_fetch(url, session):
            continue
        inspected += 1
        response = None
        try:
            response = session.get(url, timeout=15, stream=True, allow_redirects=True)
            response.raise_for_status()
            final = urlparse(response.url)
            if (final.scheme != "https" or final.hostname != host or
                    final.port not in (None, 443) or
                    "pdf" not in response.headers.get("Content-Type", "").lower()):
                continue
            data = bytearray()
            for chunk in response.iter_content(chunk_size=32768):
                data.extend(chunk)
                if len(data) > MAX_BYTES:
                    break
            if len(data) > MAX_BYTES:
                continue
            found = pdf_extract_evidence(bytes(data))
            if len(found) > len(best):
                best = {**found, "assessment_evidence_source": url}
            if len(found) == len(LABELS):
                break
        except Exception:
            continue
        finally:
            if response is not None:
                response.close()
    return best
