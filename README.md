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

Il workflow `.github/workflows/deploy.yml` prova a distribuire il sito su SFTP solo dopo l'esito positivo di tutti i test dashboard, usando i GitHub Secrets `SFTP_HOST`, `SFTP_USERNAME`, `SFTP_REMOTE_DIR`, `SFTP_KNOWN_HOSTS` e uno tra `SFTP_PASSWORD` o `SFTP_PRIVATE_KEY`; `SFTP_PORT` è una variabile facoltativa. La chiave host è verificata e la pubblicazione non cancella file remoti. Un errore di configurazione blocca il deploy e compare in Actions; non implica che il sito sia stato aggiornato. Le scansioni e le notifiche Resend restano separate.
