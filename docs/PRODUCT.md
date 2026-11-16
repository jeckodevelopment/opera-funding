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
