# Registro finanziatori e programmi

La gerarchia canonica è **finanziatore → programma → opportunità**. La fonte di verità versionata è `config/funders.json`; gli elementi già presenti in `config/sources.json` sono fonti di scoperta, non necessariamente erogatori.

- Ogni finanziatore ha un ID permanente, tipologia, territorio e stato di verifica. Un nome nel registro **non dimostra** che Opera+ sia ammissibile.
- Ogni programma identifica l'eventuale pagina ufficiale e un canale di candidatura; `monitoring=existing-source` indica il crawler già attivo. `monitoring=direct` viene sottoposto a scansione periodica, ma risulta **monitorato** soltanto dopo un controllo riuscito. `monitoring=reference-only` rappresenta un canale ufficiale documentato che non pubblica necessariamente bandi: è mostrato come **Solo riferimento**, senza richieste automatiche e senza falsi stati di scansione.
- Le opportunità vengono associate solo mediante `source_id` esplicito. Le opportunità provenienti da aggregatori (Vol.To) **non vengono attribuite** all'aggregatore come finanziatore; richiedono riconciliazione su fonte ufficiale.
- `scan-status.json` contiene il registro pubblico `funder_monitoring` con stato effettivo di controllo, senza dati riservati. I dati dell'associazione e le note operative restano fuori dal registro.
- I programmi senza un canale pubblico verificato sono anagrafica da approfondire, **non opportunità aperte**. Non inventare scadenze o creare schede opportunità da semplici pagine istituzionali.
- Per edizioni annuali e finestre multiple mantenere gli ID di opportunità già governati da `public_ids.py`; non usare il nome del programma come identificativo della candidatura.

## Evoluzioni da completare

1. Validare le pagine ufficiali di tutti i finanziatori e ampliare il censimento territoriale (Province e Comuni).
2. Estendere lo scanner con controlli sicuri e programmati per i programmi `direct`, con discovery di bandi effettivi e rilevamento modifiche.
3. Navigazione superiore con tre pagine logiche: `?view=dashboard`, `?view=finanziatori` e `?view=monitoraggio`. Le viste sono mutuamente esclusive; i link delle opportunità `?opportunity=<ID>` continuano a funzionare. La homepage rimane la dashboard filtrata su `Aperte`.
4. Collegare le opportunità da aggregatori all'erogatore effettivo solo dopo prova documentale; usare notifiche attuali soltanto per nuove opportunità valutate.

## Verifica frontend

- Dopo la prossima scansione, aprire `#finanziatori` e verificare la ricerca per nome, categoria e territorio.
- Aprire `#monitoraggio-programmi` e verificare che i programmi con `monitoring_status=not_configured` non appaiano come monitorati.
- Con un `scan-status.json` precedente all'introduzione del registro, verificare il messaggio di assenza dati.
- Verificare su smartphone il layout a una colonna, il filtro iniziale `Aperte`, le schede e i link PDF già esistenti.
- **Il merge di questa PR non avvia un deploy**: la pubblicazione frontend resta demandata al publisher di `jeckodevsite`.

## Controllo diretto delle pagine aziendali

Le pagine dei programmi con `monitoring=direct` (inizialmente Fondo di Beneficenza Intesa Sanpaolo ed Enel Cuore) sono controllate durante la scansione ordinaria. Il modulo `src/programme_monitor.py` verifica robots.txt, HTTPS e identità dell'host dopo eventuali redirect; impone limiti di download e mantiene impronte della pagina e collegamenti candidati appartenenti al dominio ufficiale.

La prima verifica crea una **baseline silenziosa**. Solo una variazione successiva genera `changed=true`, che significa **pagina da ricontrollare**, non "bando aperto". L'errore non cancella la baseline precedente e non è etichettato come controllo riuscito. I digest sono conservati in `data/programme-monitoring.json` nel repository, ma non esposti dal report della dashboard. Il workflow registra il file insieme a `scan-status.json`.

**Evoluzione successiva:** il modulo `src/programme_ingest.py` esamina (massimo 8 per programma a scansione, con cursore circolare persistente) i link candidati presenti su pagine ufficiali, scarta collegamenti generici e contenuti senza evidenze documentali, usa lo stesso parser delle opportunità esistenti e aggiunge al catalogo solo nuove schede con una fonte verificata e raggiungibile. I record passano dai consueti ID numerici, controlli di stato, valutazione e notifiche già esistenti. Le sole modifiche della pagina non inviano email né implicano apertura. I link a bandi annuali devono avere un URL specifico: se l'ente riutilizza la stessa URL per nuove edizioni, l'estrazione deve preservare esplicitamente le finestre applicative prima di separare le edizioni.

### Collaudi aggiuntivi
- Eseguire `python -m unittest tests/test_programme_monitor.py` oppure la suite completa.
- Prima scansione: `baseline_created=true`, `changed=false` per pagine raggiungibili.
- Scansione successiva: `changed=true` solo se il contenuto rilevante cambia.
- Simulare robots.txt negato e verificare `error` senza cancellare la baseline.

## Collaudi: navigazione e ingestione

