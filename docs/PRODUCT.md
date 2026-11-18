# Specifica MVP — Opera+ Funding

## Obiettivo
Individuare e mostrare opportunità di finanziamento per Opera+ anche quando richiedono partnership o nuovi progetti ad hoc.

## Regole di prodotto
- La pertinenza (0–100) e l'ammissibilità sono **separate**; un requisito mancante non elimina né declassa automaticamente un bando.
- Ammissibilità iniziale: `da verificare`; non dedurre idoneità da parole chiave.
- Non fabbricare scadenze, importi, beneficiari, PDF o stati aperto/chiuso; campo `null` se sconosciuto.
- Conservare link a pagine ufficiali, documenti, FAQ e allegati, non copie dei documenti.
- Registrare la fonte, la data di rilevazione e il controllo più recente.
- La scansione delle pagine indice è **discovery**, non verifica completa delle condizioni; rendere visibile la distinzione.
- Tenere lo storico delle opportunità già viste; non cancellare automaticamente una scheda solo perché scompare dalla pagina indice.
- Rendere espliciti errori delle fonti e ultimo esito di scansione.
- Non inserire dati personali o candidature private nel repository pubblico.

## Classificazione preliminare v2 (16 novembre 2026)
- Il **punteggio di pertinenza** rimane tematico (da titolo indice), non misura probabilità di aggiudicazione e non determina ammissibilità.
- **Tipologia** separata: finanziamento potenziale, call progettuale da verificare, altro avviso, non classificato. Gli avvisi di selezione del personale, incarichi e appalti restano visibili nello storico e possono essere filtrati; non vengono conteggiati automaticamente come finanziamenti verificati.
- **Stato**: aperto (fonte indice), chiuso, non verificato. Lo stato esplicito si estrae soltanto se presente accanto a metadati di pubblicazione/scadenza; una scadenza precedente alla data corrente segnala "chiuso".
- **Scadenza** valorizzata solamente se preceduta da un'etichetta esplicita "Scadenza"; le date di pubblicazione non sono scadenze.
- La classificazione resta preliminare: gli indici possono essere obsoleti, incompleti o con titoli troncati. Le schede non sono ancora validate sui PDF/FAQ del singolo bando.
- Nessun elemento è nascosto per ammissibilità non soddisfatta o per data trascorsa. La dashboard consente di filtrarli.
- Lo storico rimane anche se un link scompare dalle pagine indice. La prossima scansione aggiorna i dati dei link ancora rilevati.

## Prossimi incrementi
1. Verifica manuale e ampliamento del registro delle fonti, con connettori specifici per portali dinamici/API.
2. Estrazione affidabile di scadenza, importo e requisiti da pagine dettaglio e documenti ufficiali.
3. Classificazione approfondita e spiegabile; valutazione ammissibilità e potenziale progetto ad hoc.
4. Filtri completi, storico e notifiche email.
5. Pubblicazione tramite jeckodevsite già integrata, da monitorare.

## Enrichment HTML e identità grafica (novembre 2026)
- Su un massimo iniziale di tre opportunità per fonte e scansione, il motore può visitare schede HTML della stessa origine, rispettando robots.txt e imponendo timeout e limite dimensionale. Non segue documenti PDF e non archivia copie di pagine o documenti.
- Dalle schede vengono estratte solo scadenze esplicite, importi indicativi etichettati e collegamenti a bando, FAQ e allegati. I dati estratti non equivalgono a una verifica legale del bando; le altre informazioni rimangono da verificare.
- Le fonti esterne agli aggregatori e i portali dinamici richiedono connettori dedicati. Conservare sempre visibili le opportunità non arricchite.
- La grafica richiama il template Opera+ in `jeckodevelopment/tpl_operaplus`: dark `#101419`, pannelli `#1b2228`, oro `#c7a676` e serif Georgia. Il wordmark testuale Opera+ replica il fallback del template; per utilizzare l'immagine grafica ufficiale occorre acquisire il relativo asset pubblicabile e aggiornare whitelist del publisher.

## Affidabilità link, stati e beneficiari (novembre 2026)
- Il link primario viene verificato progressivamente con richieste HTTPS senza scaricare file; 404/410 sono marcati **non disponibile** e la dashboard mostra come alternativa l'indice dell'ente. Errori di rete o 403 non equivalgono a link inesistente. Al massimo otto nuovi link per fonte/scansione; la copertura non è istantanea.
- Ogni scansione ricalcola lo stato dei bandi storici: una scadenza trascorsa prevale sulle etichette «aperto» dell'indice. Una dicitura «aperto» senza scadenza affidabile resta «non verificato», mai candidatura confermata.
- Estrazione di un breve **estratto dei beneficiari** esclusivamente quando una scheda HTML ha un'etichetta esplicita. Non equivale a verifica dell'ammissibilità.
- Il logo ufficiale è caricato dall'asset pubblico https://opera.plus/assets/operaplus-logo.png indicato dall'associazione, senza duplicare il file nel repository; serve accessibilità del dominio esterno.
- La dashboard conserva bandi non verificati, chiusi e con requisiti mancanti; il link diretto non viene mostrato se la fonte risponde esplicitamente 404/410.

## Dashboard UX compatta (novembre 2026)
- Intestazione ridotta: logo grafico Opera+ contenuto rigidamente in 104×38 px su desktop e 80×30 px su smartphone. Titolo semplice e descrizione breve, senza spazio verticale eccessivo.
- Riepilogo compatto, filtri su due righe (una su desktop ampio), ricerca sempre visibile, pulsante per ripristinarli, ordinamento per priorità/pertinenza, scadenza o rilevazione.
- Per facilitare l'uso quotidiano, la vista iniziale mostra le opportunità non segnalate come chiuse: gli avvisi chiusi restano disponibili tramite filtro “Tutti, anche chiusi”. **Nessuna esclusione per requisiti di ammissibilità**.
- Solo 20 risultati inizialmente, con “Mostra altri risultati”; scheda riassuntiva con titolo, ente, stato, scadenza, tipologia e punteggio. I dettagli secondari, collegamenti documentali, beneficiari ed evidenze sono espandibili.
- Gli stati con data trascorsa sono calcolati anche nel browser, per evitare badge “aperto” non aggiornati prima della successiva scansione.
- Compatibilità con schema dati esistente e collegamenti esterni con protocollo HTTPS.

