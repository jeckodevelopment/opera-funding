#!/usr/bin/env python3
"""One-off smoke test: real Resend delivery with configured GitHub secrets.

No catalog changes, no ledger mutations, no recipient addresses in logs.
"""
import os
from datetime import datetime, timezone
from notify import FROM_ADDRESS, DASHBOARD, parse_recipients, post_resend

def main():
    key=os.getenv("RESEND_API_KEY","")
    raw=os.getenv("FUNDING_ALERT_RECIPIENT","")
    if not key or not raw:
        raise RuntimeError("Secrets RESEND_API_KEY e FUNDING_ALERT_RECIPIENT non configurati")
    recipients=parse_recipients(raw)
    if not recipients:
        raise RuntimeError("Nessun destinatario configurato")
    date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    subject="Opera+ Funding — verifica invio notifiche"
    html=(
        "<!doctype html><html lang='it'><body style='font-family:Arial,sans-serif;"
        "color:#17212b;max-width:640px;margin:24px auto'>"
        "<h2>Opera+ Funding</h2><p><strong>Invio di prova riuscito.</strong></p>"
        "<p>Questo messaggio verifica il sistema di notifiche automatiche "
        "tramite il dominio updates.opera.plus. Non segnala un nuovo bando.</p>"
        "<p>Data di esecuzione: "+date+"</p>"
        "<p><a href='"+DASHBOARD+"'>Apri Opera+ Funding</a></p>"
        "</body></html>"
    )
    body=("Invio di prova Opera+ Funding. Non segnala un nuovo bando.\n"
          "Data: "+date+"\nDashboard: "+DASHBOARD)
    count=0
    for address in recipients:
        # Unique per recipient, fixed for all reruns of the same GitHub job.
        # Never print addresses or response IDs.
        import hashlib, hmac
        token=hmac.new(key.encode(),address.casefold().encode(),"sha256").hexdigest()[:32]
        job=os.getenv("GITHUB_RUN_ID","local")
        post_resend(key,address,subject,html,body,f"opera-smoke-{job}-{token}")
        count+=1
    print(f"Smoke test completato: {count} messaggi accettati da Resend.")
    print("La consegna finale nelle caselle va verificata sui destinatari/Resend.")

if __name__=="__main__":
    main()