- Il menu in alto mostra soltanto Dashboard, Finanziatori, Monitoraggio programmi. Ogni voce mostra la propria vista esclusiva, su desktop e smartphone; l'indicatore di salute conduce al pannello di monitoraggio.
- L'apertura diretta di `?view=finanziatori` o `?view=monitoraggio` funziona senza perdere le altre sezioni; la homepage mostra le opportunità Aperte.
- I collegamenti permanenti `?opportunity=<ID>` aprono esclusivamente la scheda, con ritorno al catalogo. La stampa PDF non visualizza le sezioni nascoste.
- Verificare che nuovi link ufficiali specifici siano esaminati e ammessi solo se la pagina presenta evidenze concrete; niente nuovi record da FAQ o pagine generiche. Un programma non raggiungibile o negato da robots non genera opportunità.
- Ripetere la scansione e verificare assenza di duplicati: stessa URL mantiene l'ID numerico. Le candidature senza apertura provata rimangono da verificare e non attivano email di nuovi bandi aperti.
- Controllare `scan-status.json > programme_ingestion` (numero nuovo, già presente, scartato per programma); nessun dato riservato viene pubblicato.

## Integrità del catalogo

L'ingestione dei nuovi bandi riutilizza le funzioni già presenti in `src/operational_assessment.py` e `src/catalog_reconciliation.py`: valutazioni operative conservative e coperture documentate sono prodotte dal medesimo ciclo di scansione, senza introdurre un modello parallelo.

## Interfaccia compatta

Le pagine **Finanziatori** e **Monitoraggio programmi** visualizzano tabelle HTML semantiche invece delle precedenti schede. Finanziatori mostra nome, tipologia, territorio, numero di programmi e link alla fonte ufficiale; la ricerca per nome/tipologia/territorio rimane attiva. Monitoraggio mostra programma, finanziatore, stato reale, ultima verifica e fonte, segnalando modifiche da controllare separatamente dall'apertura di nuovi bandi. Le tabelle sfruttano larghezze proporzionali ai contenuti sui dispositivi ampi. Su schermi stretti ogni record resta una riga logica, presentata con campi e relative etichette disposti verticalmente, senza scorrimento orizzontale imposto. Nessuna modifica alla Dashboard principale, agli identificativi delle opportunità, al motore di scansione o al giudizio di adeguatezza.

### Collaudi UI

- Verificare la disposizione in riga delle tabelle, la ricerca e la corrispondenza fra contatori e righe filtrate.
- Verificare gli stati monitorato/errore/non configurato, le date, i link ufficiali e la marcatura di pagina modificata.
- Su smartphone verificare che ogni riga mostri etichette e valori senza scrolling orizzontale o contenuti tagliati.
- Controllare regressioni: menu a tre pagine, Dashboard con default *Aperte*, scheda opportunità e PDF.

## Ampliamento censimento — 18 novembre 2026

Sono stati aggiunti **10 finanziatori** (Comuni di Alba, Bra, Pinerolo, Rivoli, Moncalieri, Asti, Chivasso, Città Metropolitana di Torino e Province di Novara e Alessandria) e **14 programmi/canali** istituzionali e aziendali. Totale: **41 finanziatori, 21 programmi**; **10** programmi di tipo `direct`, **5** già monitorati dalle fonti tradizionali e **6** `reference-only`. Questi sono valori di configurazione: lo stato operativo reale è letto dall'ultima scansione.

La copertura diretta comprende pagine ufficiali di contributi culturali dei Comuni di Alba, Bra, Pinerolo, Rivoli, Moncalieri, bandi delle politiche giovanili della Città Metropolitana e liste di Fondazione TIM e UniCredit Foundation. I nuovi programmi possono generare schede solo quando vengono individuate pagine specifiche con dati verificabili e superano la pipeline esistente: non si genera automaticamente un bando dalla pagina generica del programma.

- **Alba:** https://www.comune.alba.cn.it/it/page/bando-per-le-associazioni-area-cultura-2023 — attenzione a bandi territoriali e edizioni annuali; la pagina di riferimento può mantenere un vecchio slug.
- **Bra:** https://www.comune.bra.cn.it/it/page/richiesta-di-contributi — contributi alle associazioni con sede o operatività territoriale.
- **Pinerolo:** https://www.comune.pinerolo.to.it/schede-informative/bando-pubblico-per-selezione-proposte-per-lassegnazione-contributi-economici
- **Rivoli:** https://www.comune.rivoli.to.it/Novita/Avvisi/Avviso-pubblico-per-la-concessione-di-contributi-economici-alle-associazioni-del-territorio
- **Moncalieri:** https://www.comune.moncalieri.to.it/servizi/bando-manifestazioni — verificare anche iscrizione albo comunale.
- **Città Metropolitana di Torino:** https://www.cittametropolitana.torino.it/istruzione-e-sviluppo-sociale/politiche-giovanili/avvisi-e-bandi — alcune misure sono riservate ai Comuni.
- **Fondazione TIM:** https://www.fondazionetim.it/bandi — bandi anche per Cultura e Arte.
- **UniCredit Foundation:** https://www.unicreditfoundation.org/it/bandi-aperti — possibili bandi rivolti a singoli ricercatori o istituzioni specifiche.
- **Iren:** https://sponsorizzazioni.gruppoiren.it/ — portale richieste contributi: **Solo riferimento**, non bando.
- **Reale Foundation:** https://www.realegroup.eu/IT/chi-siamo/sostenibilita/reale-foundation — **Solo riferimento**, non prova di candidatura libera.
- **Asti, Chivasso, Novara e Alessandria:** pagine ufficiali informative o regolamenti censiti come **Solo riferimento**; l'apertura di un bando non è implicita.