## UX operativa, stati affidabili e PDF (16 novembre 2026)
- **Vista iniziale:** solo finanziamenti potenziali e call progettuali, escludendo soltanto lo storico chiuso. Per vedere selezioni/appalti, usare "Tutte, inclusi altri avvisi". Tutte le opportunità possono essere ritrovate con i filtri.
- **Ordinamento iniziale:** APERTO per scadenza crescente; poi DA VERIFICARE per pertinenza decrescente; poi IN ARRIVO per data di apertura, se confermata. CHIUSO solo con filtro apposito o "Tutti, anche chiusi". Le altre opzioni di ordinamento sono esplicite.
- **Stati in maiuscolo:** APERTO, DA VERIFICARE, IN ARRIVO, CHIUSO. Una scadenza passata o una chiusura esplicita prevalgono sempre.
- **Condizione APERTO:** l'indice deve confermare l'apertura, il link deve essere raggiungibile e deve esistere una scadenza futura oppure un bando a sportello esplicitamente verificato. La sola data futura non basta, e un punteggio di pertinenza alto non certifica la candidabilità.
- **DA VERIFICARE** significa informazioni incomplete sullo stato della call, non inidoneità dell'associazione. La suitability/pertinenza resta separata dai requisiti obbligatori; non nascondere opportunità per partner o requisiti mancanti.
- **Scadenze:** se non rilevate nell'HTML, il motore può leggere un PDF ufficiale dello stesso dominio (un documento per scheda, max 2 MB e prime 8 pagine testuali). Le date vengono estratte solo da etichette esplicite, con URL di origine e timestamp. Nessuna copia del documento viene persistita.
- PDF scansiti o senza testo estraibile richiederanno connettori/analisi specifici; **una data non trovata rimane mancante** e lo stato non viene inventato.
- Il default mostra solo call/finanziamenti e una metrica delle opportunità confermate APERTE. La fonte della scadenza è disponibile nei dettagli della scheda.

## Suitability spiegabile (16 novembre 2026)
- La classificazione produce motivazioni di pertinenza e alcune **possibili** idee progettuali per Opera+ coerenti con il titolo della call; non sono condizioni ufficiali del bando e non sostituiscono la lettura della documentazione.
- Il punteggio originale `relevance` resta invariato per non attribuire precisione a informazioni mancanti. È esplicitamente contrassegnato come **preliminare / confidenza bassa** finché non saranno disponibili requisiti e importi verificati.
- Controlli candidabilità: natura giuridica dei beneficiari, eventuale partenariato, cofinanziamenti e vincoli. La presenza della parola «partner» attiva un invito alla verifica, **non una dichiarazione** che sia obbligatorio.
- I requisiti mancanti non occultano né penalizzano automaticamente l'opportunità. Lo stato di apertura della call resta indipendente dalla suitability e dall'idoneità dell'associazione.

## Revisione UX ad alto contrasto (novembre 2026)
- **Tema chiaro caldo:** sfondo avorio tenue, schede bianche e testo scuro, mantenendo il richiamo all'identità Opera+ (logo ufficiale compatto, serif nei titoli e accento oro). Il logo ufficiale conserva un piccolo supporto scuro per garantirne il contrasto.
- **Stati immediatamente leggibili:** badge APERTO verde scuro su verde pallido, DA VERIFICARE ambra su crema, IN ARRIVO blu su azzurro pallido, CHIUSO grigio su grigio chiaro. Il testo dello stato è sempre visibile e non dipende solo dal colore.
- **Navigazione rapida:** pulsanti di filtro in primo piano per “In evidenza”, APERTO, DA VERIFICARE, IN ARRIVO, CHIUSO e Tutti; stato attivo evidente tramite colore e `aria-pressed`. La ricerca e gli altri filtri restano nella stessa sezione.
- **Schede operative:** badge di stato e scadenza **prima** del titolo, ente subito dopo, pertinenza in secondo piano e link alla fonte immediato; requisiti, documenti e idee progettuali nei dettagli espandibili.
- **Regole invarianti:** nessun bando chiuso nella vista iniziale; APERTO richiede evidenze, ordinamento per scadenza; da verificare subito dopo; storico accessibile con un clic. Nessuna esclusione automatica per requisiti di ammissibilità.
- **Accessibilità e responsività:** controlli ben distinguibili, focus visibile, testo scuro ad alto contrasto, impaginazione adattiva mobile, test automatici su badge, filtri e date.

## Verifiche effettive e recupero delle opportunità aperte (16/11/2026)
- La scansione iniziale di 150 link produceva zero schede APERTO: era una carenza del parsing e della verifica, non una prova dell'assenza di bandi aperti.
- Nuovo parser per schede strutturate con etichette **Stato**, **Domande dal**, **Scadenza**, inclusi i prefissi dei giorni della settimana. Conserva provenienza e data, senza confondere la scadenza con la pubblicazione.
- Per le fonti ad alta priorità, le schede candidabili sono analizzate prima delle notizie e degli archivi; fino a sei schede per fonte per ciclo, con limitazione delle richieste.
- File `config/priority_pages.json`: elenco limitato di pagine ufficiali particolarmente importanti, controllate **a ogni scansione** e non solo quando compaiono in cima all'indice. L'inclusione non pre-certifica il bando; lo stato APERTO viene creato soltanto dalla pagina raggiunta con finestra verificata.
- Prima pagina prioritaria: Regione Piemonte, contributi per comunicazione e promozione di manifestazioni nel 2026, con scadenza riportata ufficialmente al 24/11/2026. Ammissibilità dell'associazione da valutare sui requisiti del bando.
- La tipologia “call progettuale” viene mostrata separatamente dallo stato “DA VERIFICARE”. I link già confermati 404/410 non sono mostrati nell'elenco predefinito, ma restano nello storico con avviso.
- I bandi con data o stato non reperibile rimangono DA VERIFICARE. Non vengono creati dati fittizi per rendere i numeri più rassicuranti.
- Priorità successiva: adapter specifici per portali europei e aggregatori, verifica automatica dei PDF complessi e campo 'suitability' fondato sui requisiti completi.

## Rianalisi periodica delle schede (16 novembre 2026)
- Il flag `detail_checked` **non** rende il controllo definitivo: l'analisi delle pagine ufficiali è versionata con `detail_version` e datata con `detail_checked_at`.
- Quando il parser cambia versione, la prossima scansione riprocessa progressivamente le schede già viste. Dopo tre giorni una scheda viene nuovamente candidata alla verifica, per individuare proroghe e cambiamenti.
- La rianalisi avviene per piccoli lotti e privilegia i bandi progettuali; può quindi richiedere più esecuzioni per completare il backlog. Le pagine esplicitamente prioritarie continuano a essere ricontrollate ogni volta.
- Il risultato del controllo non equivale alla conferma dell'ammissibilità di Opera+. Stato APERTO e scadenza richiedono evidenze ufficiali; se mancano, rimane DA VERIFICARE.

## Copertura delle verifiche, non solo numero di link (novembre 2026)
- Lo scanner utilizza una **coda di revisione equa** per ogni fonte: prima le opportunità progettuali non chiuse, poi le altre. Fra quelle da controllare dà precedenza alle schede mai tentate e a quelle controllate da più tempo, evitando di analizzare sempre gli stessi primi risultati.
- Ogni tentativo di analisi registra `detail_attempted_at`, anche se il portale impedisce l'accesso. La lettura effettivamente riuscita continua ad avere `detail_checked_at` e `detail_version`. Una nuova versione del parser o un controllo più vecchio di tre giorni rende la scheda ricandidabile.
- Rimangono limiti moderati per fonte (6 schede ad alta priorità o 3 per le altre per scansione); il backlog si smaltisce progressivamente senza sovraccaricare gli enti. Le pagine curate in `priority_pages.json` continuano a essere controllate a ogni esecuzione.
- `data/scan-status.json` ora include `coverage` con totali e conteggi per fonte: APERTO, CHIUSO, IN ARRIVO, DA VERIFICARE, scadenze note, scadenze con URL di provenienza, schede lette e link raggiungibili. **Il numero di elementi indicizzati non equivale al numero di bandi verificati.**
- Il riepilogo è un'evidenza operativa per guidare l'aggiunta di adattatori specifici alle fonti che rimangono opache. Un cambio nel report non attesta automaticamente che Opera+ sia ammessa a candidarsi.

