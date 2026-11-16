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
