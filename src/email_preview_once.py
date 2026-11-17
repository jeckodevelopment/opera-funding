#!/usr/bin/env python3
"""One-time branded email preview to all configured recipients, no catalog writes."""
import hashlib
import os
from notify import parse_recipients,post_resend
from email_template import make_message

SAMPLES=[
    {"title":"Sostegno alla produzione culturale e artistica",
     "issuer":"Fondazione Esempio", "deadline":"2027-01-15",
     "summary":"Finanziamenti per progetti culturali, attività artistiche e iniziative formative.",
     "url":"https://jeckodevelopment.com/dev/funding/"},
    {"title":"Innovazione digitale per le arti performative",
     "issuer":"Programma Esempio", "deadline":"2027-01-31",
     "summary":"Progetti che integrano cultura, nuove tecnologie e coinvolgimento dei pubblici.",
     "url":"https://jeckodevelopment.com/dev/funding/"},
]

def main():
    key=os.environ.get("RESEND_API_KEY","")
    if not key:
        raise RuntimeError("Secret Resend non configurato")
    targets=parse_recipients(os.environ.get("FUNDING_ALERT_RECIPIENT",""))
    if not targets:
        raise RuntimeError("Secret destinatari non configurato")
    subject,html,plain=make_message(SAMPLES)
    subject="[ANTEPRIMA — BANDI FITTIZI] "+subject
    html=html.replace('<body style=', '<body style=',1).replace(
        '<h1 style=', '<p style="margin:12px 24px;padding:12px 14px;background:#f7f0e1;color:#805c2b;font:700 12px Arial,sans-serif;">'
        'ANTEPRIMA GRAFICA — BANDI E DATE DI ESEMPIO, NON OPPORTUNITÀ REALI</p><h1 style=',1)
    plain="ANTEPRIMA GRAFICA — bandi e date fittizi. Non è una notifica di nuovi bandi.\n\n"+plain
    run_id=os.environ.get("GITHUB_RUN_ID","preview")
    for target in targets:
        # Do not reveal emails in logs. A unique request for each target.
        fingerprint=hashlib.sha256(target.casefold().encode()).hexdigest()[:16]
        post_resend(key,target,subject,html,plain,"funding-preview-"+run_id+"-"+fingerprint)
    print(f"Resend ha accettato {len(targets)} anteprime email individuali. Verificare consegna e grafica nelle caselle.")

if __name__=="__main__":
    main()