## Presentazione associativa e salute delle fonti (novembre 2026)
- La homepage mostra di default solo opportunità APERTE o IN ARRIVO con evidenza ufficiale. Altre opportunità con stato non confermato restano consultabili dal filtro “Altre opportunità”; le chiuse dallo storico. Il sistema non etichetta APERTO un bando privo di prova.
- Nelle schede vengono mostrate soltanto informazioni utili alla scelta: ente, titolo, stato confermato, data quando disponibile, contributo quando disponibile, beneficiari, possibili idee e collegamenti a fonte/documenti. Sono rimossi motivazioni tecniche, checklist standard e messaggi ripetitivi.
- Indicatore nell'intestazione: VERDE con 0 fonti fallite; GIALLO con 1–2 fonti fallite e quota inferiore al 25%; ROSSO se almeno 3 fonti fallite o quota almeno 25%, o report delle fonti mancante. Indica salute dell'accesso alle fonti, non automaticamente completezza/qualità delle singole schede.
- A fondo pagina elenco delle anomalie, con nome fonte, motivo del fallimento e link alla pagina ufficiale quando disponibile. Il registro delle 13 fonti è **approvato** dall'associazione: non significa che tutte le opportunità siano già state validate o che un sito sia sempre raggiungibile.

## Qualità delle letture e risultati vuoti
- Una fonte con pagina raggiungibile ma zero opportunità individuate riceve `warning` nel report: è una **copertura non accertata**, non equivale a un errore HTTP e non significa necessariamente assenza di bandi.
- L'indicatore verde richiede zero errori e zero avvisi; giallo da una a poche anomalie, rosso con almeno tre fonti fallite o quattro fonti problematiche, oppure almeno il 25% delle fonti. La lista a fondo pagina distingue la ragione: fonte irraggiungibile, blocco robots.txt, oppure nessuna opportunità riconosciuta.
- Questa soglia segnala la qualità della raccolta, non la candidabilità di Opera+ né garantisce che tutti i bandi della fonte siano stati acquisiti.

## Scadenze per più finestre di candidatura (Festival partecipativi 2027)
- La pagina ufficiale Compagnia di San Paolo prevede una prima finestra al **03/12/2026** (festival da aprile ad agosto 2027) e una seconda al **05/04/2027** (festival da settembre 2027 a marzo 2028).
- Il parser legge dinamicamente entrambe le date dalle frasi di candidatura della pagina e imposta in `deadline` quella futura più vicina, conservando `application_windows` con entrambe. Le date non vengono precaricate come informazioni statiche.
- La dashboard visualizza le finestre complete nel dettaglio e ricorda che la data applicabile dipende dal periodo del festival. Questo evita di far perdere la prima scadenza ordinando soltanto per il termine generale.

## Dashboard operativa — interfaccia attuale (novembre 2026)

Questa sezione descrive la **UI corrente**, sostituendo le indicazioni grafiche precedenti (tema scuro, KPI grandi e filtri a sei colonne) che rimangono solo come cronologia delle iterazioni.

- **Logo:** usa la variante nera e oro fornita da Opera+, con trasparenza ritagliata, ottimizzata e conservata localmente in `web/assets/operaplus-logo.png`. Niente dipendenza da un'immagine esterna.
- **Stile:** sfondo chiaro avorio, schede bianche, titoli editoriali serif, dettagli neri/grigi e oro come accento. Contrasto esplicito degli stati. Desktop e smartphone sono entrambi supportati.
- **Vista iniziale:** candidature APERTE supportate da evidenze ufficiali. Schede da approfondire e storico CHIUSO sono accessibili tramite tab, ma non confusi con i bandi candidabili.
- **Scheda:** stato e ente immediati; titolo e **sintesi di massimo due righe**; fonte primaria; calendario laterale con giorno, mese e anno; affinità numerica e barra visuale; dettagli espandibili solo per contributo, destinatari, finestre multiple e documenti. Nessuna checklist tecnica o commento ripetitivo nella scheda.
- **Sintesi:** preferisce la descrizione HTML ufficiale della scheda quando disponibile; altrimenti una frase prudente basata esclusivamente sulla tipologia e sui temi già rilevati. Le descrizioni non sono inventate come condizioni di finanziamento.
- **Ordinamento:** due controlli in vista, **Scadenza** crescente (default) e **Punteggio** decrescente. Con i filtri multi-stato, il sistema mantiene prima APERTO, poi IN ARRIVO, poi gli altri e infine CHIUSO; all'interno di ogni gruppo applica la scelta. Affinità non equivale ad ammissibilità.
- **Semaforo tecnico:** verde se tutte le fonti sono state elaborate senza errori, giallo se poche fonti falliscono, rosso quando almeno tre falliscono o almeno il 25% è in errore, o se il report manca. **Zero opportunità trovate non è un errore tecnico**: non cambia il colore. A fondo pagina si elencano solo gli errori effettivi d'accesso/elaborazione.
- **Aggiornamento:** opportunità e report arrivano dai JSON pubblici GitHub con fallback locale e pulsante manuale. Il publisher di `jeckodevsite` carica a richiesta HTML, JS, CSS, PNG del logo e un'istantanea JSON di riserva; non ha bisogno di cron SFTP.
- **Schema dati:** il parser ufficiale registra anche `summary` quando la pagina fornisce una descrizione adatta, con `detail_version=3` per rianalizzare progressivamente le schede esistenti.

## Edizioni annuali, finestre e dettagli operativi (novembre 2026)

### Bando CRT Ordinarie: una scheda per ciascuna scadenza
La fonte ufficiale `https://www.fondazionecrt.it/bandi-progetti/arte-cultura-ordinarie/` presenta **tre finestre effettive nell'edizione 2026**, da non accorpare in un unico termine:

| Candidatura | Apertura | Scadenza |
| --- | --- | --- |
| Progetto, prima scadenza | 02/02/2026 | 30/04/2026 ore 15:00 |
| Progetto, seconda scadenza | 01/07/2026 | 15/10/2026 ore 15:00 |
| Sostegno attività, unica scadenza | 02/02/2026 | 04/03/2026 ore 15:00 |

Sono tutte **scadute al 16/11/2026**; sono visibili tramite lo storico CHIUSO, non spacciate per candidature attive. L'URL ufficiale resta invariato, ma ogni riga ha un `id` stabile formato da URL base, anno, tipologia, finestra e data di chiusura. Le nuove edizioni creano nuove righe senza modificare le precedenti. Il crawler le estrae dalla pagina a ogni scansione, non da valori fissati nel codice; nessuna finestra viene inventata.

