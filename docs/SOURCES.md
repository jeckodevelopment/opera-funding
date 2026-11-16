# Registro delle fonti (prima versione)

La configurazione machine-readable è in `config/sources.json`. Ogni URL è un **punto di partenza da verificare**, non una garanzia di recupero automatico. Il primo connettore effettua discovery dei link sulle pagine indice accessibili: alcune fonti usano Javascript, sistemi anti-bot o API che richiederanno adattatori dedicati.

Priorità alta: Compagnia di San Paolo; Fondazione CRT; Regione Piemonte; Comune di Torino; Fondazione per la Cultura Torino.
Priorità media: Vol.To (aggregatore da ricondurre alla fonte originale); MiC spettacolo; Europa Creativa; Erasmus+; Funding & Tenders.

## Campi da aggiungere per fonte
- endpoint RSS/API, sitemap o selettori e paginazione
- eventuali condizioni d'uso e frequenza consentita
- data ultimo controllo positivo e numero opportunità riconosciute
- grado di copertura e alert di malfunzionamento
- giurisdizione, destinatari e aree di intervento

Non aggirare sistemi anti-bot e rispettare robots.txt, termini d'uso e limiti di frequenza.

## Nuove fonti europee (16/11/2026)
- Desk Italia Europa Creativa: https://europacreativa.cultura.gov.it/ — pagina nazionale con notizie e aggiornamenti sulle call.
- Interreg ALCOTRA: https://interreg-alcotra.eu/it/bandi-0 — progetti transfrontalieri Italia–Francia, potenzialmente utili per collaborazioni culturali e formative.
- Agenzia nazionale Erasmus+ Italia: https://www.erasmusplus.it/programma/documenti-ufficiali/ — testi ufficiali e guide, non lista strutturata dei singoli bandi.

Attenzione: il crawler generico legge ancora soltanto gli indici HTML; per i portali europei che mostrano bandi via JavaScript o documenti aggregati sono necessari adapter dedicati. L'aggiunta di una fonte non prova che tutte le sue call siano già coperte. Nessuna opportunità viene attribuita a Opera+ senza verifica dei requisiti.

