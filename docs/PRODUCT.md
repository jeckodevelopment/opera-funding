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

## Prossimi incrementi
1. Verifica manuale e ampliamento del registro delle fonti, con connettori specifici per portali dinamici/API.
2. Estrazione affidabile di scadenza, importo e requisiti da pagine dettaglio e documenti ufficiali.
3. Classificazione approfondita e spiegabile; valutazione ammissibilità e potenziale progetto ad hoc.
4. Filtri completi, storico e notifiche email.
5. Deploy SFTP su jeckodevelopment.com/dev/funding con secrets GitHub.
