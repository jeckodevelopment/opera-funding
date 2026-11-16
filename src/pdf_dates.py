"""Bounded verification of explicit official PDF application deadlines.

PDF bytes are processed in memory only. Never infer a deadline from a publication
date, a filename, or an unrelated timestamp. No OCR of scanned documents.
"""
from datetime import date
from io import BytesIO
from urllib.parse import urlparse
import re
from pypdf import PdfReader

MAX_PDF_BYTES = 5_000_000
MAX_PAGES = 16
MAX_DOCUMENTS = 3

MONTHS = {
    "gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,"giugno":6,
    "luglio":7,"agosto":8,"settembre":9,"ottobre":10,"novembre":11,"dicembre":12,
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12
}
DATE_TOKEN = r"(\d{1,2})\s*(?:[./-]\s*(\d{1,2})\s*[./-]\s*|\s+(" + "|".join(MONTHS) + r")\s+)(20\d{2})"
LABEL = (
    r"(?:scadenza(?:\s+(?:per|della|delle)\s+(?:la\s+)?(?:presentazione|candidatura|domande))?"
    r"|termine\s+ultimo(?:\s+per\s+(?:la\s+)?presentazione(?:\s+delle\s+domande)?)?"
    r"|termine\s+(?:di|per)\s+(?:la\s+)?(?:presentazione|candidatura|domande)"
    r"|deadline|apply\s+by"
    r"|(?:domande|candidature|istanze|proposte)\s+(?:devono\s+)?(?:essere\s+)?"
    r"(?:presentate|inviate|pervenire|trasmesse)\s+entro"
    r"|entro\s+(?:e\s+non\s+oltre\s+)?(?:il\s+)?(?:termine\s+del\s+)?)"
)
# Allow a short phrase such as "alle ore 12:00 del" between the label and date,
# but no intervening date or another independent section.
PDF_DATE = re.compile(r"(?i)\b" + LABEL + r"\b[^\d]{0,65}?" + DATE_TOKEN, re.I)
PRESENTATION_RANGE = re.compile(
    r"(?i)(?:presentazione\s+(?:delle\s+)?domande|invio\s+(?:delle\s+)?candidature)"
    r"[^\d]{0,60}?\bdal\s+" + DATE_TOKEN +
    r"\s+(?:alle\s+\d{1,2}(?:[.:]\d{2})?\s+)?al\s+" + DATE_TOKEN
)

def _match_date(match, first=1):
    try:
        day=int(match.group(first))
        numeric=match.group(first+1)
        month=int(numeric) if numeric else MONTHS[match.group(first+2).lower()]
        year=int(match.group(first+3))
        return date(year,month,day).isoformat()
    except (ValueError,TypeError,KeyError,IndexError):
        return None

def extract_pdf_deadline(payload, *, today=None):
    """Nearest upcoming explicitly labelled deadline; latest expired if all past."""
    today=today or date.today()
    pdf=PdfReader(BytesIO(payload), strict=False)
    dates=[]
    for page in pdf.pages[:MAX_PAGES]:
        text=" ".join((page.extract_text() or "")[:35000].split())
        for match in PDF_DATE.finditer(text):
            parsed=_match_date(match)
            if parsed:dates.append(parsed)
        for match in PRESENTATION_RANGE.finditer(text):
            parsed=_match_date(match,5)
            if parsed:dates.append(parsed)
    if not dates:return None
    future=[value for value in dates if value>=today.isoformat()]
    return min(future) if future else max(dates)

def pdf_deadline_from_documents(documents, source_url, session, eligible_to_fetch, *, include_first=False):
    """Try up to three permitted same-host PDFs; return date and original official URL."""
    source_host=urlparse(source_url).hostname
    inspected=0
    for doc in (documents if include_first else documents[1:]):
        link=doc.get("url","")
        parsed=urlparse(link)
        if (parsed.scheme!="https" or parsed.hostname!=source_host
                or parsed.port not in (None,443)
                or not parsed.path.lower().endswith(".pdf")):
            continue
        if not eligible_to_fetch(link,session):
            continue
        if inspected>=MAX_DOCUMENTS:break
        inspected+=1
        response=None
        try:
            response=session.get(link,timeout=15,stream=True,allow_redirects=True)
            response.raise_for_status()
            final=urlparse(response.url)
            if (final.scheme!="https" or final.hostname!=source_host
                    or final.port not in (None,443)
                    or "pdf" not in response.headers.get("Content-Type","").lower()):
                continue
            data=bytearray()
            for chunk in response.iter_content(chunk_size=32768):
                data.extend(chunk)
                if len(data)>MAX_PDF_BYTES:break
            if len(data)>MAX_PDF_BYTES:continue
            value=extract_pdf_deadline(bytes(data))
            if value:return value,link
        except Exception:
            continue
        finally:
            if response is not None:response.close()
    return None,None
