"""Canonical actionable status: no OPEN without evidence of an active application window."""
from datetime import date

OPEN_MARKERS = ("aperto", "attivo")
CLOSED_MARKERS = ("chiuso", "chiusa", "scaduto", "scaduta")

def _iso(raw):
    if not raw: return None
    try: return date.fromisoformat(str(raw)[:10])
    except (ValueError, TypeError): return None

def effective_status(record, today=None):
    today=today or date.today()
    end=_iso(record.get("deadline"))
    start=_iso(record.get("opening_date"))
    if record.get("closure_confirmed") or (end is not None and end < today):
        return "CHIUSO"
    if str(record.get("status","")).lower() in ("chiuso","chiusa","scaduto","scaduta") and not record.get("reopened_confirmed"):
        return "CHIUSO"
    # Archive/category pages do not accept applications even if their text
    # mentions an open grant elsewhere; do not display them as open calls.
    if record.get("opportunity_type")=="altro avviso":
        return "DA VERIFICARE"
    if start and start>today and record.get("opening_evidence"):
        return "IN ARRIVO"
    source_open = record.get("source_open_confirmed") is True
    # Both current application evidence and a dated end/window are mandatory.
    valid_window = (end is not None and end >= today) or (
        record.get("rolling_confirmed") is True and bool(record.get("rolling_evidence"))
    )
    link_ok = record.get("link_status") == "raggiungibile"
    if source_open and valid_window and link_ok and (start is None or start<=today):
        return "APERTO"
    return "DA VERIFICARE"

def annotate(record, today=None):
    record["funding_status"] = effective_status(record,today)
    return record