## Priorità 2026: spettacolo dal vivo
La pagina ufficiale [Aiuti allo spettacolo dal vivo](https://bandi.regione.piemonte.it/contributi-finanziamenti/aiuti-allo-spettacolo-dal-vivo) è stata aggiunta al controllo diretto ripetuto: lo stato, la scadenza e la loro provenienza vengono nuovamente estratti dal sito della Regione a ogni esecuzione, non precaricati come fatti nel JSON. Il bando è rivolto a **imprese e liberi professionisti**: la sua apertura non costituisce prova dell'ammissibilità di Opera+, che richiede una verifica delle condizioni del bando e dell'eventuale forma progettuale.

## Adattatori alle fonti piemontesi (novembre 2026)
- **Compagnia di San Paolo:** il parser riconosce ora `Stato: IN CORSO` e `Data scadenza`, senza interpretare `Data pubblicazione` come scadenza. I bandi prioritari `Festival partecipativi 2027` e `AI nell'economia sociale` sono monitorati direttamente. Il primo prevede finestre differenti per i festival di stagioni diverse: consultare il calendario completo, non soltanto l'ultima data riportata in testata.
- **Città di Torino:** interpretazione delle finestre ufficiali `Attivo dal DD/MM/YYYY al DD/MM/YYYY`, esclusivamente su pagine del portale bandi comunale; priorità agli avvisi per iniziative culturali della Circoscrizione 7.
- **Fondazione CRT:** resta fonte ad alta priorità, ma lo stato degli avvisi e le scadenze si considerano provati solo se individuati nelle pagine o documenti ufficiali; non vengono dedotti dall'appartenenza al registro delle fonti.
- Le opportunità vengono sottoposte a controlli effettivi a ogni scansione mediante link ufficiale e robots.txt. L'inclusione nella lista di priorità non equivale ad apertura o ammissibilità accertata.

## Verifica dei bandi europei in inglese
- L'adattatore per le schede della Commissione europea riconosce `Opportunity status: open/closed`, `Opening date` e `Deadline` con mesi inglesi, mantenendo i collegamenti ufficiali come prova.
- Sono state aggiunte al controllo diretto le schede `Culture Moves Europe – Call for residency hosts 2026–2027` e `Circulation of European literary works 2027` (portale Cultura UE), e `European Literacy Coalition consortium` (Erasmus+). Gli accessi dipendono dal rispetto di robots.txt e dalla disponibilità delle pagine.
- Alcune call sono rivolte prevalentemente a editori, consorzi, professionisti o soggetti con caratteristiche specifiche. L'apertura della call non determina automaticamente l'ammissibilità di Opera+.
- La copertura dell'intero catalogo di Funding & Tenders e dei risultati caricati dinamicamente resta un incremento successivo: il registro delle fonti è approvato, ma non equivalente a copertura totale.

## Fondazione CRT — catalogo ufficiale e scadenze
- La fonte primaria passa dalla sezione di **notizie** `/category/progetti-e-bandi/` al **catalogo ufficiale** `/progetti-e-bandi/`. Questo riduce la discovery di articoli sulle iniziative già finanziate come se fossero bandi candidabili.
- Monitoraggio ricorrente delle tre pagine ufficiali `NoteSipari`, `Orizzonti L.I.V.E.` e `Ordinarie – Arte e Cultura`. Le pagine dell'edizione 2026 mostrano finestre multiple e, al 16/11/2026, scadenze trascorse. Lo scanner usa l'ultima scadenza identificata, senza classificare come aperto ciò che è chiuso.
- Il registro `config/sources.json` marca tutte le 13 fonti come `approved: true` secondo la decisione dell'associazione. Tale approvazione riguarda **la scelta delle fonti**, non l'affidabilità a priori dei dati raccolti, lo stato di disponibilità di ogni singola scansione o la candidabilità delle opportunità.
- Lo storico dei collegamenti già importati dalle notizie CRT viene mantenuto nel dataset; eventuale pulizia o esclusione permanente richiede una politica di archiviazione distinta.

## Europa Creativa Desk Italia: canale ufficiale alternativo (novembre 2026)
Il sito `https://europacreativa.cultura.gov.it/` è una fonte approvata di informazione e assistenza sui bandi. Il motore automatico non riesce a leggerlo perché il controllo di `robots.txt` risulta indisponibile o nega l'accesso. **Non si aggira il blocco** cambiando User-Agent, ignorando le regole o usando proxy per eludere le restrizioni.

Le opportunità sono invece reperite dal catalogo ufficiale gestito dalla Commissione europea, `https://culture.ec.europa.eu/funding/calls`, già presente nel registro come `eucreative`. In `config/sources.json`, `creativeitalia` conserva URL e identità del Desk e dichiara `official_alternative_source_id: eucreative`. Non viene eseguita alcuna richiesta automatica al portale italiano; la scansione riporta `coverage_mode: official_alternative`, `alternative_url` e un testo esplicativo. Il risultato viene segnalato positivo **solo se** la lettura del canale ufficiale alternativo è riuscita: in caso contrario rimane un errore tecnico nel semaforo.

I bandi hanno link alla **fonte reale della Commissione**, non al sito italiano che non abbiamo consultato. I risultati già importati dalle altre fonti non vengono duplicati sotto il Desk Italia. Il catalogo europeo può non comprendere tutte le notizie e i servizi informativi italiani, per cui la copertura del Desk è indiretta e **non equivale alla sua scansione completa**.

Tra le pagine ufficiali curate per il controllo diretto compare anche `Culture Moves Europe – Call for individual mobility 2026–2027`: riguarda artisti e professionisti, e non rende automaticamente Opera+ soggetto ammissibile. Se il sito europeo non consente una determinata richiesta, il controllo resta conservativo, senza forzature.

## EU Funding & Tenders — API ufficiale delle call Creative Europe

Il monitoraggio europeo adesso usa anche l'API pubblica ufficiale della Commissione europea, `https://api.tech.ec.europa.eu/search-api/prod/rest/search?apiKey=SEDIA`, documentata sul portale Funding & Tenders alla pagina `/screen/support/apis`. È un'**interfaccia prevista per l'integrazione di applicazioni esterne**, non un servizio di scraping né un proxy che elude restrizioni. Non richiede token personali, login o altri servizi di hosting.

Per `eufunding` lo scanner invia una ricerca limitata al programma Creative Europe (codice ufficiale `43251814`), a call e topic pubblici e agli stati open/forthcoming. Legge i risultati JSON, le date ufficiali, gli identificativi di topic e gli URL canonici. La risposta non valida provoca un errore della fonte: non viene scambiata per una scansione conclusa senza bandi. Gli URL dei topic sono verificati separatamente; una scadenza senza prova o un link non verificato **non** produce arbitrariamente uno stato APERTO.

`creativeitalia` conserva l'URL del Desk italiano nel registro e viene coperto indirettamente da `eufunding` grazie a `official_alternative_source_id`. Il report riporta `coverage_mode` e l'URL dell'API/portale che ha fornito realmente i dati. Non vengono forzate richieste al sito italiano bloccato. La copertura riguarda le call Creative Europe presenti nei risultati ufficiali, e non tutte le notizie italiane o tutti i programmi europei.

I dati dell'API sono interpretati in modo conservativo: l'esistenza di un topic non dimostra che Opera+ sia ammissibile e un budget generale non equivale al contributo richiedibile da una singola organizzazione. Il canale resta soggetto a modifiche future dell'API ufficiale; i test coprono schema, errori e assegnazione dello stato.

## Verifica delle candidature presso gli erogatori (novembre 2026)
Vol.To/CSVnet è un ottimo aggregatore ma non deve essere interpretato automaticamente come conferma che una candidatura è aperta. Per tre opportunità identificate direttamente sul loro sito è stato aggiunto un piccolo registro `config/issuer_checks.json`, che punta alle **pagine ufficiali degli erogatori**:
- **Fabbrica – Spazi Civici per la Gioventù**: Sport e Salute (`https://www.sportesalute.eu/fabbrica`), apertura piattaforma 04/11/2026, scadenza 18/12/2026.
- **Lo Sport è vita**: Sport e Salute (`https://www.sportesalute.eu/lo-sport-e-vita.html`), apertura 28/10/2026, chiusura 28/11/2026.
- **Una mano a chi sostiene 2026/27**: Fondazione Cattolica (`https://www.unamanoachisostiene.it/`), iscrizioni 16/11/2026–16/02/2027.

A ogni scansione, **dopo deduplicazione**, il motore può leggere le tre pagine con un controllo robots.txt standard, URL HTTPS e redirect sullo stesso host, massimo 1 MB e timeout. Richiede date di apertura e chiusura esplicite insieme al linguaggio di candidatura; soltanto allora imposta `source_open_confirmed`, `opening_date`, `deadline` e `status_evidence` con la pagina ufficiale dell'erogatore. Se l'accesso viene negato o la pagina non contiene prove, la scheda non viene promossa arbitrariamente. La verifica della finestra non costituisce una certificazione dell'ammissibilità di Opera+ né sostituisce la lettura dei requisiti e dell'eventuale partenariato.

### Interreg ALCOTRA — finestre PITER+ ufficiali
La pagina del bando `/it/bando-la-selezione-dei-progetti-singoli-dei-piani-territoriali-integrati-piter-2021-2027` descrive esplicitamente tre scadenze di presentazione: **2 luglio 2024**, **3 settembre 2024**, **3 dicembre 2024**. Il parser distingue questo elenco etichettato dalle date successive relative alla selezione e alla pubblicazione degli esiti. Registra le tre finestre in `application_windows` e la scadenza finale in `deadline`, con fonte ufficiale, pertanto nel 2026 il bando risulta **SCADUTA**. Non vengono create tre righe distinte retroattive: questa fonte storica conserva il calendario nel dettaglio; la logica di schede separate resta prevista per bandi ricorrenti come CRT Ordinarie.

## Qualità catalogo: backlog candidabile vs pagine informative (17/11/2026)
Il totale delle schede `DA VERIFICARE` include anche pagine informative già identificate come `altro avviso` (notizie CRT, guide ministeriali e documenti Erasmus+). Il report di scansione espone ora `candidate_unverified`, `informational_unverified` e `candidate_missing_deadline`, complessivi e per fonte, senza nascondere opportunità o alterare i contatori storici. La priorità operativa riguarda le opportunità progettuali senza una finestra di candidatura verificata. Il classificatore Erasmus+ Agenzia nazionale riconosce guide e PDF documentali come avvisi informativi, non come nuovi bandi. Rimangono visibili nel catalogo; la distinzione evita di interpretare una guida o un esito come candidatura aperta. Nessuna scadenza viene dedotta dal nome del file.

## Catalogo — esclusione dei falsi bandi dai controlli di candidatura (17/11/2026)
La scansione mantiene tutte le pagine nel dataset, ma non considera automaticamente una candidatura da verificare i contenuti che sono chiaramente navigazione o descrizione di progetti preesistenti: vetrine `/it/i-progetti/` di Compagnia di San Paolo, indici generici di Regione Piemonte (`/contributi-finanziamenti`, `/crowdfunding`), guida generale sui finanziamenti al patrimonio culturale della Commissione europea e pagina storica dei partenariati strategici Erasmus+ Italia. Sono classificati `altro avviso`, con motivazione, senza attribuire stato CHIUSO o scadenza inventata. Le pagine di candidatura vere sono preservate e protette da test. 

## Torino — scadenze con mese scritto in italiano (17/11/2026)
Le schede ufficiali del portale bandi di Torino possono esprimere la data come `Scadenza delle domande: 26 novembre 2026` oltre alle date numeriche già gestite. Il parser riconosce queste etichette esplicite e registra l’URL della fonte, senza confondere date di pubblicazione o dell’evento e senza assumere uno stato APERTA dalla sola presenza di una scadenza futura. L’estrazione si applica soltanto al dominio ufficiale del portale bandi torinese e ha test dedicati. Restano necessari la verifica dell’apertura e il controllo della documentazione per dichiarare una candidatura attiva.

## Verifica pagine ufficiali multilingua (17/11/2026)
Per Culture Moves Europe Residency Hosts 2026–2027 ed Erasmus+ European Literacy Coalition, il registro delle pagine prioritarie elenca un URL localizzato dello stesso host ufficiale. Se la scheda principale non offre insieme scadenza e dichiarazione esplicita di apertura, lo scanner può consultare la versione ufficiale alternativa rispettando robots.txt, HTTPS, stesso host anche dopo redirect, timeout e limite di download. L'alternativa è accettata solo con entrambe le prove; deadline_source e status_evidence registrano l'URL effettivo. La pagina principale rimane invariata e una data isolata o un sito terzo non consentono la promozione ad APERTA. L'ammissibilità di Opera+ rimane da verificare.

## Torino, finestre testuali di candidatura e linee guida (17/11/2026)
Il portale bandi di Torino può descrivere la finestra per la presentazione di una istanza come `nel periodo compreso tra il 10 settembre 2026 e il 30 settembre 2026 ... possibilità di presentare istanza`. Lo scanner interpreta la data finale come termine delle candidature **solo** quando il periodo è esplicitamente legato alla presentazione di istanze/domande/richieste, è cronologicamente coerente e si trova su `bandi.comune.torino.it`. Questo consente di riconoscere come scaduta la finestra del secondo avviso Circoscrizione 4 del 2026, documentata dal Comune; non si deduce la data da un periodo generico di eventi e non si presume che il bando sia aperto soltanto dalla data. Le pagine sulle Linee Guida 2027 della Circoscrizione 7 e sulla preinformazione di fondi UE piemontesi restano nel catalogo come contenuti informativi, non come nuove candidature aperte. Conservare la fonte e non eliminare lo storico.

**Versione parser dettagli 7.** La nuova estrazione delle finestre testuali richiede una revisione delle schede già analizzate con la versione 6, anche se controllate da meno di tre giorni. La coda rimane limitata per fonte: i risultati vengono aggiornati soltanto sulla base delle pagine effettivamente consultate, senza anticipare uno stato non provato.

## Verifica delle nove candidate residue (17/11/2026)
La riconciliazione di due pubblicazioni dello stesso avviso Circoscrizione 7 / 2027 conserva il link sindacato di Vol.To in `alternative_urls` e mantiene la scheda ufficiale Torino come unica opportunità **solo quando entrambe riportano identica scadenza ufficiale**. Senza corrispondenza di data non si accorpano.

**Educare alla lettura (Centro per il libro e la lettura).** Il link CSVnet indicizzato non è raggiungibile; viene consultata separatamente una pagina originale dell'ente, che attesta la scadenza del 13/11/2026. L'estrazione riconosce il termine esplicito di presentazione e marca SCADUTA quando la data è trascorsa, senza inventare una data di apertura.

**Call europee.** Per Residency Hosts e European Literacy Coalition il registro ora include rispettivamente un annuncio ufficiale della Commissione europea e una versione linguistica ufficiale aggiuntiva. La scansione utilizza la prima fonte che confermi *sia* lo stato aperto *sia* la scadenza; mantiene il collegamento principale. Un URL non raggiungibile oppure senza entrambi i dati lascia DA VERIFICARE.

**Altre candidate residue.** Vol.To Dora in Avanti (20/11), Culture Moves Europe mobilità individuale (30/04/2027), formazione professionisti della giustizia (04/03/2027), Una mano a chi sostiene (16/02/2027), Fondo beneficenza Intesa Sanpaolo (31/12/2026) richiedono evidenze di effettiva apertura; il solo dato nell'aggregatore non è prova sufficiente. La regola `issuer_checks` del sito Fondazione Cattolica è già presente e verifica la finestra di presentazione se robots e il sito originale consentono la lettura.