### Regole di qualità

Non classificare come `APERTO` un canale solo perché riceve richieste o mostra bandi storici. Non identificare il beneficiario di un contributo provinciale come finanziatore. Per i bandi comunali verificare la ricaduta territoriale, l'eventuale iscrizione all'albo e le finestre annuali; per le aziende distinguere sponsorizzazioni dirette da selezioni pubbliche. Sono ancora da ricercare e qualificare Province e Comuni non coperti e fondazioni/aziende senza una pagina ufficiale candidabile.

### Collaudi

- Validare `config/funders.json` e la suite completa.
- Dopo la scansione verificare i 10 programmi `direct`, il loro stato reale, i contatori di importazione e gli eventuali errori robots/redirect.
- Verificare che i 6 programmi `reference-only` siano indicati **Solo riferimento** e non falsamente come monitorati.
- Verificare che bandi comunali senza reale candidatura o di soggetti non ammissibili non generino falsi alert e che nuovi bandi verificati siano assegnati alla fonte e al programma corretti.
- Non alterare il filtro iniziale *Aperte*, le viste tabellari, i link numerici e le notifiche esistenti.

## Completamento censimento provinciale e altri Comuni (19 novembre 2026)

Il registro è ampliato a **49 finanziatori e 29 programmi/canali** (11 `direct`, 5 `existing-source`, 13 `reference-only`). Il censimento ora comprende tutti gli enti provinciali piemontesi (inclusa Città Metropolitana), ma **non dimostra che tutti pubblichino bandi a cui Opera+ possa presentare domanda**. I portali di trasparenza censiscono spesso contributi già deliberati, senza possibilità di candidatura.

### Fonti istituzionali aggiunte e modalità

| Ente | Fonte ufficiale | Classificazione | Motivazione |
| --- | --- | --- | --- |
| Provincia di Asti | https://www.provincia.asti.it/it | Solo riferimento | Portale istituzionale, senza bando culturale specifico verificato |
| Provincia di Biella | https://www.provincia.biella.it/ | Solo riferimento | Portale istituzionale; verificare eventuali avvisi pertinenti |
| Provincia di Cuneo | https://albo.provincia.cuneo.it/amministrazione-trasparente/sovvenzioni-contributi-sussidi-vantaggi-economici/criteri-modalita | Solo riferimento | Criteri/trasparenza; la pagina segnala assenza erogazioni nel periodo indicato |
| Provincia di Vercelli | https://servizi.provincia.vercelli.it/L190/contributo/lista?activePage=&idSezione=73&search=&sort= | Solo riferimento | Registro delle concessioni, non bandi aperti. Gli avvisi della Regione riportati dal sito non sono finanziamenti provinciali |
| Provincia del Verbano-Cusio-Ossola | https://www.provincia.verbano-cusio-ossola.it/servizio/erogazione-contributi-ad-enti-ed-associazioni-per-progetti-ed-iniziative-nel-campo-dellistruzione/ | Solo riferimento | Possibile canale per progetti educativi, requisiti da verificare |
| Città di Ivrea | https://servizionline.comune.ivrea.to.it/cmsivrea/portale/trasparenza/trasparenzaamministrativadettaglio.aspx?CDOC=956&CP=191&R=1 | Solo riferimento | Bando storico, non riapertura verificata; requisiti di anzianità presenti nelle edizioni passate |
| Città di Settimo Torinese | https://www.comune.settimo-torinese.to.it/it/news-category/133558?type=0 | Scansione diretta | Monitoraggio della pagina degli avvisi alle associazioni; il bando per eventi 2026 aveva scadenza già trascorsa |
| Città di Biella | https://comune.biella.it/trasparenza/sovvenzioni-contributi-sussidi-vantaggi-economici/ | Solo riferimento | Portale trasparenza non assimilabile a bando |

**Regole di riconciliazione:** una segnalazione della Provincia di Vercelli relativa a un bando regionale deve rimanere attribuita alla Regione Piemonte, e una pagina di trasparenza non può generare da sola nuove opportunità. Un titolo storico non prova che ci sia una finestra attiva. Quando vengono individuati veri bandi per enti senza sede nel Comune, valutare condizioni territoriali, destinatari e ricaduta dei progetti.

### Collaudi