Il sito ufficiale chiarisce inoltre che **spettacolo dal vivo** deve essere candidato a NoteSipari o Orizzonti L.I.V.E. e non a Ordinarie. Questa distinzione è rilevante per Opera+ quando si valutano progetti lirici, di formazione, comunicazione culturale e videolezioni.

### Interfaccia
- Il calendario laterale resta la prima indicazione della scadenza. Le schede usano un indicatore **Adeguatezza per Opera+** a tutta larghezza in fondo, con sfumatura tenue da rosso ad ambra a verde, valore numerico 0–100 e cursore accessibile. Si tratta dell'attuale punteggio preliminare di pertinenza; non è una prova dell'ammissibilità.
- Un pulsante **Esamina opportunità** apre un `<dialog>` nativo modale e navigabile da tastiera, richiudibile con pulsante, Escape o clic sullo sfondo. Include descrizione, stato, ente, date di apertura e scadenza, tipologia, edizione, finestra di candidatura, importo/dotazione se noto, beneficiari se disponibili, documenti ufficiali e spunti progettuali (distinti dai requisiti del bando).
- Nessun importo, massimale, beneficiario o condizione viene inventato se la fonte non lo comunica; i campi mancanti sono segnalati in modo sobrio.
- Il logo nell'intestazione è nuovamente derivato dal PNG originale allegato: ritaglio dell'area visibile, trasparenza conservata e immagine locale verificata. Il percorso del publisher SFTP resta `web/assets/operaplus-logo.png`, senza nuove dipendenze esterne.

### Indicazioni progettuali per CRT Ordinarie
La scheda di dettaglio mostra ora suggerimenti separati per «Progetto» e «Sostegno attività», progettati intorno alla divulgazione lirica, all'educazione extrascolastica e alle videolezioni di Opera+. Questi sono **spunti editoriali, non condizioni ufficiali né valutazioni definitive di ammissibilità**. Il dialogo rende visibile l'esclusione dello spettacolo dal vivo da Ordinarie, sulla base della pagina ufficiale CRT, con rinvio ai bandi specifici NoteSipari e Orizzonti L.I.V.E.

## Verifica di scadenze da documenti ufficiali e qualità del catalogo (novembre 2026)

- Le etichette visibili sono riferite alla **opportunità**: **APERTA**, **SCADUTA**, **IN ARRIVO** e **STATO NON CONFERMATO**. I tab diventano «Aperte» e «Scadute». Gli stati tecnici interni `APERTO`/`CHIUSO` rimangono invariati per compatibilità dei dati e dei report.
- La baseline del dataset al 16/11/2026 è 215 elementi, 127 senza stato accertato; **125 dei 127 non hanno una scadenza censita**, ma una parte è composta da vecchie notizie o documenti, non da bandi attivi. Non bisogna interpretare tutti i record come candidature.
- Il lettore di allegati PDF ora tenta fino a **3 PDF ufficiali permessi**, esaminandone le prime **16 pagine** e al massimo **5 MB** per allegato, senza conservare i contenuti. Gestisce date numeriche o con mese scritto, etichette di termine/scadenza, frasi sulla presentazione delle domande e intervalli dal/al. La data di pubblicazione **non** diventa una scadenza.
- Anche gli indici che rimandano direttamente a un PDF possono produrre `deadline` e `deadline_source`. Sono ammessi soltanto URL HTTPS sul dominio della fonte o su host **esplicitamente approvati**, dopo il normale controllo robots.txt; per Vol.To è ammesso il dominio ufficiale dell'aggregatore CSVnet, `infobandi.csvnet.it`. Non vengono seguiti redirect verso host arbitrari.
- Il backlog dei bandi già importati viene ricontrollato progressivamente **anche se scomparso dall'indice corrente**, con lo stesso limite per fonte e la coda equa; non è necessario reinserire manualmente il collegamento.
- Le notizie di Fondazione CRT pubblicate fuori dalla sezione ufficiale `/bandi-progetti/` restano nell'archivio come **altro avviso**, non come potenziali finanziamenti da candidare. Non si inventa uno stato «SCADUTA» in assenza di una scadenza documentata.
- L'estrazione rimane limitata a PDF con testo accessibile, alle prime pagine ed agli allegati selezionati. Non risolve PDF scansionati senza testo, documenti Word, portali che richiedono login né calendari che prevedono più finestre non etichettate. In questi casi lo stato non viene dichiarato APERTA senza prove.

## 16 novembre 2026 — tutte le tipologie per impostazione predefinita
Il filtro Tipologia ora parte da **Tutte le tipologie**, e «Azzera filtri» ripristina tale scelta. Non sono esclusi preventivamente avvisi, call o altre categorie. Il filtro sullo **stato APERTA** resta quello approvato per la vista iniziale: non mostriamo automaticamente le opportunità scadute o prive di prova, consultabili tramite i tab dedicati. L'ordinamento rimane Scadenza crescente, con alternativa Punteggio decrescente.

## Fonti residue: parser etichettato e selezione dei bandi
La nuova estrazione `structured_facts` è limitata a tre formati **documentati nelle pagine ufficiali**:
- **CSVnet/Vol.To:** l'etichetta `SCADENZA` seguita da data italiana testuale (es. 13 novembre 2026) è riconosciuta; una data di pubblicazione non costituisce termine di candidatura.
- **ALCOTRA:** i campi `Data di apertura` e `Data di chiusura` (es. prima finestra del quarto bando, 01/07/2025–31/10/2025) producono una scadenza con URL ufficiale. I siti «Come depositare», «Progetti finanziati» e le pagine indice rimangono informazioni e non candidature.
- **Città di Torino:** gli intervalli testuali `Dal ... al ... è possibile presentare la richiesta` vengono interpretati come vere finestre di candidatura; i semplici periodi di svolgimento dei progetti non costituiscono scadenze. Le comunicazioni di concessione già avvenuta non sono nuove candidature.
- **Ministero della Cultura:** le pagine «assegnazione contributi», «consuntivi», «rendicontazione» e gli indici generici rimangono informazioni disponibili nello storico, ma non bandi a cui Opera+ possa ancora candidarsi. Le nuove opportunità, quando pubblicate, continuano a essere acquisite.

La coda assegna temporaneamente 9 verifiche per esecuzione a Vol.To, MiC, Torino e ALCOTRA, mantenendo il normale controllo robots.txt e i limiti sui PDF. Il parser dettagli è versionato a `detail_version=5` per rianalizzare progressivamente le pagine già consultate. Una fonte funzionante con nessun bando rimane verde e nessuna data viene inventata.

## 16 novembre 2026 — completamento parser Vol.To/MiC/ALCOTRA

I controlli reali sulla PR #33 hanno ridotto da 42 a 20 le possibili candidature non risolte nelle quattro fonti prioritarie, separando correttamente le pagine informative. Restavano formati testuali ufficiali non coperti, ora trattati come segue:

