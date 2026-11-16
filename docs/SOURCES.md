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
