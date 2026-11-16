# Pubblicazione Opera+ Funding

La destinazione prevista è **https://jeckodevelopment.com/dev/funding/**. La dashboard è statica: il comando `python src/build_site.py` prepara `dist/` copiando HTML/CSS/JS e gli ultimi file pubblici `data/opportunities.json` e `data/scan-status.json`.

## GitHub Actions SFTP

Il workflow `Deploy Opera+ Funding dashboard` è predisposto, **ma disabilitato di default**.

In Settings → Secrets and variables → Actions configurare:
- Segreti obbligatori: `SFTP_HOST`, `SFTP_USERNAME`, `SFTP_REMOTE_DIR` (percorso remoto assoluto che mappa su `/dev/funding/`) e `SFTP_KNOWN_HOSTS` (riga known_hosts con chiave host attendibile, verificata fuori banda).
- Autenticazione: `SFTP_PRIVATE_KEY` **oppure** `SFTP_PASSWORD`.
- Segreto opzionale: `SFTP_PORT` (default 22).
- Variabile di repository: `FUNDING_DEPLOY_ENABLED=true` **solo dopo aver configurato e verificato tutto**.

Il deploy è attivato da modifiche a dati o frontend su main, oltre che manualmente. Il workflow **non elimina file remoti** e non pubblica documenti dei bandi, ma soltanto codice frontend e JSON pubblici. Nessuna credenziale deve entrare nei commit.

Il percorso SFTP reale dipende dal servizio hosting: verificare la corrispondenza con l'URL prima di abilitare il workflow. Il cron di scansione è lun/mer/ven alle 06:00 UTC (orario locale variabile con l'ora legale). GitHub Actions può ritardare i cron.
