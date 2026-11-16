# Pubblicazione Opera+ Funding

La dashboard è destinata a https://jeckodevelopment.com/dev/funding/.

## Responsabilità delle repository

- **opera-funding** (pubblica): mantiene i sorgenti `web/`, i metadati `data/*.json`, il motore di scansione e il workflow di aggiornamento programmato lunedì, mercoledì e venerdì alle 06:00 UTC.
- **jeckodevsite** (privata): tramite `.github/workflows/publish-opera-funding.yml`, importa il contenuto di `web/` e i JSON da `opera-funding/main`, poi pubblica **soltanto** `/dev/funding/` con il publisher SFTP esistente, rollback e verifica HTTPS. Programmazione lunedì, mercoledì e venerdì alle 07:40 UTC e avvio manuale tramite GitHub Actions.

Non servono credenziali SFTP in questa repository pubblica. Il deploy usa i secret già configurati in jeckodevsite.

## Verifica manuale

1. Eseguire `Scan funding sources` in opera-funding e controllare `data/scan-status.json`.
2. Eseguire `Pubblica Opera+ Funding via SFTP` in jeckodevsite.
3. Verificare https://jeckodevelopment.com/dev/funding/ e che gli altri percorsi del sito non siano stati modificati.

Gli orari sono UTC: GitHub Actions può ritardare l'avvio; il publisher recupera l'ultimo snapshot disponibile. Il motore di ricerca iniziale scopre solo link delle pagine indice e non attesta ancora i requisiti di ammissibilità.