- **Vol.To:** `Scadenza del bando: 20 Novembre 2026` e le varianti con mese in lettere sono lette come date di presentazione, non come date di selezione dei vincitori. Le pagine generiche «Progetti Vol.To» e «Progetti di Servizio Civile» sono informazioni, non bandi.
- **MiC:** la finestra effettiva delle domande `Dalle ore 16:00 del 3 novembre 2026 fino alle ore 16:00 del 31 gennaio 2027`, presente nel bando Rievocazione Storica 2027, è acquisita solo se associata a parole `piattaforma/modulistica` e `domande/candidature`. Le date di attività di un evento non diventano deadline. Le pagine `consuntivi` e le descrizioni generiche FNSV sono tenute fuori dalle candidature.
- **ALCOTRA:** il testo `Bando chiuso il 31 gennaio 2025` costituisce prova diretta dello stato chiuso e della scadenza, anche qualora un portale non esponga il campo strutturato in modo leggibile dallo scanner.
- L'evidenza di un'apertura storica è conservata; `effective_status` usa la data corrente e la scadenza per evitare di mostrare APERTA una finestra già terminata.

I nuovi controlli mantengono il limite sulla scansione, i collegamenti ufficiali e la separazione fra fonte, deadline, stato e ammissibilità.

### Parser version 6: revisione obbligatoria dopo nuovi formati ufficiali
L'integrazione dei formati Vol.To, MiC e ALCOTRA della PR #34 richiede un bump di versione del lettore dettagli. Senza questo, le schede con `detail_checked_at` recente e `detail_version=5` verrebbero saltate, anche se il codice ora riconosce le loro scadenze. La versione **6** forza la revisione progressiva degli elementi candidabili secondo la coda equa e il budget per fonte; la scansione produce nuovi valori di `deadline`, `deadline_source` e stato soltanto quando la fonte realmente letta contiene evidenze.

## Normalizzazione delle opportunità (novembre 2026)
- Il monitoraggio delle fonti controlla direttamente la scheda ufficiale **Torino Youth Climate Action Fund**: termine di presentazione delle proposte progettuali l'**8 ottobre 2026**, quindi scaduto. La data è acquisita dal testo «Termine di presentazione delle proposte progettuali: ore 12.00 del 8 ottobre 2026», non da un periodo generico di attività.
- La scheda ufficiale **ALCOTRA PITER+ — progetti singoli 2021–2027** riporta «Data di chiusura 03/12/2024» e non è più candidabile. Viene riletta direttamente senza promuoverla artificialmente a opportunità aperta.
- Vol.To/CSVnet pubblica talvolta lo **stesso bando tramite due indirizzi**. Il catalogo unifica esclusivamente record CSVnet dello stesso ente, con titolo identico e scadenza identica, mai finestre o edizioni diverse; conserva gli URL alternativi e la prima data di individuazione. Le opportunità prive di data non sono accorpate senza prove.
- La deduplicazione viene eseguita prima del salvataggio dei JSON e del report di copertura, così i conteggi non duplicano lo stesso finanziamento. Non modifica la UI o il flusso FTP.

## Dashboard: backlog candidature vs altri contenuti (17/11/2026)
La scheda `DA APPROFONDIRE` riguarda **solo** `finanziamento potenziale` e `call progettuale da verificare` prive di stato confermato. Le schede con `opportunity_type` differente, se prive di stato attivo/scaduto verificato, sono rappresentate nella categoria separata `ALTRO CONTENUTO`: ciò evita di confondere le pagine informative o non classificate con bandi candidabili, senza cambiare lo stato canonico `funding_status`, inventare date o eliminare record. I pulsanti di stato riportano i numeri calcolati sul dataset realmente caricato, anche sulla copia locale di riserva. Il filtro iniziale e il pulsante Azzera filtri mostrano **TUTTI** i record, come richiesto; l'ordinamento privilegia i bandi aperti e le call da verificare, e colloca gli altri contenuti in fondo. La modifica è al frontend: richiede la pubblicazione manuale via SFTP da `jeckodevsite` secondo `docs/DEPLOY.md`.

## Stato iniziale dashboard (17/11/2026)
La vista iniziale e il reset dei filtri selezionano sempre **Aperte**. La vista **Tutti** continua a includere ogni scheda, comprese le pagine informative, ma è attivabile soltanto con scelta esplicita. È mantenuta la distinzione fra **Da approfondire** (solo candidabili) e **Altri contenuti**. La modifica corregge la regressione introdotta con la separazione delle categorie e richiede pubblicazione frontend SFTP.

## Consolidamento lettura allegati PDF (18 novembre 2026)
- L'estrazione documentale combina ora **evidenze complementari** provenienti da un massimo di due PDF ufficiali HTTPS dello stesso dominio, anziché scegliere solamente il PDF con il maggior numero di campi. Per esempio, destinatari nel bando e partenariato nelle FAQ concorrono alla stessa scheda.
- La fonte originaria di ciascun campo acquisito dai PDF viene conservata in `assessment_field_sources` (mappa campo → URL). Resta disponibile `assessment_evidence_source` per compatibilità con le schede precedenti.
- A parità di campo, prevale il primo documento nella lista: l'estrattore non stabilisce automaticamente quale versione del bando sia prevalente. Un eventuale conflitto richiede verifica; non si deduce l'ammissibilità legale da parole chiave.
- Si mantengono i limiti preesistenti di documenti, pagine, byte, timeout, controllo robots e origine. Non viene salvata una copia dei PDF; i PDF scannerizzati senza testo ricercabile rimangono non leggibili senza un processo specifico.
- La mappa di provenienza viene mantenuta nei successivi cicli di scansione, anche quando una scheda non è riletta. La dashboard non cambia graficamente.

## Evidenze HTML pertinenti al requisito (18 novembre 2026)
- Il parser delle schede HTML (schema dettaglio v9) non considera più una semplice occorrenza di parole come "requisiti", "partnership" o "attività" una prova sufficiente di candidabilità. Acquisisce invece i passaggi da sezioni esplicitamente etichettate (obiettivi, attività finanziabili, beneficiari, requisiti), oppure da affermazioni puntuali riguardanti l'accesso e le condizioni del bando.
- Una sezione o una parola chiave senza contenuto sostanziale non valorizza i quattro campi documentali; il campo resta mancante. La revisione automatica v9 riprende progressivamente le schede acquisite con versioni precedenti.
- Gli estratti riportano contenuti della fonte, non certificazioni di ammissibilità; la valutazione resta prudente e separata dalle date di apertura.
- Limite dell'incremento: i PDF rimangono soggetti al parser documentale dedicato; gli estratti storici acquisiti in passato vanno riconciliati nelle scansioni successive, anche quando le pagine non sono più accessibili. Il criterio selettivo potrebbe recuperare meno campi, ma con minore rischio di falsi positivi.