- Confermare 49 finanziatori e 29 programmi, di cui 13 `reference-only`, senza erronee etichette di controllo riuscito.
- Verificare la prima scansione `direct` di Settimo Torinese, con gestione robots/redirect, eventuali link candidati e importazioni realmente verificate.
- Confermare che schede e-mail non siano create per concessioni pregresse, avvisi regionali ripubblicati o bandi comunali già scaduti.
- Testare ricerca e layout adattivo senza scroll orizzontale nella pagina Finanziatori e Monitoraggio programmi, senza regressioni sulla Dashboard.

## Revisione impaginazione tabelle

Le colonne non hanno più una larghezza minima imposta indipendentemente dalla finestra. Su desktop usano proporzioni specifiche per ciascuna tabella, consentendo il ritorno a capo di denominazioni lunghe. Fino a 640 px le intestazioni rimangono disponibili alla struttura semantica della tabella e ogni record dispone i cinque campi in righe compatte con etichette leggibili. Controllare anche nomi lunghi, link, indicatori di stato e date su schermi stretti.


## Monitoraggio tematico: Torino 2033 e opera lirica europea (novembre 2026)

Sono censiti i canali istituzionali Torino 2033, Fondazione per la Cultura Torino (pagina dedicata), FEDORA, Opera Europa, European Festivals Association/EFFEA, European Cultural Foundation e Creative Europe. L'elenco è configurato in `config/funders.json`; Comune di Torino, Fondazione per la Cultura e Creative Europe preesistenti sono riutilizzati, evitando doppie fonti di scoperta.

- `monitoring=direct`: controllo periodico condizionato da robots.txt, HTTPS e riuscita del fetch, con baseline silenziosa. Una modifica pagina **non** corrisponde a un bando aperto. Il crawler considera solo collegamenti candidati sullo stesso host; collegamenti verso portali esterni richiedono un'integrazione distinta.
- `monitoring=existing-source`: Creative Europe riutilizza la fonte `eucreative`; le nuove call passano attraverso valutazione e notifiche già implementate.
- Torino 2033 e Opera Europa sono soprattutto **programmi e canali di partenariato**: non attribuire loro erogazioni dirette senza un avviso ufficiale. FEDORA, EFFEA ed ECF richiedono verifica per ogni edizione, incluso il ruolo associativo e gli eventuali partner.
- Gli interessi tematici da usare nelle verifiche sono opera lirica, educazione musicale, giovani e scuole, diffusione culturale, accessibilità, digitale e cooperazione europea. Non attribuire un punteggio di adeguatezza a una semplice pagina di programma: valutare le singole opportunità con le regole operative esistenti.
- Non generare opportunità aperte dalle pagine istituzionali né comunicazioni email per semplici variazioni. Solo nuove opportunità effettive, valutate e riconciliate, passano nelle notifiche periodiche esistenti.

### Collaudi specifici
1. Verificare nella pagina Finanziatori le nuove organizzazioni e nella pagina Monitoraggio i sette programmi senza duplicati per Comune/Fondazione/Creative Europe.
2. Eseguire la suite `tests/test_funder_registry.py` e `tests/test_programme_monitor.py` e verificare che lo schema e gli ID restino validi.
3. Dopo il workflow di scansione verificare gli stati effettivi delle nuove pagine: `ok`, `error` o baseline; non presentare come monitorato un fetch fallito.
4. Controllare che la prima scansione non crei opportunità fittizie, che i link generici siano scartati e che i risultati siano deduplicati.
5. Controllare che le notifiche non partano per una sola variazione del contenuto e che opportunità vere seguano la valutazione di adeguatezza corrente.


## Verifica territoriale e distinzione dagli stati personali

Le opportunità comunali e provinciali non sono automaticamente compatibili con una associazione avente sede in un territorio diverso: occorre verificare il requisito **testuale e documentato** del bando per sede legale, sede operativa, attività pregressa, ricadute territoriali e partner. Quando il requisito esplicito di sede comunale indica un Comune differente da quello dichiarato nel profilo e il passo citato non ammette alternative, il confronto marca `potenzialmente_incompatibile`, limita l'adeguatezza a BASSA e impedisce di suggerire una candidatura diretta. Non è una certificazione legale: se il bando menziona ricadute locali o alternative, lo stato rimane `da_verificare` finché la prova specifica non è acquisita. Il caso Rivoli richiede quindi verifica delle diverse categorie ammesse, non un sì automatico e non un'esclusione basata sul solo ente emittente.

Lo stato iniziale del workflow personale è denominato «Da esaminare» (precedente «Da valutare»); riguarda soltanto la lavorazione delle opportunità seguite sul browser, **non** la copertura delle valutazioni del catalogo. I dati locali precedenti sono normalizzati in lettura.


## Riconciliazione catalogo del 19/11/2026

Snapshot preliminare (18/11 23:21 UTC): 264 schede, 34 aperte, 34 con workflow di controllo ammissibilità ancora aperto, 11 aperte di adeguatezza MEDIA, 23 BASSA; nessuna candidatura certificata come pienamente ammissibile. Gli altri giudizi editoriali non equivalgono a verifica puntuale di requisiti. La presenza di 1 scheda aperta con revisione incompleta è oggetto della riconciliazione automatica per ID pubblico stabile, con vincolo sull'ID della fonte; non si ricopia una recensione su un'altra opportunità.

