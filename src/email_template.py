"""Email-safe Opera+ Funding visual layout, aligned with the public dashboard.

Tables and inline styles intentionally support Gmail, Apple Mail and Outlook.
No remote CSS, JavaScript, embedded font or tracking pixels.
"""
from datetime import date
from html import escape
from urllib.parse import urlparse

DASHBOARD="https://jeckodevelopment.com/dev/funding/"
LOGO="https://jeckodevelopment.com/dev/funding/assets/operaplus-logo.png"
MAX_ITEMS=12

def _date_label(value):
    months=("gennaio","febbraio","marzo","aprile","maggio","giugno","luglio",
            "agosto","settembre","ottobre","novembre","dicembre")
    try:
        value=date.fromisoformat(str(value)[:10])
        return f"{value.day} {months[value.month-1]} {value.year}"
    except (ValueError,TypeError):
        return "Da verificare"

def _safe_https(value):
    parsed=urlparse(str(value or ""))
    if parsed.scheme!="https" or not parsed.netloc or parsed.username or parsed.password:
        return DASHBOARD
    return str(value)

def _detail_link(item):
    """Use the published stable numeric opportunity ID, never a source URL as ID."""
    number=item.get("public_id")
    if type(number) is int and number>0:
        return f"{DASHBOARD}?opportunity={number}"
    # Non-catalog test rows or old records: link to the dashboard, not an
    # invented detail ID. The official source remains a separate link.
    return DASHBOARD


