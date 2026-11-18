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

### Esportazione della scheda di valutazione (PDF)

Nella finestra **Esamina opportunità** è disponibile **Esporta scheda PDF**: apre la funzione di stampa del browser con una scheda **A4 dedicata alla singola opportunità**, senza stampare dashboard, menu o altre schede. In Chrome, Firefox, Edge o Safari selezionare **Salva come PDF** (o equivalente) come destinazione: il file viene creato dal browser, senza inviare dati a servizi esterni. Questa prima versione usa il sistema di stampa nativo per non introdurre librerie terze, font privati, backend o dipendenze. La stampa non produce automaticamente un download: il salvataggio PDF va selezionato nella finestra del browser.

La scheda contiene logo Opera+, titolo, ente, stato, data di generazione, scadenza/apertura, importo e natura dell'importo, tipologia, punteggio tematico, ammissibilità, livello di affidabilità, motivazioni, beneficiari, possibili procedure a sportello, verifiche richieste, dati mancanti, spunti progettuali e URL ufficiali completi. I campi non disponibili sono dichiarati come tali; non vengono inventati. Il contenuto è costruito come testo sicuro (nessun HTML esterno interpretato), con collegamenti consentiti soltanto via HTTPS, deduplicati. I dati possono cambiare: il PDF è una fotografia del catalogo alla data di generazione, **non un'attestazione di ammissibilità**. Il pulsante non cambia stato, ranking, informazioni pubbliche o notifiche email. In fase di stampa la finestra dell'opportunità viene chiusa per garantire la resa A4, senza perdere i filtri.

### Pagine autonome e URL condivisibili delle opportunità

La dashboard resta la vista principale all'indirizzo `/dev/funding/`. Il collegamento **Esamina opportunità** ora apre una pagina autonoma nella stessa applicazione statica, invece di un popup: `/dev/funding/?opportunity=<ID-codificato>`. L'ID è quello stabile del catalogo, compresi i record che distinguono finestre di candidatura; non si deducono URL da titoli, che possono cambiare. L'URL è copiabile dalla barra degli indirizzi o con **Copia link della scheda** e può essere aperto direttamente da email e messaggi. Il pulsante **Torna al catalogo**, i comandi Indietro/Avanti del browser e il refresh mantengono la navigazione. Un ID non più presente mostra un messaggio esplicito e offre il ritorno al catalogo. La pagina mantiene i dettagli, le evidenze, i documenti e l'esportazione della scheda PDF.

La scelta di un parametro query consente il **deep linking su hosting statico**, senza rewrite del server o creazione di centinaia di file HTML. Non è ancora una pagina HTML separata indicizzabile con metadati social specifici (OG): tale funzione richiederebbe generazione statica delle pagine o supporto lato server. Non viene introdotto un backend, un sistema di registrazione o nuovi criteri che eliminino opportunità. La futura funzione *Opportunità da seguire* potrà conservare il medesimo ID per ogni scheda.

### Opportunità da seguire — primo livello personale

Il pulsante **Segui opportunità** è disponibile sulle schede del catalogo e nelle pagine autonome, con l'indicazione del salvataggio. La nuova scheda **Da seguire** mostra soltanto le opportunità contrassegnate; gli altri filtri rimangono disponibili. Il salvataggio di soli ID è effettuato in `localStorage` del browser (`opera-funding-watchlist-v1`); non vengono raccolti nomi, email o note, né inviati dati a terzi. **Non è una lista condivisa**: cambia fra dispositivi o browser, può essere cancellata dalla pulizia dei dati del sito e potrebbe non sopravvivere alla modalità privata. Per una vera gestione di volontari, ruoli, stati e note serviranno autenticazione e backend con dati riservati; NON mettere questi dati nel catalogo JSON pubblico. Il badge e il filtro non eliminano opportunità, non alterano punteggi, stato, scansioni o notifiche email.

### Collegamenti alle opportunità

Il comando **Esamina opportunità** usa un normale link HTML verso l'URL condivisibile della scheda, con aspetto grafico di pulsante coerente con **Segui opportunità**. La navigazione nativa del browser (anche da tastiera, in nuova scheda e dopo un ricaricamento) evita la dipendenza da intercettazioni JavaScript del click. La dashboard mantiene il catalogo completo e non cambia il tracciamento delle opportunità.