## Diagnostica documentale e divergenze tra PDF (18 novembre 2026)
- La lettura dei PDF ufficiali registra in `assessment_document_diagnostics` esiti per documento (evidenze estratte, testo non estratto, testo leggibile ma nessuna evidenza pertinente, PDF non interpretabile, file eccessivo, accesso non consentito, download non riuscito o risposta non valida).
- `testo_non_estratto` non dimostra da solo che il file sia scannerizzato: indica che l'estrazione testuale non ha trovato testo nelle pagine esaminate. Non viene eseguito OCR e non si salvano copie del file.
- Se due PDF restituiscono testi diversi per lo stesso campo, prevale temporaneamente il primo estratto, ma `assessment_document_discrepancies` conserva i due URL e segnala `testi_diversi_da_verificare`. Due formulazioni diverse **non sono automaticamente in contraddizione**: serve una revisione prima di trarre conclusioni.
- `assessment_document_issues` riunisce i problemi documentali in modo distinto da `assessment_missing_fields`; le anomalie **non riempiono** campi mancanti, non cambiano stato del bando, percentuale di adeguatezza né attestano idoneità dell'associazione.
- Tutti questi dati rimangono metadati pubblici tecnici della scansione, senza testo integrale dei documenti. Le scansioni successive conservano la diagnostica come fanno per gli estratti; in una successiva fase si affinerà la gestione dello storico per distinguere anomalie ormai risolte.

## Esportazione PDF completa della scheda opportunità (18 novembre 2026)
- La funzione **Esporta PDF** genera un documento stampabile A4 che comprende tutte le informazioni presenti nel pannello «Requisiti, condizioni e informazioni aggiuntive»: finalità, attività finanziabili, destinatari/beneficiari, requisiti, ambito, data di apertura, natura dell'importo, edizione, finestra corrente, finestre successive e indicazioni per le procedure a sportello.
- Una sola funzione `opportunityRequirementFacts()` alimenta sia il dettaglio Web sia la stampa, per evitare che i due elenchi divergano nei prossimi sviluppi. I campi assenti non vengono inventati; se nessun dato è disponibile appare una nota di incompletezza.
- Restano inclusi titolo, ente, stato, scadenza, importo, adeguatezza motivata, copertura/metodo, criticità e verifiche, spunti progettuali e l'elenco dei link alle fonti e agli allegati.
- L'impaginazione di stampa usa una colonna per i testi lunghi e consente alle sezioni estese di proseguire nelle pagine successive; testi esterni sono inseriti come nodi di testo e i link sono limitati a HTTPS.
- L'esportazione è una stampa del browser («Salva come PDF»); non richiede backend PDF, non cambia le valutazioni, né produce file di documentazione pubblici contenenti note riservate della gestione personale.

## PDF sintetico senza metadati tecnici (18 novembre 2026)
- La sezione «Motivazione dell'adeguatezza» del PDF mostra soltanto la motivazione sostanziale; sono esclusi «Copertura documentale», «Metodo» ed «Elementi utilizzati». Il disclaimer finale è mantenuto.
- I dati tecnici restano disponibili nella scheda Web, nel pannello espandibile dedicato alla metodologia. Requisiti, condizioni e informazioni aggiuntive restano integralmente esportati.

## Vincoli documentali nel giudizio di adeguatezza (18 novembre 2026)
- L'adeguatezza continua a essere espressa su un solo indicatore grafico, distinto dall'apertura e dall'ammissibilità giuridica.
- Quando il parser trova formulazioni diverse per **beneficiari** o **requisiti** in PDF ufficiali differenti, la valutazione ALTA viene prudenzialmente limitata a MEDIA e viene registrato `adequacy_verification_flags: ["fonti_requisiti_da_confrontare"]` e una motivazione leggibile. Non è una certificazione di conflitto: possono essere passaggi complementari o versioni differenti, da verificare manualmente.
- Divergenze nelle sole finalità non comportano un abbassamento automatico, perché non dimostrano una differenza nell'ammissibilità.
- Le espressioni negative come «non solo persone fisiche» non sono interpretate come esclusioni; un'esclusione chiara di associazioni culturali resta invece un vincolo prudenziale già esistente.
- Il giudizio non aumenta automaticamente per la presenza di più documenti; mantiene traccia dei segnali di verifica senza inventare requisiti, possibilità di partecipazione o percentuali di aggiudicazione.

## Segnali documentali di accesso al bando (18 novembre 2026)
- Ogni opportunità riceve un campo `eligibility_condition_status` **separato** dal giudizio unico di adeguatezza e dallo stato temporale della call. I valori sono: `compatibilita_documentata` (la fonte indica esplicitamente fra i beneficiari associazioni/enti non profit; nessuna certificazione di ammissibilità completa), `condizionata` (partenariato o cofinanziamento obbligatorio citato), `potenzialmente_incompatibile` (destinatari esclusivamente individuali o imprese; verificare eventuale ruolo come partner), `informazioni_insufficienti` (assenza di prova pertinente o fonte), `non_applicabile` (pagina informativa).
- `eligibility_condition_reason` registra una motivazione prudente; `eligibility_condition_sources` conserva riferimenti HTTPS delle fonti e, quando presente, la provenienza per campo dalla lettura dei PDF. Le mere occorrenze del termine «associazione» nei testi non costituiscono prova senza un'espressione relativa all'ammissibilità o una revisione documentale.
- Questo è un **segnale operativo**, non un verdetto giuridico, né una sostituzione dei requisiti puntuali di un ente. Non presuppone che Opera+ abbia sede, iscrizioni, anzianità, dimensione, cofinanziamento o partner richiesti. Nessuna opportunità viene nascosta e le etichette grafiche di adeguatezza restano invariate.
- Il sistema mantiene la valutazione motivata per tutte le opportunità. I segnali sono generati a ogni scansione dopo l'applicazione delle revisioni documentali.
 
## Requisiti specifici documentati (18 novembre 2026)
- Lo scanner registra in `eligibility_specific_requirements` le condizioni esplicitamente riconoscibili negli estratti ufficiali su cinque dimensioni: territorio e sede; registrazione e natura giuridica; anzianità; cofinanziamento, bilancio e fatturato; partenariato e suoi requisiti minimi.
- Ogni elemento contiene categoria, breve estratto, campo sorgente e collegamento HTTPS attribuibile, con stato `requisito_documentato_da_verificare`. La quantità totale è `eligibility_specific_unchecked`; non è un numero di requisiti non soddisfatti.
- Una mera menzione di città, budget o partner non costituisce requisito. Le condizioni non riconosciute dai pattern restano documentazione da esaminare; la mancanza di un match **non significa** assenza di vincoli. Non si deducono sede, iscrizione RUNTS, anzianità, dimensioni economiche o partner effettivamente posseduti da Opera+.
- Il motore **non certifica** l'ammissibilità né altera il singolo giudizio visuale di adeguatezza, lo stato di apertura, il PDF o la dashboard. Un confronto conclusivo richiederà dati dell'associazione verificati e requisiti letti integralmente.
- L'estrazione è prudenziale e riguarda soltanto `requirements_excerpt` e `beneficiaries_excerpt` con provenienza documentale, non titolo o tag tematici. I campi vengono rigenerati ad ogni scansione e non sono esposti come nuovi badge.