def make_message(items):
    shown=items[:MAX_ITEMS]
    count=len(items)
    subject=f"Opera+ Funding — {count} {'nuova opportunità' if count==1 else 'nuove opportunità'}"
    intro=(f"Abbiamo individuato {count} "
           f"{'nuova opportunità' if count==1 else 'nuove opportunità'} "
           "potenzialmente interessanti per i progetti culturali e formativi di Opera+.")
    entries=[]
    plain=[intro,""]
    for item in shown:
        title=escape(str(item.get("title") or "Opportunità"))
        issuer=escape(str(item.get("issuer") or item.get("source_name") or "Ente da verificare"))
        deadline=escape(_date_label(item.get("deadline")))
        url=escape(_safe_https(item.get("url")),quote=True)
        detail=escape(_detail_link(item),quote=True)
        adequacy=str(item.get("adequacy_label") or "DA VERIFICARE").upper()
        if adequacy not in ("ALTA","MEDIA","BASSA"):
            adequacy="DA VERIFICARE"
        funding=str(item.get("funding_status") or "DA VERIFICARE").upper()
        if funding not in ("APERTO","IN ARRIVO","DA VERIFICARE"):
            funding="DA VERIFICARE"
        adequacy_html=escape("Adeguatezza "+adequacy)
        funding_html=escape(funding)
        # An unavailable summary is better omitted than fabricated.
        summary=str(item.get("summary") or "").strip()
        summary_html=(
            '<tr><td style="padding:0 0 14px;color:#687176;font:13px/1.6 Arial,Helvetica,sans-serif;">'
            +escape(summary[:220])+'</td></tr>'
        ) if summary else ""
        entries.append(
            '<tr><td style="padding:0 24px 13px;">'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
            'style="border:1px solid #e5e2dc;border-radius:10px;border-collapse:separate;background:#ffffff;">'
            '<tr><td style="padding:20px 20px 18px;">'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="100%">'
            '<tr><td style="font:700 12px Arial,Helvetica,sans-serif;color:#626a6d;padding-bottom:12px;">'
            +issuer+'</td><td align="right" style="padding-bottom:12px;">'
            '<span style="display:inline-block;border:1px solid #b7dfc5;background:#e8f6ee;'
            'color:#167046;border-radius:4px;padding:5px 9px;font:700 10px Arial,Helvetica,sans-serif;">'+funding_html+'</span>'
            '</td></tr>'
            '<tr><td colspan="2" style="font:700 11px/1.5 Arial,Helvetica,sans-serif;color:#5b654d;padding-bottom:8px;">'+adequacy_html+'</td></tr>'
            '<tr><td colspan="2" style="padding:0 0 11px;font:normal 21px/1.3 Georgia,Times New Roman,serif;'
            'color:#25282a;">'
            '<a href="'+detail+'" style="color:#25282a;text-decoration:underline;text-decoration-color:#c4ab82;'
            'text-underline-offset:3px;">'+title+'</a></td></tr>'
            +summary_html+
            '<tr><td colspan="2" style="padding-top:13px;border-top:1px solid #eeeae4;">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            '<td style="font:12px/1.5 Arial,Helvetica,sans-serif;color:#737b80;">'
            'Scadenza <strong style="color:#293136;">'+deadline+'</strong></td>'
            '<td align="right" style="font:700 12px Arial,Helvetica,sans-serif;">'
            '<a href="'+url+'" style="color:#805c2b;text-decoration:underline;">Fonte ufficiale</a>'
            '</td></tr></table></td></tr>'
            '</table></td></tr></table></td></tr>'
        )
        plain.append(f"- {item.get('title') or 'Opportunità'}")
        plain.append(f"  Scheda: {_detail_link(item)}")
        plain.append(f"  Ente: {item.get('issuer') or item.get('source_name') or 'Da verificare'}")
        plain.append(f"  Stato: {funding} | Adeguatezza: {adequacy}")
        plain.append(f"  Scadenza: {_date_label(item.get('deadline'))}")
        plain.append(f"  Fonte: {_safe_https(item.get('url'))}")
        plain.append("")
    extra=count-len(shown)
    more=(f"Altre {extra} opportunità sono disponibili nella dashboard." if extra else "")
    if more: plain.append(more)
    plain.extend(["Consulta tutte le opportunità: "+DASHBOARD,
                  "Notifica informativa: verifica sempre requisiti e scadenze presso gli enti."])
    html=(
        '<!doctype html><html lang="it"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light"></head>'
        '<body style="margin:0;padding:0;background:#f7f6f3;color:#1f2225;">'
        '<div style="display:none;font-size:1px;color:#f7f6f3;line-height:1px;'
        'max-height:0;max-width:0;opacity:0;overflow:hidden;">'+escape(intro)+'</div>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f7f6f3;">'
        '<tr><td align="center" style="padding:24px 12px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" width="600" '
        'style="width:100%;max-width:600px;background:#ffffff;border:1px solid #e5e2dc;'
        'border-collapse:separate;border-radius:12px;">'
        '<tr><td style="padding:21px 24px;border-bottom:1px solid #e9e5dd;">'
        '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
        # The source logo has dark lettering on transparent pixels. Email
        # dark-mode engines can darken surrounding surfaces without recoloring
        # the image. A bounded opaque white tile plus a white CSS gradient
        # keeps a deliberate light area behind the original logo in clients
        # that preserve gradients under forced dark-mode inversion.
        '<td valign="middle" bgcolor="#ffffff" style="vertical-align:middle;'
        'background-color:#ffffff;background-image:linear-gradient(#ffffff,#ffffff);'
        'border:1px solid #e5e2dc;border-radius:8px;padding:9px 11px;">'
        '<img src="'+LOGO+'" alt="Opera+" width="140" '
        'style="display:block;width:140px;max-width:140px;height:auto;border:0;'
        'background-color:#ffffff;background-image:linear-gradient(#ffffff,#ffffff);"></td>'
        '<td style="vertical-align:middle;padding:0 16px;color:#d6d2cb;">|</td>'
        '<td style="vertical-align:middle;font:normal 23px Georgia,Times New Roman,serif;'
        'color:#25282a;">Funding'
        '<span style="display:block;font:10px Arial,Helvetica,sans-serif;'
        'letter-spacing:1px;color:#777f81;margin-top:5px;">OSSERVATORIO OPPORTUNITÀ</span>'
        '</td></tr></table></td></tr>'
        '<tr><td style="padding:30px 24px 21px;">'
        '<p style="margin:0 0 12px;color:#9c763b;letter-spacing:2px;'
        'font:700 10px Arial,Helvetica,sans-serif;">OPERA+ / FINANZIAMENTI</p>'
        '<h1 style="margin:0 0 12px;color:#25282a;letter-spacing:-.5px;'
        'font:normal 32px/1.15 Georgia,Times New Roman,serif;">Le opportunità da non perdere.</h1>'
        '<p style="margin:0;color:#677074;font:13px/1.75 Arial,Helvetica,sans-serif;">'
        +escape(intro)+'</p></td></tr>'
        +''.join(entries)+
        ('<tr><td style="padding:8px 24px 0;font:12px Arial,sans-serif;color:#677074;">'
         +escape(more)+'</td></tr>' if more else '')+
        '<tr><td align="center" style="padding:13px 24px 30px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
        '<td bgcolor="#252a2d" style="border-radius:7px;padding:14px 22px;">'
        '<a href="'+DASHBOARD+'" style="font:700 13px Arial,Helvetica,sans-serif;'
        'color:#ffffff;text-decoration:none;">Esplora tutte le opportunità</a>'
        '</td></tr></table></td></tr>'
        '<tr><td align="center" style="padding:19px 24px;background:#faf9f7;'
        'border-top:1px solid #e5e2dc;font:11px/1.7 Arial,Helvetica,sans-serif;color:#808487;">'
        '<strong style="display:block;color:#4e5558;font-size:12px;">Opera+ Funding</strong>'
        'Monitoraggio automatico delle opportunità di finanziamento.<br>'
        'Informazioni orientative: verifica requisiti e scadenze presso gli enti promotori.<br>'
        '<span style="color:#9b9b9b;">Notifica automatica · updates.opera.plus</span>'
        '</td></tr></table></td></tr></table></body></html>'
    )
    return subject,html,"\n".join(plain)
