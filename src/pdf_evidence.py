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
    found_fields = {}
    field_sources = {}
    diagnostics = []
    discrepancies = []
    # Complementary official documents (call and FAQ) may contain different
    # applicant requirements. Keep the first source for conflicting passages.
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
            diagnostics.append({"url":url,"status":"accesso_non_consentito"})
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
                diagnostics.append({"url":url,"status":"risposta_non_pdf_o_redirect_non_valido"})
                continue
            data = bytearray()
            for chunk in response.iter_content(chunk_size=32768):
                data.extend(chunk)
                if len(data) > MAX_BYTES:
                    break
            if len(data) > MAX_BYTES:
                diagnostics.append({"url":url,"status":"documento_troppo_grande"})
                continue
            try:
                extracted = pdf_extract_evidence(bytes(data))
            except Exception:
                diagnostics.append({"url":url,"status":"pdf_non_interpretabile"})
                continue
            if not extracted:
                # Could be image-only, or a text PDF without recognized facts.
                # Do not assert it was scanned without checking text extraction.
                diagnostics.append({"url":url,"status":"nessuna_evidenza_estratta"})
            else:
                diagnostics.append({"url":url,"status":"evidenze_estratte"})
            for field, value in extracted.items():
                if not value:
                    continue
                if field not in found_fields:
                    found_fields[field] = value
                    field_sources[field] = url
                elif " ".join(found_fields[field].casefold().split()) != " ".join(value.casefold().split()):
                    # Different passages are NOT necessarily contradictory.
                    # A reviewer must resolve document priority and meaning.
                    discrepancies.append({"field":field,"first_source":field_sources[field],
                                          "other_source":url,"status":"testi_diversi_da_verificare"})
            if len(found_fields) == len(LABELS):
                break
        except Exception:
            diagnostics.append({"url":url,"status":"download_non_riuscito"})
            continue
        finally:
            if response is not None:
                response.close()
    if diagnostics:
        found_fields["assessment_document_diagnostics"] = diagnostics
    if discrepancies:
        found_fields["assessment_document_discrepancies"] = discrepancies
    if field_sources:
        found_fields["assessment_evidence_source"] = next(iter(field_sources.values()))
        found_fields["assessment_field_sources"] = field_sources
    return found_fields
