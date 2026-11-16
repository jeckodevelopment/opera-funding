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
