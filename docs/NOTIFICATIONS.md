# Notifiche email gratuite — Opera+ Funding

## Architettura

Lo scanner è programmato **ogni giorno**, inclusi i fine settimana, con tre tentativi mattutini e un controllo di freschezza in orario Europe/Rome per evitare scansioni duplicate. Dopo la verifica d'integrità, `.github/workflows/scan.yml` **pubblica il JSON del catalogo**, poi esegue `python src/notify.py` e infine versiona il registro delle consegne. Il modulo invia un riepilogo separato per destinatario, senza esporre gli altri indirizzi. Sono candidabili alla notifica le nuove opportunità autentiche e catalogate negli stati APERTO, IN ARRIVO o DA VERIFICARE, con adeguatezza ALTA, MEDIA o BASSA. Le nuove schede non valutate restano nella coda d'istruttoria, fuori dal catalogo e dalle notifiche.

La prima esecuzione inizializza `data/notification-state.json` senza inviare tutte le opportunità storiche. Le esecuzioni successive confrontano lo stato delle schede con il registro, memorizzano gli identificativi già notificati e inviano le novità senza ripetizioni. Le informazioni pubblicate nel registro **non contengono indirizzi email, credenziali, token né dati personali dei destinatari**. Se un singolo invio fallisce, il registro tiene traccia dei destinatari già raggiunti (solo codici HMAC non reversibili senza chiave segreta), e nella scansione seguente riprova esclusivamente quelli non ancora raggiunti. La richiesta a Resend contiene una chiave di idempotenza per ridurre i doppi invii in caso di retry (garanzia del provider di 24 ore). Il registro deve restare sotto versionamento Git.

**Nessun invio** quando mancano novità, non sono configurati i due Secrets oppure è stato raggiunto il limite di sicurezza di 10 email effettive al giorno / 100 al mese (ogni destinatario conta come un invio). Le quote applicative sono volontariamente molto inferiori ai limiti del piano gratuito Resend (100 al giorno, 3.000 al mese). Il piano gratuito rimane una dipendenza esterna, da verificare periodicamente. La quota di Resend è condivisa con eventuali altri progetti dello stesso account: non garantiamo che un account già saturo possa inviare senza errori.

## Configurazione iniziale (richiesta una sola volta)