## Profilo richiedente e confronto documentale prudente (18 novembre 2026)
- In `config/applicant_profile.json` esiste uno schema versionato dei dati dell'associazione. La natura di «associazione culturale» è indicata come **dichiarata**, non verificata documentalmente; sede, iscrizione al RUNTS, data costitutiva, dati economici e partner sono inizialmente sconosciuti. Nessun dato identificativo o finanziario riservato deve essere inserito in un repository pubblico.
- Ciascun campo del profilo contiene `value`, `verification` (`non_verificato`, `dichiarato`, `documentato`) e `source`. Un fatto `documentato` richiede un riferimento alla prova; le sole dichiarazioni non determinano automaticamente un requisito soddisfatto.
- Il confronto produce `applicant_requirement_comparison` con categoria, requisito, fonte, esito (`compatibile`, `potenzialmente_incompatibile`, `da_verificare`) e motivazione. I conteggi sono in `applicant_comparison_counts` e **non rappresentano** la certificazione di ammissibilità complessiva.
- Nella prima iterazione sono confrontabili soltanto due vincoli interpretati in modo sufficientemente puntuale: obbligo **esplicito** di iscrizione al RUNTS con valore booleano documentato e anzianità minima esplicita rispetto alla data costitutiva documentata e alla data della scansione. Un semplice elenco di soggetti ammessi (ad esempio «iscritti al RUNTS») non dimostra un obbligo esclusivo; l'anzianità non ancora raggiunta alla data del controllo resta da verificare perché il termine di candidatura potrebbe essere successivo. Anche questi esiti restano indicativi: gli altri requisiti, il periodo di riferimento del bando ed eventuali eccezioni potrebbero prevalere.
- Territorio (sede legale/operativa), importi, cofinanziamento e partenariato rimangono `da_verificare` anche se il profilo contiene dati documentati: le formulazioni nei bandi possono essere condizionate o ambigue, e non vengono fatte deduzioni geografiche o economiche rischiose.
- L'elaborazione non cambia il giudizio grafico unico, non modifica la classificazione APERTA/SCADUTA, non altera PDF e dashboard e non nasconde le opportunità. Tutti i campi vengono ricalcolati ad ogni scansione.

## Dati dichiarati dell'associazione e confronto preliminare (18 novembre 2026)
- Profilo Opera+ aggiornato da dichiarazione del 18/11/2026: **associazione culturale non riconosciuta**, costituzione **23/04/2026**, sede legale dichiarata **Torino, Piemonte**, codice fiscale presente, iscrizione **RUNTS in corso**, nessuna attività pregressa dichiarata, disponibilità a partenariati, cofinanziamento valutabile soltanto caso per caso.
- Tutti i nuovi dati sono classificati `dichiarato`: nessuna risposta viene promossa automaticamente a `documentato` né certifica l'ammissibilità a una call. Sono registrati solamente fatti organizzativi non segreti: non vengono raccolti codice fiscale numerico, dati personali, disponibilità finanziarie, accordi nominativi o copie di documenti. **Attenzione**: `config/applicant_profile.json` si trova in un repository pubblico; in futuro eventuali dati riservati devono restare fuori da questo file e dai JSON pubblicati.
- Per i requisiti RUNTS obbligatori, il confronto segnala che la registrazione è *in corso* e che occorre verificarne il completamento entro la data prevista. Per l'anzianità minima, la data dichiarata permette di segnalare preliminarmente se il requisito **non è ancora raggiunto alla data della scansione**: il risultato resta `da_verificare` perché il bando potrebbe fissare una data successiva e servirà verificare l'atto costitutivo.
- Per la sede si riporta il luogo dichiarato senza certificare la corrispondenza con sedi legali/operative e aree ammissibili; per il partenariato, la disponibilità a collaborare non equivale alla presenza di partner formalizzati; per il cofinanziamento, la valutazione caso per caso non dimostra una capacità economica.
- Nuova categoria `esperienza_pregressa`: rileva soltanto requisiti espliciti di progetti/attività già realizzati, perché Opera+ dichiara di non aver ancora svolto attività; questa circostanza non comporta esclusione automatica da opportunità per nuovi enti.
- Lo stato `da_verificare` non significa esclusione: i motivi associati servono a orientare la candidatura, senza alterare lo stato APERTA/SCADUTA, il giudizio grafico unico di adeguatezza o il PDF.

## Coda operativa di verifica delle opportunità aperte (18 novembre 2026)
- Ogni scansione produce nel report `data/scan-status.json` il blocco `open_eligibility_review`. Contiene le opportunità classificate **APERTO** dal motore di stato (nessuna inferenza di apertura dalle sole date), con ID pubblico, titolo, adeguatezza esistente, situazione documentale, eventuali condizioni pendenti, data di scadenza quando valida, fonti ufficiali e una lista sintetica di verifiche concrete.
- L'ordinamento porta prima le scadenze **entro 14 giorni**, poi fra pari urgenze evidenzia le condizioni di ammissibilità da chiarire (condizionata o potenzialmente incompatibile), poi la scadenza e il numero di condizioni ancora da verificare. Le opportunità a sportello o senza data esplicita **non ricevono** una data inventata e restano nella coda.
- `condition_status_counts` riepiloga le condizioni di tutte le opportunità aperte; `specific_requirement_category_counts` conta le categorie di requisiti riconosciuti. `open_total` non dipende dal limite eventuale di visualizzazione, mentre `in_queue` descrive le righe effettivamente incluse.
- Le verifiche derivano soltanto dai metadati già estratti: beneficiari e attività mancanti, requisiti senza fonte, partenariato, cofinanziamento, RUNTS, anzianità, sede, esperienza pregressa, PDF non letti e testi da confrontare. Non sono giudizi giuridici e **non cambiano** la percentuale di adeguatezza né la disponibilità delle opportunità.
- Il report è un output operativo per la futura agenda e la revisione documentale, **non una nuova schermata pubblica**. I dati sono ricalcolati dopo l'applicazione del profilo richiedente a ogni scansione. Nessuna pubblicazione SFTP dell'interfaccia è richiesta.

## Attivazione scansioni per i moduli di ammissibilità (18 novembre 2026)
- Il workflow `.github/workflows/scan.yml` monitora anche `src/eligibility_conditions.py`, `src/eligibility_specific.py`, `src/applicant_comparison.py`, `src/open_review_queue.py` e `config/applicant_profile.json` oltre agli altri file già previsti. In precedenza questi nuovi moduli non erano inclusi nel filtro di push: il merge di una loro modifica poteva non lanciare il ricalcolo.
- La scansione rimane eseguibile manualmente e programmata quotidianamente. Il report `data/scan-status.json` deve contenere `open_eligibility_review` dopo la prima scansione realmente conclusa sul nuovo codice. **Non interpretare la sola integrazione della PR come prova di aggiornamento dei JSON**, ma verificare timestamp, esito del job e presenza dei nuovi campi.
- Un test di regressione blocca le PR se un file essenziale per i requisiti, il profilo o la coda non è incluso nei percorsi monitorati. Il filtro non comprende i documenti non funzionali, evitando scansioni per sole modifiche editoriali.

