#!/usr/bin/env python3
"""One-shot dark-mode branded email preview; never changes opportunity/notification state."""
import hashlib
import os
from email_template import make_message
from notify import parse_recipients, post_resend

EXAMPLES=[
    {"title":"Sostegno alla produzione culturale e artistica",
     "issuer":"Fondazione Esempio", "deadline":"2027-01-15",
     "summary":"Finanziamenti per progetti culturali, attività artistiche e iniziative formative.",
     "url":"https://jeckodevelopment.com/dev/funding/"},
    {"title":"Innovazione digitale per le arti performative",
     "issuer":"Programma Esempio", "deadline":"2027-01-31",
     "summary":"Progetti culturali con tecnologie digitali, formazione e nuovi pubblici.",
     "url":"https://jeckodevelopment.com/dev/funding/"},
]

def main():
    key=os.getenv("RESEND_API_KEY") or ""
    raw=os.getenv("FUNDING_ALERT_RECIPIENT") or ""
    if not key or not raw:
        raise RuntimeError("Secrets delle notifiche mancanti")
    recipients=parse_recipients(raw)
    if not recipients:
        raise RuntimeError("Nessun destinatario valido")
    subject,html,text=make_message(EXAMPLES)
    subject="[PROVA DARK MODE — BANDI FITTIZI] "+subject
    notice="PROVA DARK MODE — LE OPPORTUNITÀ E LE DATE SONO FITTIZIE"
    html=html.replace(
        '<h1 style=',
        '<p style="margin:12px 24px;padding:12px 14px;background:#f7f0e1;'
        'color:#805c2b;font:700 12px Arial,sans-serif;">'+notice+'</p><h1 style=',1)
    text=notice+"\\nNon si tratta di una notifica di nuovi bandi.\\n\\n"+text
    run_id=os.getenv("GITHUB_RUN_ID","manual")
    for address in recipients:
        fingerprint=hashlib.sha256(address.casefold().encode()).hexdigest()[:16]
        post_resend(key,address,subject,html,text,
                    f"funding-dark-preview-{run_id}-{fingerprint}")
    print(f"Anteprima dark mode: {len(recipients)} messaggi accettati da Resend.")
    print("Indirizzi riservati. Consegna e contrasto del logo da verificare in casella.")

if __name__=="__main__":
    main()