- Schede con titoli generici «SCOPRI IL BANDO»: usare esclusivamente un titolo specifico già documentato in `config/assessment_reviews.json`, preservando identificativi e URL ufficiali.
- Fabbrica (#143): candidatura diretta non sostenibile allo stato documentato del RUNTS; possibile ruolo di partner solo secondo condizioni dell'avviso ufficiale. Non presentare come candidata diretta.
- Dora in Avanti (#175): verifica del requisito ETS e dell'operatività locale prima di consigliare candidatura; attenzione alla scadenza ravvicinata del 20/11/2026.
- Opportunità con sede obbligatoria in Comune diverso da Torino: rischio di incompatibilità, salvo alternative documentate (ricadute locali, progetto sul territorio, partner). Non dedurre vincoli provinciali dal solo nome dell'ente.
- Gli elementi rimasti privi di prova sui requisiti restano nella coda documentale, senza trasformare automaticamente in ammissibili record di adeguatezza ALTA/MEDIA.

**Verifica:** eseguire quality checks e la successiva scansione su `main`; confrontare `data/scan-status.json > catalog_reconciliation`, `assessment_coverage` e i record #143, #146, #175, #183, #188 e #189. La scansione aggiorna i dati, non può sostituire documenti non disponibili o una verifica giuridica della posizione dell'associazione.


## Valutazione obbligatoria all'acquisizione

Ogni scheda censita deve ricevere durante la stessa scansione un giudizio di adeguatezza (ALTA, MEDIA, BASSA o INFORMATIVA) e una motivazione. La pubblicazione **non si interrompe** per una scheda ancora priva di motivazione: prima di scrivere il catalogo viene assegnato automaticamente un giudizio prudenziale BASSA motivato, mantenendo la scheda e segnalando il fallback. Gli avvisi puramente informativi restano INFORMATIVA. Evidenze parziali producono un giudizio prudente, **non** uno stato editoriale «Da valutare». La verifica dei vincoli giuridici e dei beneficiari rimane separata e può essere indicata come non dimostrata, senza simulare l'ammissibilità. Lo stato personale «Da esaminare» riguarda esclusivamente la gestione del lavoro sulle opportunità seguite, non la valutazione del catalogo.


### Regola di continuità della pubblicazione (19/11/2026)
La valutazione editoriale incompleta non è motivo per fermare la scansione, scartare un record o sopprimere una candidatura. Un fallback BASSA segnala soltanto evidenze scarse e può essere rivalutato quando arriva documentazione. I record di tipo informativo restano INFORMATIVA. Le verifiche di ammissibilità giuridica sono separate, e non si trasforma la mancanza di prove in una esclusione. Gli errori infrastrutturali o d'integrità reali mantengono i propri controlli di sicurezza.

## Verifica documentale mirata — sette opportunità (19/11/2026)

Verifica svolta sulla fonte primaria di ciascun bando e confrontata con i soli dati dichiarati nel profilo associativo (costituzione 23/04/2026, sede legale Torino, RUNTS in corso, nessuna attività pregressa). Le valutazioni restano consultabili anche quando la candidatura diretta è esclusa; non cambiano artificialmente le date o lo stato ufficiale APERTO/CHIUSO.

| ID | Giudizio | Conclusione per Opera+ | Fonte primaria |
| --- | --- | --- | --- |
| 176 | BASSA | Capofila escluso: 3 anni di sede in Piemonte e esperienza ECG triennale non soddisfatti; partecipazione come partner di OSC ammessa in astratto ma requisiti specifici da confermare, co-proponente pubblico obbligatorio | https://bandi.regione.piemonte.it/contributi-finanziamenti/bando-educazione-alla-cittadinanza-globale-sostenibilita-solidarieta-internazionale-anno-2026 |
| 23 | MEDIA | Ente non profit con sede piemontese è tipologia prevista; occorre specifica manifestazione turistica con promozione, non un corso online generico, e domanda entro 24/11/2026 ore 12 | https://bandi.regione.piemonte.it/contributi-finanziamenti/lr-142016-art-20-contributi-iniziative-comunicazione-promo-pubblicita-nellambito-manifestazioni |
| 182 | BASSA | **Candidatura esclusa**, costituzione anteriore al 01/01/2024 e proventi 2025 >= 200.000 EUR obbligatori; partenariati vietati. Non basta interesse per l'AI | https://www.compagniadisanpaolo.it/it/contributi/bando-per-lo-sviluppo-di-strategie-e-percorsi-di-uso-responsabile-e-sicuro-dellintelligenza-artificiale-nelleconomia-sociale/ |
| 183 | MEDIA | Ammissibile come categoria di ente culturale del territorio, ma occorrono lavoratori/collaboratori contrattualizzati (linea A >= 1 anno, linea B neoassunti) oppure tirocinio extracurricolare con promotore (C). Non finanzia corso Rigoletto per il pubblico. Nessun destinatario documentato | https://www.compagniadisanpaolo.it/it/contributi/buoni-formazione-per-la-cultura/ |
| 19 | BASSA | **Candidatura esclusa**: riservato esclusivamente a Pro Loco iscritte ai registri al 01/01/2026; Opera+ non è una Pro Loco e ancora non era costituita | https://bandi.regione.piemonte.it/contributi-finanziamenti/avviso-pubblico-finanziamento-alle-associazioni-turistiche-pro-loco-piemonte-anno-2026 |
| 143 | BASSA | RUNTS richiesto alle associazioni ETS anche in partenariato (presenza componenti sportive RASD e sociali RUNTS). Opera+ con RUNTS in corso non ha un percorso associativo già ammissibile | https://www.sportesalute.eu/fabbrica.html |
| 255 | BASSA | Testo **originale** Allianz verificato: enti non profit legalmente costituiti in Italia, anche in partenariato. Nessuna anzianità minima generale espressa, ma esperienza documentata nel settore, capacità economico-organizzativa e progetto dedicato a destinatari fragili; senza esperienza pregressa Opera+ non dispone di sufficienti prove | https://umanamente.allianz.it/content/dam/onemarketing/azit/faum-it/call-for-ideas-2026/Call-for-Ideas-2026_FINAL2.pdf |

La scheda Allianz in precedenza poteva essere penalizzata erroneamente come se il requisito nazionale `sede legale in Italia` imponesse la sede in uno specifico Comune. Il comparatore ora distingue esplicitamente il riferimento nazionale/regionale da un obbligo municipale. Non si deduce alcuna ammissibilità legale positiva dal solo controllo.

La fonte Allianz è un PDF ufficiale, non un semplice articolo di aggregatore. L'aggiornamento mantiene l'URL della scheda importata per gli ID e i link esistenti, ma usa il PDF come fonte della valutazione. Controllare dopo scansione giudizio, motivazione, flag di esclusione diretta e attività ancora necessarie per ciascuno dei sette ID. La valutazione non annulla lo stato ufficiale del bando: «APERTO» non implica «AMMISSIBILE».


### Approfondimento fonti ufficiali: festival 2027 e Circoscrizione 7 (19/11/2026)

- **#190 — Festival partecipativi 2027:** fonte ufficiale https://www.compagniadisanpaolo.it/it/contributi/linee-guida-per-i-festival-partecipativi-2027/ . Il bando ammette solo festival già tenuti almeno una volta nei due anni precedenti ed esclude esplicitamente le prime edizioni; almeno alcune attività devono essere gratuite, la contribuzione è compresa fra 5.000 e 30.000 euro ed è al massimo il 40% dei costi. Le due finestre hanno termine 3 dicembre 2026 e 5 aprile 2027. Opera+ non ha dichiarato attività svolte: la candidatura come organizzatore di un festival nuovo non soddisfa il requisito dell'edizione 2027. Conservare la scheda con adeguatezza BASSA, ostacolo esplicito e possibile futura rivalutazione; non eliminarla.
- **#8 — Avviso Eventi culturali 2027 della Circoscrizione 7:** PDF ufficiale https://bandi.comune.torino.it/sites/default/files/allegati/avvisi/2026/4576/13_Avviso_Eventi_Culturali_2027.pdf . Prevede diverse categorie di associazioni e organismi no profit: alcune richiedono sede o attività in Torino e iscrizione al registro comunale, altre ammettono un'iniziativa rivolta alla comunità locale anche senza sede cittadina. Nessun requisito generalizzato di sede nella sola Circoscrizione 7. La candidatura richiede progetto culturale concreto, statuto e categoria soggettiva verificati; istanza online entro il 26 novembre 2026. L'iniziativa va attuata indipendentemente dal contributo. Restare MEDIA, con giudizio condizionato e requisiti specifici.

La classificazione serve a orientare le decisioni senza attestare ammissibilità legale. Il prossimo scan applica le revisioni, conserva gli ID e pubblica sempre ogni scheda valutata.

## Chiusura verifica operativa bandi #23 e #183 (19 novembre 2026)

**#23 — Regione Piemonte, art. 20 L.R. 14/2016, annualità 2026.** Il bando è aperto dal 2 novembre al **24 novembre 2026 ore 12:00**, con istanza FINDOM del rappresentante legale/delegato. Ammette associazioni senza scopo di lucro con sede legale in Piemonte, ma finanzia **comunicazione e promo-pubblicità** di una manifestazione/evento di valenza turistica realizzato nel 2026 in Piemonte, al più sino al 10 gennaio 2027 per eventi a cavallo d'anno. È previsto **un solo evento per soggetto**, anche di rilevanza locale. Il sito contiene bando (DD 603/2026), schema domanda e relazione di dettaglio obbligatoria nel formato scaricabile da FINDOM. Fonti: https://bandi.regione.piemonte.it/contributi-finanziamenti/lr-142016-art-20-contributi-iniziative-comunicazione-promo-pubblicita-nellambito-manifestazioni e https://servizi.regione.piemonte.it/catalogo/bandi-cultura-turismo-sport-finanziamenti-domande . Nel profilo del progetto non è documentata una manifestazione candidata: **la semplice idoneità della categoria associativa non basta**. Esito MEDIA condizionato, non domanda pronta. Non impostare d'ufficio un evento fittizio e non proporre il corso online autonomo come iniziativa turistica.

**#183 — Compagnia di San Paolo, Buoni formazione per la cultura.** Strumento **a sportello** con domanda ROL, sino a esaurimento fondi e **una richiesta per ente**. Beneficiari: enti culturali non profit con sede legale e/o operativa in Piemonte, Liguria o Valle d'Aosta. Le linee ammesse sono: A, personale/lavoratori o collaboratori in forza da almeno 1 anno (incompatibile con la recente costituzione dell'associazione al novembre 2026); B, dipendenti assunti da non più di 1 anno; C, tirocinio extracurricolare di giovani che hanno terminato gli studi da non oltre 12 mesi, con soggetto promotore e requisiti regionali, senza copertura del rimborso obbligatorio. Contributo **2.000–10.000 euro**, sino al 100% dei costi; sono richiesti destinatari nominativi, analisi dei fabbisogni, programma/cronoprogramma in una relazione descrittiva e piano economico. Attività a conclusione **entro settembre 2027**. Il cofinanziamento è un elemento valutativo, non dichiarato come condizione assoluta. Fonte: https://www.compagniadisanpaolo.it/it/contributi/buoni-formazione-per-la-cultura/ . Non sono documentati attuali contratti, assunzioni o un tirocinio qualificato dell'associazione: esito MEDIA **condizionato alla creazione reale di un percorso per destinatari ammissibili**; nessuna candidatura pronta e nessun finanziamento del corso lirico destinato al pubblico.

**Regole per il catalogo:** mantenere le due schede anche se non esiste un progetto candidabile ora. Non trasformare queste lacune in una certificazione di incompatibilità soggettiva generalizzata; distinguere sempre ente, iniziativa, beneficiari e tempi, con fonte e requisiti verificati. La valutazione di adeguatezza rimane MEDIA, senza promesse di concessione o ammissibilità finale.


### Approfondimento opportunità MEDIA: residenze, fondo beneficenza e Fondo Cattolica (19/11/2026)

- **#33 Culture Moves Europe – Residency Hosts 2026/27** (https://culture.ec.europa.eu/it/culture-moves-europe/call-for-residency-hosts): anche enti di nuova costituzione possono candidarsi se legalmente registrati e attivi nei settori culturali ammissibili. Una residenza reale richiede 1–5 residenti internazionali, mentor, alloggio, spazi, portfolio e CV. Non dedurre esclusione dall'età dell'associazione, ma non proporre il solo corso online come progetto ammissibile; termine 18/01/2027.
- **#177 Fondo di Beneficenza Intesa Sanpaolo** (https://group.intesasanpaolo.com/it/sociale/fondo-di-beneficenza/come-richiedere-un-contributo e https://group.intesasanpaolo.com/it/sociale/fondo-di-beneficenza/domande-frequenti): associazione non profit costituita e iscritta ad almeno un registro pubblico. **Il RUNTS non è obbligatorio**, ma la mera attribuzione di un codice fiscale o un'istanza RUNTS in corso non dimostrano l'iscrizione richiesta. Verificare statuto, atto costitutivo, procedure contabili e progetto a impatto sociale. Non certificare ammissibilità.
- **#252 Una mano a chi sostiene 2026/27** (https://www.unamanoachisostiene.it/ e https://www.unamanoachisostiene.it/fondazione-cattolica-una-mano-a-chi-sostiene-faqs-2026/): ammessi anche enti privati senza fini di lucro, non solo ETS. È richiesto un progetto **nuovo** con impatto sociale misurabile. Il contributo massimo è 20.000 euro, entro l'80% del budget, e viene liquidato dopo rendicontazione: occorrono copertura residua e liquidità anticipata. Termine fase iniziale 16/02/2027. Non attribuire falsamente inammissibilità per RUNTS in corso.

Conservare i giudizi editoriali MEDIA come pertinenza progettuale condizionata: i vincoli operativi non certificano ammissibilità. Tutte le opportunità rimangono censite anche se richiedono documenti aggiuntivi.

## Scheda opportunità: verifica requisiti Opera+ (19/11/2026)

La scheda di dettaglio presenta, **immediatamente prima dei pulsanti d'azione**, una sezione nativa `<details>` «Verifica requisiti Opera+», **chiusa per impostazione predefinita**. Anche da chiusa mostra il conteggio dei requisiti verificati, delle criticità e delle condizioni da verificare; quando non ci sono condizioni estratte, segnala la mancanza di documentazione, senza inventare requisiti o spunte.

Il contenuto utilizza esclusivamente `applicant_requirement_comparison` con categorie, motivazioni e fonti `https`; il blocco esplicito `direct_application_blocker`, ove presente, è segnalato distintamente come ostacolo alla candidatura diretta. Uno stato `compatibile` è descritto come verifica con fonte documentale, `potenzialmente_incompatibile` come criticità, `da_verificare` come verifica aperta. La classificazione resta **preliminare, mai attestazione di ammissibilità complessiva**; dati dichiarati non sono promossi a conferme e non si rimuovono opportunità. I link ufficiali sono filtrati tramite URL sicuri.

Non si aggiungono colonne alla tabella, non si modifica il motore di scansione e non si espongono dati privati del profilo Opera+ nel frontend. Dopo il merge è necessario pubblicare il frontend con il publisher unico di `jeckodevsite`, verificando vista mobile, apertura/chiusura via tastiera, fonti, conteggi e posizione rispetto alle azioni.


## Riconciliazione dei requisiti sull'intero catalogo (19/11/2026)

La scansione ricalcola `requirement_coverage_status` e `requirement_evidence_count` per **ogni scheda**, incluse quelle storiche e informative. Il report `requirement_reconciliation` contiene copertura per catalogo completo, opportunità aperte e aperte ALTA/MEDIA, oltre alla coda prioritaria `open_without_comparable_requirements`. Stati distinti: `confronti_documentati`, `ostacolo_documentato`, `senza_requisiti_confrontabili`, `avviso_informativo`.

Le lacune restano lacune: **nessuna spunta inventata**, nessuna eliminazione di opportunità, nessuna modifica alle valutazioni editoriali. Solo un confronto con requisito esplicito e URL HTTPS può essere contato come documentato. Un blocco di candidatura diretta già motivato è rilevato separatamente. Il controllo integrità riconcilia i conteggi con tutti i record; la mancanza di informazioni di fonte non blocca la pubblicazione.

Collaudo: suite qualità, scanner, conteggi coerenti, zero ID persi/duplicati, controllo della coda aperta senza requisiti confrontabili e dell'accordion nei casi con e senza evidenze. Il frontend già pubblicato legge il feed JSON GitHub, quindi non richiede nuovo SFTP.


### Requisiti prioritari e pubblicazione del backfill (19 novembre 2026)

Il workflow storico `history-backfill.yml` ora aggiunge al commit tutti i dati pubblici generati sotto `data/`: in precedenza il programma lasciava modifiche locali non salvate (in particolare il registro dei programmi) e `git rebase origin/main` falliva. Verificare con una nuova esecuzione e monitorare eventuali conflitti concorrenti.

Per le schede MEDIA #8 (registro comunale), #33 (registrazione dell'ente, alloggio e spazi di lavoro per la residenza) e #146 (quota residua coperta con risorse proprie) sono stati aggiunti riconoscimenti specifici e prudenti delle clausole già presenti nelle fonti revisionate. Nuova categoria `capacita_operativa` per non confondere l'ospitalità artistica con un partenariato. I singoli confronti rimangono `da_verificare` in assenza di documenti del richiedente. Nessuna esclusione o spunta verde automatica.


### Revisione requisiti aperti e race condition backfill (19 novembre 2026)

Il backfill storico aveva completato la raccolta ma fallito nel `git rebase origin/main` con conflitti nei JSON perché il checkout del job in coda era precedente all'ultimo commit della scansione ordinaria. Il workflow ora esegue `git fetch origin main; git reset --hard origin/main` **all'inizio del job effettivo, dopo l'acquisizione del gruppo `funding-scan`**, prima della scansione. Il backfill non viene più lanciato a ogni modifica di `src/scan.py`: resta disponibile il lancio manuale e l'avvio quando cambia il suo workflow. Un conflitto imprevisto resta un errore, non si sovrascrivono ciecamente dati più recenti. Verificare il completamento dell'esecuzione post-merge e del commit.

Revisione ufficiale delle opportunità aperte BASSA ancora prive di controlli confrontabili: **#25** è riservata agli Ambiti Territoriali Sociali (Regione Piemonte), **#32** è una mobilità per singoli artisti/professionisti (Commissione europea), **#148** premia progetti già attuati con impatto misurabile (Erase Indifference), **#162 e #254** richiedono manifestazioni storiche continuative da cinque anni (Ministero della Cultura). Le cinque schede conservano l'adeguatezza e indicano un ostacolo specifico alla **candidatura diretta**, con fonte primaria e possibile verifica di ruoli diversi se previsti: la difficoltà documentata non causa eliminazione. Per **#120**, l'avviso Erasmus+ richiede un consorzio di almeno cinque enti indipendenti di cinque paesi: requisito da verificare, non esclusione automatica, né spunta verde. Il catalogo e l'accordion devono distinguere questi casi dai requisiti ancora ignoti.

Fonti ufficiali: https://bandi.regione.piemonte.it/contributi-finanziamenti/presentazione-progetti-invecchiamento-attivo-parte-ambiti-territoriali-sociali ; https://culture.ec.europa.eu/culture-moves-europe/call-for-individual-mobility ; https://www.eraseindifference.org/challenge/ ; https://spettacolo.cultura.gov.it/bando-fondo-nazionale-rievocazione-storica-2027-attivazione-della-modulistica-online-per-la-presentazione-delle-domande-di-contributo/ ; https://erasmus-plus.ec.europa.eu/funding-opportunities/european-literacy-coalition-consortium-fpa-sga .