## Gate automatico di integrità prima di notifiche e pubblicazione (18 novembre 2026)
- Il workflow di scansione esegue `python src/scan_integrity.py` **subito dopo lo scanner e prima dell'invio delle email**. Se il controllo fallisce, GitHub Actions interrompe la scansione con errore e **non invia notifiche né pubblica i nuovi JSON**. L'esito è visibile direttamente nei log del job.
- Il validatore controlla che il catalogo non sia vuoto, che il timestamp `checked_at` sia recente (massimo 30 minuti, con tolleranza per differenze d'orologio), che gli ID numerici siano validi e univoci, che tutti i record abbiano adeguatezza, copertura documentale e metadati di ammissibilità, che i totali coincidano con i dati e che la coda `open_eligibility_review` includa esattamente le opportunità marcate `APERTO` con controlli operativi non vuoti.
- I fallimenti segnalano la tipologia del problema, senza sostituire lo storico esistente con una scansione parziale. Il gate prova la **coerenza interna** dei dati, non la correttezza dei siti ufficiali, il completamento delle candidature o l'ammissibilità giuridica.
- È incluso un test di regressione per omissione di campi, duplicati, report scaduti, conteggi non coerenti e coda parziale. La modifica allo script di controllo stesso ora rientra tra i percorsi che attivano una scansione su `main`.

## Priorità di arricchimento documentale sulle opportunità aperte (18 novembre 2026)
- La scansione mantiene i limiti di interrogazioni per fonte e continua a dare precedenza ai **nuovi bandi** e ai record non ancora esaminati. All'interno delle revisioni periodiche dei candidati già consultati, vengono anticipati i bandi classificati **APERTO** che mancano di attività finanziabili, beneficiari o requisiti esplicitamente documentati. Se scadono nei prossimi 14 giorni, ricevono ulteriore precedenza.
- Le schede aperte con questi campi incompleti sono eleggibili a un nuovo tentativo dopo **24 ore** dall'ultima lettura, mentre i casi completi e gli archivi mantengono il limite di **3 giorni**. Questo non garantisce nuove evidenze: fonti non disponibili, limitazioni di accesso e PDF illeggibili restano segnalati senza inventare informazioni.
- La precedenza non altera il giudizio di adeguatezza, lo stato APERTO/SCADUTA, la coda delle verifiche, le iscrizioni o il PDF. Rimangono invariati la scoperta di nuove opportunità e i limiti di scansione per non sovraccaricare le fonti.
- Dati di controllo al 18/11/2026, report 21:55 UTC: 33 aperte; 11 senza attività finanziabili complete, 10 con requisiti incompleti, 7 con beneficiari da chiarire. I conteggi non sono disgiunti e devono essere aggiornati dopo la nuova scansione.

## Riconciliazione e percorso operativo per ogni opportunità (18 novembre 2026)
- La scansione include il blocco `catalog_reconciliation` in `data/scan-status.json`: conteggi coerenti fra catalogo complessivo, opportunità APERTE e sottoinsieme APERTE con adeguatezza ALTA/MEDIA. Per ogni gruppo riporta lacune documentali nelle finalità, attività finanziabili, beneficiari e requisiti, anomalie delle fonti, controlli richiedente pendenti e fonte non attribuibile. La lista `priority_open_ids` identifica gli ID numerici del sottoinsieme prioritario senza modificare l'ordinamento della dashboard.
- Ogni scheda ottiene un `application_path` operativo **distinto dal giudizio grafico di adeguatezza**, una motivazione `application_path_reason` e i controlli `application_next_actions`. I percorsi sono `verificare_candidatura_diretta`, `verificare_candidatura_in_partenariato`, `integrare_verifica_documentale`, `bassa_priorita_progettuale`, `non_attiva`. Nessun percorso equivale a esito giuridico accertato; `application_eligibility_verified` resta sempre `false`.
- Il percorso diretto è **solo un invito alla verifica**: richiede che una fonte attribuibile citi associazioni tra i beneficiari, che siano presenti estratti di attività, beneficiari e requisiti e che non siano note condizioni pendenti o divergenze documentali. Non basta l'etichetta ALTA. Se un partenariato è obbligatorio, si propone di verificare capofila e accordi. Se la fonte esclude la candidatura diretta ma menziona partner ammissibili, si verifica tale ruolo senza inventare ammissibilità.
- Il giudizio BASSA mantiene la scheda visibile ma riduce la priorità di investimento nella candidatura; i bandi non APERTI non diventano presentabili. Le opportunità incomplete rimangono nel catalogo e nella coda, con i documenti da recuperare. Le motivazioni operative non sostituiscono i requisiti ufficiali.
- La coda `open_eligibility_review` include i percorsi, i passi successivi e il riepilogo `application_path_counts`. Il controllo di integrità impedisce che siano pubblicati catalogo e report privi di questi dati o con totali incongruenti. Nessun nuovo punteggio, badge o scala grafica.
- I conteggi dell'ultima scansione precedente al rilascio sono soltanto una base storica; **verificare l'effettiva nuova scansione** prima di dichiarare i risultati aggiornati.

## Verifica individuale urgente — ECG Piemonte 2026 (18 novembre 2026)
- Opportunità pubblica `176`: fonte ufficiale Regione Piemonte `https://bandi.regione.piemonte.it/contributi-finanziamenti/bando-educazione-alla-cittadinanza-globale-sostenibilita-solidarieta-internazionale-anno-2026`, scadenza **23 novembre 2026**. La pagina ufficiale conferma attività ammissibili di Educazione alla Cittadinanza Globale, percorsi didattici e di sensibilizzazione.
- **Capofila:** solo OSC con sede legale/operativa in Piemonte da almeno **3 anni** ed esperienza specifica ECG negli ultimi **3 anni**; per le categorie indicate di associazioni senza fine di lucro è prevista l'iscrizione RUNTS. Opera+ dichiara costituzione il 23/04/2026, RUNTS in corso e nessuna attività pregressa: **non emerge un percorso di candidatura diretta come capofila** alle condizioni attuali.
- **Partner:** la fonte consente a una OSC di partecipare come capofila o partner a una sola proposta; è obbligatorio almeno un ente locale piemontese co-proponente. Va ancora confermato il perimetro di ammissibilità dei partner, senza presupporre che Opera+ sia automaticamente ammessa a questo ruolo. Contributo regionale fino a 15.000 euro, massimo 90% dei costi.
- Giudizio MEDIA motivato solo per **possibile partecipazione progettuale in partenariato**, non come capofila. L'azione `verificare_candidatura_in_partenariato` richiede individuazione di capofila OSC idonea, autorità locale co-proponente, verifica dei partner nel bando integrale e sostenibilità economica.
- La revisione integra gli estratti ufficiali nel file `config/assessment_reviews.json`; non modifica artificialmente scadenza o apertura né dichiara conclusa la valutazione giuridica.

## Conservazione delle verifiche individuali nella coda operativa (18 novembre 2026)
- La coda `open_eligibility_review` riutilizza anche le attività `assessment_gaps` risultanti dalle singole revisioni documentali, senza farle scomparire quando le quattro categorie di estratti risultano popolate.
- Esempi concreti: il bando **Dora in Avanti** (#175) richiede conferma della presenza territoriale e dei requisiti ETS; l'invito **Circoscrizione 7** (#8) richiede di consultare gli avvisi PDF settoriali su eventi culturali e formazione. Queste richieste ora restano visibili come controlli, invece del generico «Confermare i requisiti».
- Le attività sono testo di fonte/revisione da svolgere, **non certificazioni di idoneità**. Nessuna opportunità viene rimossa o automaticamente promossa; rimane un solo giudizio visivo di adeguatezza.
