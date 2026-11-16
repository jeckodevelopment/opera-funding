"""Conservative URL health and deadline reconciliation without hiding historical calls."""
from datetime import date, datetime, timezone
from urllib.parse import urlparse
import requests

def reconcile_status(row, today=None):
    today = today or date.today()
    deadline = row.get("deadline")
    if deadline:
        try:
            parsed = date.fromisoformat(deadline[:10])
            if parsed < today:
                row["status"] = "chiuso"
                row["status_basis"] = "scadenza trascorsa"
                return row
        except (ValueError, TypeError):
            pass
    # A source 'open' badge with no reliable deadline can be stale, even years later.
    if str(row.get("status","")).startswith("aperto") and not deadline:
        row["status"] = "non verificato"
        row["status_basis"] = "etichetta aperto non accompagnata da scadenza verificabile"
    return row

def check_link(item, session, now):
    url = item.get("url") or ""
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.port not in (None, 443)
            or not parsed.hostname or parsed.hostname.endswith((".local", ".internal"))
            or parsed.hostname in ("localhost", "127.0.0.1", "::1")):
        item["link_status"] = "da verificare"
        return item
    try:
        # Stream the response without downloading pages/documents; follow standard redirects.
        with session.get(url, timeout=10, stream=True, allow_redirects=True) as response:
            final = urlparse(response.url)
            if final.scheme != "https" or final.port not in (None, 443):
                item["link_status"] = "da verificare"
            elif response.status_code in (404, 410):
                item["link_status"] = "non disponibile"
            elif response.status_code == 200:
                item["link_status"] = "raggiungibile"
                item["resolved_url"] = response.url
            else:
                item["link_status"] = "da verificare"
            item["link_http_status"] = response.status_code
    except requests.RequestException:
        item["link_status"] = "da verificare"
    item["link_checked_at"] = now
    return item
