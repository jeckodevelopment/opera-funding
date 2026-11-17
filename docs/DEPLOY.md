# Pubblicazione Opera+ Funding

La dashboard è ospitata su https://jeckodevelopment.com/dev/funding/, mentre **i dati aggiornati provengono direttamente da GitHub**.

## Flusso dati e rilascio applicazione

1. **opera-funding** (repository pubblica): lo scanner aggiorna `data/opportunities.json` e `data/scan-status.json` sul ramo `main` tramite GitHub Actions, ogni lunedì/mercoledì/venerdì alle **06:00 UTC**, e dopo modifiche al motore di scansione. La pubblicazione del commit JSON non necessita SFTP.
2. Il browser della dashboard legge entrambi i file da:
   - `https://raw.githubusercontent.com/jeckodevelopment/opera-funding/main/data/opportunities.json`
   - `https://raw.githubusercontent.com/jeckodevelopment/opera-funding/main/data/scan-status.json`
3. Il browser richiede i JSON a ogni apertura (e tramite **Aggiorna dati**), con `cache: no-store` e senza credenziali. GitHub può applicare una cache CDN per alcuni minuti; **non è un feed istantaneo garantito**.
4. Se GitHub non è raggiungibile, entrambi i file vengono letti dal percorso locale `/dev/funding/data/`, cioè dalla copia di sicurezza pubblicata con l'ultima versione della dashboard. La pagina mostra esplicitamente **Copia locale di riserva** e la data della scansione: non spaccia la copia come aggiornata.
5. **jeckodevsite** (repository privata): il publisher esistente aggiorna soltanto i file HTML/CSS/JS e la copia di sicurezza dei JSON su `/dev/funding/` con SFTP, rollback e verifica HTTPS. **Il workflow è solo manuale**, da avviare dopo modifiche alla UI; non serve per ogni scansione.

## Costi e dipendenze

Non servono GitHub Pages, servizi esterni, token nel browser o nuove credenziali SFTP. L'accesso diretto ai file del repository pubblico è adatto al traffico limitato atteso. Le cache e la disponibilità di GitHub restano dipendenze note, mitigate dalla copia locale.

## Collaudo post-rilascio

1. Controllare l'ultima scansione in `data/scan-status.json` della repository pubblica.
2. Avviare una sola volta **Pubblica Opera+ Funding via SFTP** da jeckodevsite per rilasciare il nuovo `web/app.js`.
3. Aprire la pagina e verificare il testo **Dati live da GitHub** e l'ora della scansione.
4. Eseguire una nuova scansione, **senza** rilanciare il publisher SFTP, e verificare che la dashboard legga il timestamp aggiornato (tenendo conto della cache CDN di GitHub).
5. Simulare un errore del dominio raw GitHub nel browser; verificare che i dati locali siano ancora visibili, con avviso **Copia locale di riserva**.
6. Verificare che altri percorsi di jeckodevelopment.com non siano cambiati.

La qualità dei contenuti è indipendente dal canale di consegna: stati, scadenze, link e ammissibilità restano da validare secondo le regole in `docs/PRODUCT.md`.

## Aggiornamento cache GitHub (17/11/2026)
Per evitare una discrepanza temporanea tra il dataset presente in `main` e quello distribuito dalla CDN GitHub raw, ogni richiesta browser dei due JSON usa lo stesso identificatore temporale `?v=<millisecondi>`. Il comportamento `cache: no-store` rimane attivo; anche la copia locale utilizza lo stesso parametro senza cambiare il fallback. Il timestamp `checked_at` continua a riferirsi alla scansione, non alla richiesta del browser. **Questa modifica riguarda il JavaScript e richiede una nuova pubblicazione SFTP del frontend**.