### Avvio, cache e aggiornamento dati — correzione novembre 2026

Il frontend carica il feed GitHub con un limite massimo di attesa per evitare che il catalogo resti indefinitamente su “Caricamento…”. Se il feed remoto non risponde entro il limite, prova la copia locale predisposta dal publisher; se entrambe le richieste falliscono mostra un errore esplicito anziché lasciare una schermata in attesa. Il caricamento protegge anche da risposte di richieste obsolete. La pagina HTML include una versione esplicita nelle URL degli asset `app.js` e `styles.css` per aggirare le copie vecchie della cache dopo il deploy.

La scansione automatica resta programmata lunedì, mercoledì e venerdì alle **06:00 UTC**; il deploy del frontend è indipendente dalla scansione e non sostituisce l'aggiornamento del catalogo. In caso di esecuzione pianificata mancata, controllare il workflow *Scan funding sources* su GitHub Actions. Il workflow include anche le modifiche ai moduli `src/evidence.py` e `src/catalog_changes.py` fra gli eventi che richiedono una nuova scansione. Il publisher rimane esclusivamente quello di `jeckodevsite`.

### ID numerici permanenti e titoli cliccabili

Ogni record ha due identificativi distinti: `id` (URL della fonte, usato dai crawler e dalla watchlist locale) e `public_id` (numero intero permanente per i link condivisibili). `src/public_ids.py` assegna nuovi numeri progressivi dalla mappa append-only `data/opportunity-ids.json`, registrata **nello stesso commit** della scansione. Gli ID non dipendono da titolo, posizione o punteggio e non vengono riutilizzati dopo la scomparsa di una scheda. Un link ha il formato `/dev/funding/?opportunity=143`; il titolo nella card è cliccabile, così come il pulsante *Esamina opportunità*. I vecchi collegamenti con URL codificato continuano a funzionare e vengono normalizzati verso il numero permanente dopo l'apertura. Il numero 143 è illustrativo: il valore effettivo viene assegnato dal registro.

### Aggiornamento su smartphone

La directory pubblicata `/dev/funding/` dispone di regole `.htaccess` con `Cache-Control: no-store` per HTML, JS, CSS e copia JSON; il publisher di `jeckodevsite` genera inoltre versioni degli asset basate sul contenuto ad **ogni deploy**. Il rinnovo deve funzionare con il normale caricamento della pagina anche su iPhone/Android, senza richiedere Ctrl+F5 o pulizia manuale della cache. La frequenza delle nuove informazioni dipende invece dalla scansione programmata delle fonti: il deploy e la scansione sono due operazioni distinte. Le regole di caching valgono per l'hosting Apache/LiteSpeed che onora `.htaccess`; la pipeline deve verificare l'HTTPS dei file pubblicati.

### Valutazione editoriale per tutte le opportunità (novembre 2026)

Il catalogo **non elimina nessuna scheda** perché mancano data, beneficiari o ammissibilità. Durante ogni scansione `src/fit.py` produce, per tutti i record, `assessment_label` (Alta affinità, Media affinità, Bassa affinità, Informativa), `assessment_reason`, `assessment_basis` e una nota sulla distinzione fra **pertinenza** e **apertura ufficialmente verificata**. Il giudizio è deterministico e preliminare, ricavato dal punteggio tematico di scoperta e dalla tipologia del record. Non certifica l'ammissibilità, non prevede la probabilità di finanziamento e non inferisce aperture non documentate. L'interfaccia sostituisce la vecchia tab generica *Da approfondire* con **Potenziali**, indicando chiaramente in ogni scheda la valutazione assegnata e, quando necessario, **Apertura non confermata**. Le schede informative restano consultabili in *Altri contenuti* e *Tutti*. I campi della valutazione compaiono anche nelle schede PDF. Le nuove valutazioni vengono popolate al successivo scan.

### Scheda operativa personale — prima evoluzione di «Da seguire»