1. In [Resend](https://resend.com/api-keys), creare una API key con permesso **Sending access** sul dominio già verificato `updates.opera.plus`. Copiare la chiave una sola volta, **mai** nelle issue, nelle chat o nel repository.
2. Aprire la repository `jeckodevelopment/opera-funding` → **Settings → Secrets and variables → Actions** e aggiungere i seguenti **Repository secrets**:
   - `RESEND_API_KEY`: la chiave creata in Resend.
   - `FUNDING_ALERT_RECIPIENT`: uno o più indirizzi email privati, separati da virgola (oppure punto e virgola o a capo), ad esempio `persona1@example.org,persona2@example.org`. Massimo 10 destinatari, senza duplicati. Ogni destinatario riceve un messaggio **individuale**, senza conoscere gli altri indirizzi.
3. Il mittente applicativo predefinito è `Opera+ Funding <notifiche@updates.opera.plus>`; il sottodominio è verificato in Resend. L'alias mittente non richiede una casella di posta propria per **inviare**.
4. La prima esecuzione dopo l'installazione crea la baseline e **non invia email retroattive**. Una successiva scansione con un nuovo bando verificato APERTO invierà il primo riepilogo.

È possibile modificare i due Secrets in qualsiasi momento. Se un Secret è rimosso, non vengono più inviate email, ma la scansione e la pubblicazione della dashboard continuano. Non serve FTP per attivare il motore: i workflow funzionano interamente su GitHub Actions.

## Regole e collaudi

- Invio per le **nuove opportunità pertinenti** già ammesse al catalogo (APERTO, IN ARRIVO e DA VERIFICARE), mantenendo sempre esplicito lo stato; mai per gli avvisi informativi o le schede ancora in istruttoria.
- Nessuna email a ogni scansione in assenza di nuovi bandi. La rilevanza è una **stima**, non prova di ammissibilità; nell'email si rimanda alla fonte originale.
- Ogni messaggio riepilogativo comprende fino a 12 schede; più opportunità vengono inviate con più batch entro le quote. Gli elementi ALTA/MEDIA sono ordinati prima dei BASSA. Nessuna email è inviata soltanto per cambiamenti editoriali.
- In caso di errore del provider, non segnare le opportunità come inviate. I JSON pubblici vengono aggiornati anche se l'email fallisce: la failure del job deve essere visibile in Actions.
- Una fonte temporaneamente non disponibile non blocca la notifica di nuove schede verificabili provenienti dalle altre fonti; non vengono inventate conferme di apertura della fonte non disponibile.
- Eseguire `python -m unittest discover -s tests -v` e verificare le prove di baseline, duplicati, errori, escape HTML e limiti.
- Per collaudi manuali utilizzare un indirizzo destinatario di prova e una nuova opportunità testata in ambiente separato; non pubblicare opportunità fittizie nel catalogo pubblico.

**Privacy:** l'indirizzo destinatario è nel Secret GitHub; verrà trasmesso a Resend soltanto quando è necessario inviare l'email. Il registro pubblico contiene solo riferimenti a opportunità già pubbliche.

## Destinatari multipli

Il Secret mantiene il nome **`FUNDING_ALERT_RECIPIENT`** anche con più destinatari. Non bisogna creare più Secrets. Per ragioni di privacy i messaggi partono separatamente, e il registro pubblicato su GitHub contiene unicamente identificatori HMAC calcolati usando la chiave Resend come chiave segreta. Gli indirizzi non vengono stampati nei log o salvati nel repository. Le quote di sicurezza contano ogni messaggio individuale. Modificare l'elenco destinatari non comporta reinvio retroattivo dei bandi già notificati. Una rotazione della chiave Resend durante invii parzialmente completati cambia gli identificatori di consegna: verificare la coda prima di ruotare il Secret.

## Template grafico (17 novembre 2026)

Le email utilizzano il template condiviso `src/email_template.py`, ispirato alla dashboard: sfondo avorio `#f7f6f3`, schede bianche con bordi sottili, tipografia Georgia per i titoli, verde per lo stato APERTA, dettagli color oro. Il logo di Opera+ viene caricato da `https://jeckodevelopment.com/dev/funding/assets/operaplus-logo.png` con testo alternativo per i client che bloccano le immagini.

L'HTML usa tabelle di presentazione e stili inline (compatibilità con i principali client email), senza CSS remoto, JavaScript, tracking pixel o font esterni. Ogni scheda include ente, titolo, sintesi se disponibile, scadenza in italiano e collegamento HTTPS alla fonte; nessuna sintesi o scadenza viene inventata. È sempre disponibile una versione testuale.

L'anteprima di collaudo viene inviata una sola volta mediante un workflow temporaneo, con **bandi chiaramente fittizi**, oggetto `[ANTEPRIMA — BANDI FITTIZI]`, senza modificare il catalogo o il registro delle notifiche. Dopo aver verificato la ricezione, rimuovere `src/email_preview_once.py` e `.github/workflows/email-preview-once.yml`.

## Logo e dark mode

Il logo ufficiale ha lettering nero/oro e trasparenza. Per impedirne la perdita di contrasto nei client email in modalità scura, il template lo presenta sopra un riquadro bianco esplicito (`bgcolor`, `background-color` e gradiente bianco per i client che preservano i gradienti). Non viene cambiato il marchio. Il risultato effettivo può variare perché alcuni client applicano inversioni forzate: verificare il messaggio su Apple Mail e Gmail, sia in modalità chiara che scura.

## Verifica finale ordine pubblicazione e correttezza delle email (20/11/2026)

Il catalogo viene pubblicato **prima** di avvisare i destinatari: il link
sul titolo punta sempre alla scheda tramite l'ID numerico pubblico appena
reso disponibile su GitHub. Dopo l'invio il registro
`data/notification-state.json` è salvato in un commit **separato**.
Il passo usa esplicitamente `always()` con guardie sulla pubblicazione,
perché GitHub Actions altrimenti salterebbe automaticamente i passaggi
successivi a un errore. Questo secondo commit viene tentato anche in caso di invio parzialmente
fallito (senza inviare messaggi ulteriori): consente di preservare le
ricevute dei destinatari già raggiunti e riprendere soltanto quelli
rimasti in sospeso. In caso di errore della pubblicazione dati, il
workflow non invia nessuna email.

Il mittente resta Opera+ Funding tramite Resend; non si inviano email di
prova agli indirizzi reali durante i test automatizzati. Rimangono
invariati limiti, deduplicazione, registri HMAC e riservatezza.
Il testo di ogni opportunità usa un titolo collegato alla scheda
dettagliata e un link separato alla fonte ufficiale. Per i bandi
`rolling_confirmed=true` con evidenza HTTPS e senza data finale,
la dicitura è «A sportello — senza scadenza fissa», non «Da verificare».
Le scadenze non confermate continuano invece ad apparire «Da verificare».

Collaudi: `tests/test_notify.py` verifica il contenuto a sportello,
l'ordine dei passaggi pubblicazione/invio/registro, il doppio destinatario,
la ripresa dopo invio parziale, le quote e i collegamenti alle schede.
La CI completa (Python, JavaScript, JSON, build) resta obbligatoria.
