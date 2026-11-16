"""Bounded extraction of explicitly labelled deadlines from official PDF attachments.

The PDF is held in memory only; it is not copied into the repository or dashboard.
"""
from io import BytesIO
from urllib.parse import urlparse
from pypdf import PdfReader
from classify import parse_deadline
import re

MAX_PDF_BYTES = 2_000_000
MAX_PAGES = 8
PDF_DATE = re.compile(
    r"(?i)(?:scadenza|termine (?:per |di )?(?:la )?(?:presentazione|candidatura|domande)|"
    r"deadline|apply by)\s*(?:delle domande)?\s*[:–-]?\s*"
    r"(\d{1,2}[./-]\d{1,2}[./-]20\d{2})"
)

def extract_pdf_deadline(payload):
    pdf = PdfReader(BytesIO(payload), strict=False)
    for page in pdf.pages[:MAX_PAGES]:
        content = (page.extract_text() or "")[:25000]
        match = PDF_DATE.search(" ".join(content.split()))
        if match:
            parsed = parse_deadline("Scadenza "+match.group(1))
            if parsed:
                return parsed
    return None

def pdf_deadline_from_documents(documents, source_url, session, eligible_to_fetch):
    source_host=urlparse(source_url).hostname
    for doc in documents[1:]:
        link=doc.get("url","")
        parsed=urlparse(link)
        if (parsed.scheme!="https" or parsed.hostname!=source_host or parsed.port not in (None,443)
                or not parsed.path.lower().endswith(".pdf")):
            continue
        if not eligible_to_fetch(link,session):
            continue
        response=None
        try:
            response=session.get(link,timeout=15,stream=True)
            response.raise_for_status()
            if (urlparse(response.url).hostname!=source_host or
                    "pdf" not in response.headers.get("Content-Type","").lower()):
                continue
            data=bytearray()
            for chunk in response.iter_content(chunk_size=32768):
                data.extend(chunk)
                if len(data)>MAX_PDF_BYTES:
                    break
            if len(data)>MAX_PDF_BYTES:
                continue
            value=extract_pdf_deadline(bytes(data))
            if value:
                return value, link
        except Exception:
            continue
        finally:
            if response is not None:
                response.close()
        break # one PDF document per detail, bounded workload
    return None, None