Ogni pagina autonoma consente di compilare **Stato di lavorazione**, **Responsabile**, **Prossima attività**, **Scadenza interna** e **Note**. Stati: Da valutare, Interessante, Candidatura in preparazione, Presentata, Non pertinente. Il salvataggio aggiunge la scheda a *Da seguire* e persiste solo nel browser, accanto alla lista dei preferiti preesistente (migrazione compatibile: gli ID della lista rimangono invariati). I dati **non sono condivisi fra utenti o dispositivi**, non vengono inseriti nel JSON pubblico e non devono essere considerati affidabili come registro associativo comune; la pulizia dei dati browser può eliminarli. Rimuovere una scheda da *Da seguire* cancella anche la lavorazione locale di quella scheda. La futura area condivisa richiede autenticazione, ruoli, database e controlli di riservatezza. Le scadenze interne non sono ancora uno scadenziario e non producono promemoria automatici.

#### Continuità dei link numerici durante la riconciliazione

Se un aggregatore ripubblica un bando con una URL diversa oppure la scheda sindacata viene ricondotta a un bando ufficiale, il vecchio `public_id` rimane riservato. Quando il motore di riconciliazione ha già dimostrato l'equivalenza tramite `alternative_urls`, `src/public_ids.py` produce `public_id_aliases`; il router risolve il vecchio numero e mostra la scheda canonica, normalizzando poi l'indirizzo. Non vengono create equivalenze sulla base della sola somiglianza del titolo e nessun ID viene riutilizzato. Questo preserva i collegamenti condivisi durante l'evoluzione del catalogo.

### Valutazione basata sulle informazioni del bando (novembre 2026)

La valutazione non utilizza più il punteggio del solo titolo quando sono disponibili evidenze sostanziali. Il parser HTML cerca nella pagina ufficiale fino a quattro brevi estratti specifici: **finalità del programma**, **attività finanziabili**, **beneficiari** e **requisiti/partenariato**. Sono conservati in campi distinti con URL di origine; il sistema può usare anche una sintesi già presente, se raccolta da una fonte consultata. Il giudizio classifica l'affinità sulla corrispondenza dei contenuti, senza attribuire ammissibilità o probabilità di successo. Un titolo molto pertinente non può più prevalere su attività finanziabili che non hanno attinenza col progetto.

I campi `assessment_basis`, `assessment_confidence`, `assessment_gaps`, `assessment_source` e `assessment_reason` espongono le prove usate e le lacune. Se le evidenze mancano, ogni opportunità mantiene **un giudizio esplicitamente provvisorio**, accompagnato dalla dicitura «basata soltanto sul titolo» e affidabilità bassa: non viene spacciato per analisi completa. Le pagine non vengono eliminate per mancanza di dati; «Da approfondire» non torna come categoria della dashboard. Il parser può leggere estratti testuali da un massimo di due PDF ufficiali per scheda (5 MB, 16 pagine ciascuno), senza conservarne il testo integrale. Non è previsto OCR per PDF scansiti, né accesso a documenti protetti o siti che vietano la lettura automatica: gli allegati non leggibili rimangono una lacuna esplicita. Il nuovo schema obbliga il motore a riesaminare progressivamente le pagine HTML, rispettando la quota di lettura per fonte durante ogni scansione.


### Revisione documentale del catalogo — 18 novembre 2026

La revisione di merito distingue le valutazioni generate automaticamente dalle **valutazioni individuali documentate**. Queste ultime sono in `config/assessment_reviews.json` e conservano motivazioni collegate a finalità, attività finanziabili, beneficiari e requisiti, con riferimento alla pagina ufficiale e data della lettura. Il modulo `src/assessment_reviews.py` le riapplica dopo ogni scansione, prima di salvare il catalogo, senza alterare l'apertura ufficiale. L'aggiornamento iniziale copre le schede 190 (Festival partecipativi), 33 (residenze culturali), 32 (mobilità individuale) e 18 (Aiuti allo spettacolo dal vivo). Nessun'altra scheda va descritta come «verificata documentalmente» per effetto del solo punteggio tematico. Le valutazioni hanno carattere preliminare finché le condizioni dell'intero bando e gli allegati applicabili non siano stati confrontati con i requisiti effettivi dell'associazione.

La coda di lettura comprende anche la tipologia `non classificato`: il fatto che la denominazione non contenga esplicitamente la parola «bando» non esclude che si tratti di una call reale. La copertura documentale deve crescere tramite scansioni successive, senza far passare automaticamente tutte le schede per revisionate.

