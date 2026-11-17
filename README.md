# Opera+ Funding

Osservatorio open source per bandi, call e finanziamenti pertinenti ai progetti culturali e formativi di Opera+.

**Sito di destinazione:** https://jeckodevelopment.com/dev/funding/

## Stato

Progetto in avvio. Il motore raccoglie metadati e collegamenti alle fonti ufficiali, senza archiviare copie dei bandi. Pertinenza e ammissibilità sono valutazioni distinte: nessuna opportunità è nascosta a causa di requisiti da soddisfare.

Il registro delle fonti e le scelte funzionali sono documentati in `docs/`.

## Email per nuovi bandi

Le notifiche gratuite via Resend sono facoltative: configurazione, limiti, privacy e collaudi in [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md). Il mittente è `notifiche@updates.opera.plus` e il destinatario rimane un GitHub Secret. Senza credenziali la scansione continua, ma non invia email.

## Valutazione assistita nella dashboard

La dashboard pubblica rimane la vista principale e conserva l'intero catalogo, compresi gli avvisi a bassa rilevanza e quelli con dati incompleti. La scheda *Esamina opportunità* visualizza motivazione del punteggio, attendibilità, stato di ammissibilità, verifiche da compiere e dati mancanti, utilizzando i campi già estratti dal motore di scansione. Queste indicazioni non costituiscono un filtro, né modificano la classificazione o l'eventuale invio delle notifiche. L'assenza di una scadenza non implica la chiusura del bando: le opportunità a sportello possono essere prive di una data finale.

## Roadmap operativa confermata

L'attuale dashboard resta **la homepage del catalogo**, senza eliminazioni automatiche per rilevanza o ammissibilità. Sette aree incrementali: (1) opportunità da seguire e loro stati, (2) valutazione documentata dell'ammissibilità, (3) scadenziario operativo in **vista separata**, (4) spiegazione motivata del punteggio, (5) indicatori discreti Nuova/Aggiornata, (6) scheda di valutazione esportabile, (7) arricchimento dei dati (beneficiari, importi, scadenze, bandi a sportello e documenti). Gli stati e le note private dei volontari non devono essere pubblicati nei JSON aperti; una futura area collaborativa richiederà autenticazione e storage riservato.

### Provenienza e limiti dell'estrazione

Il modulo `src/evidence.py` estrae dai siti ufficiali soltanto dati associati a etichette riconoscibili. Si distinguono `amount` (valore non verificato), `amount_kind` (es. dotazione complessiva contro contributo massimo), `amount_source`, `beneficiaries_excerpt` e `beneficiaries_source`; una possibile procedura `a sportello` produce soltanto `rolling_guidance` e `rolling_guidance_source`, **non** un'apertura confermata né una scadenza inventata. Le informazioni incomplete non comportano esclusione. L'ammissibilità richiede sempre lettura delle condizioni ufficiali.

### Pubblicazione frontend

**Unico publisher autorizzato:** workflow `Pubblica interfaccia Opera+ Funding via SFTP` nella repository `jeckodevelopment/jeckodevsite` (`.github/workflows/publish-opera-funding.yml`), mediante `scripts/deploy_opera_funding.py`. Utilizza le credenziali SFTP già presenti in `jeckodevsite`, verifica gli asset pubblici via HTTPS e gestisce il rollback. Non creare workflow SFTP in `opera-funding`. La pubblicazione si avvia tramite la richiesta versionata `deploy-requests/opera-funding.txt` in `jeckodevsite` oppure manualmente via `workflow_dispatch` sull'unico publisher.

### Motivazioni dell'adeguatezza basate sulle evidenze

In `src/fit.py` la motivazione tematica usa il titolo e, se la scheda è stata effettivamente ispezionata, anche il riepilogo e i beneficiari estratti. `score_explanation_basis` distingue le due casistiche; nella finestra dettaglio vengono mostrati motivazione e livello di attendibilità. **Il punteggio numerico non viene ricalcolato**: è un indicatore storico di scoperta basato sul titolo e non rappresenta una percentuale di ammissibilità o probabilità di ottenere fondi. L'analisi non sopprime opportunità; aggiunge verifiche mirate per dotazioni complessive e procedure a sportello. Le nuove motivazioni saranno ricalcolate dal prossimo ciclo di scansione. Le richieste di deploy passano unicamente per `jeckodevsite`.

### Segnalazione discreta delle novità nel catalogo

Il motore `src/catalog_changes.py` salva per ciascuna opportunità una **impronta dei soli dati sostanziali** (titolo, ente, tipologia, date, importo, beneficiari, riepilogo e documenti). A differenza di `last_seen`, i controlli tecnici, i cambiamenti del punteggio e lo stato che evolve col passare del tempo non generano «Aggiornata». Alla prima scansione dopo l'introduzione del sistema viene costruita una **baseline silenziosa**, per non segnalare retroattivamente come nuove tutte le schede. In seguito ogni nuova opportunità riceve `catalog_new_at`; le modifiche dei dati sostanziali impostano `catalog_updated_at`. I tag discreti *Nuova*/*Aggiornata* compaiono sulle schede e nel dettaglio per sette giorni (precedenza a *Nuova*). Le informazioni non causano esclusioni, variazioni del ranking, email o modifiche allo stato di apertura. La scansione ordinaria gestisce l'aggiornamento dei metadati; il frontend è distribuito soltanto con il publisher di `jeckodevsite`.
