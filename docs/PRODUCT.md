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
