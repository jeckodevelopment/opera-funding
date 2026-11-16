# Pubblicazione su jeckodevelopment.com/dev/funding

La dashboard è statica e legge `data/opportunities.json` e `data/scan-status.json` **relativamente alla cartella web**.

Per una pubblicazione manuale copiare il contenuto di `web/` in `/dev/funding/` e i due file `data/*.json` nella sottocartella `/dev/funding/data/`.

**Non è ancora configurato il deploy SFTP automatico.** Va aggiunto un workflow separato con GitHub Actions secrets (host, utente, password o chiave, path remoto) senza committare credenziali. Il workflow di scansione salva i dati nel repository; ciò da solo non aggiorna il sito finché non viene collegato il deploy.

I cron GitHub Actions usano UTC e possono partire in ritardo; il cron proposto è lunedì, mercoledì e venerdì alle 06:00 UTC.
