# Notifiche email gratuite — Opera+ Funding

## Architettura

Lo scanner programmato (lunedì, mercoledì, venerdì alle 06:00 UTC) produce i due JSON del catalogo; subito dopo `.github/workflows/scan.yml` esegue `python src/notify.py`. Il modulo genera **una sola email riepilogativa** per esecuzione, ma soltanto quando riconosce nuove opportunità confermate APERTE e potenzialmente pertinenti (categoria finanziamento/call, punteggio di ricerca almeno 50, collegamento raggiungibile ed evidenza di apertura).

La prima esecuzione inizializza `data/notification-state.json` senza inviare tutte le opportunità storiche. Le esecuzioni successive confrontano lo stato delle schede con il registro, memorizzano gli identificativi già notificati e inviano le novità senza ripetizioni. Le informazioni pubblicate nel registro **non contengono indirizzi email, credenziali, token né dati personali dei destinatari**. Se l'invio fallisce, gli eventi restano non notificati e verranno riproposti alla scansione seguente. La richiesta a Resend contiene una chiave di idempotenza per ridurre i doppi invii in caso di retry (garanzia del provider di 24 ore). Il registro deve restare sotto versionamento Git.

**Nessun invio** quando una fonte della scansione è fallita, non ci sono novità, non sono configurati i due Secrets, oppure è stato raggiunto il limite di sicurezza di 10 email al giorno / 100 al mese. Le quote applicative sono volontariamente molto inferiori ai limiti del piano gratuito Resend (100 al giorno, 3.000 al mese). Il piano gratuito rimane una dipendenza esterna, da verificare periodicamente. La quota di Resend è condivisa con eventuali altri progetti dello stesso account: non garantiamo che un account già saturo possa inviare senza errori.

## Configurazione iniziale (richiesta una sola volta)

1. In [Resend](https://resend.com/api-keys), creare una API key con permesso **Sending access** sul dominio già verificato `updates.opera.plus`. Copiare la chiave una sola volta, **mai** nelle issue, nelle chat o nel repository.
2. Aprire la repository `jeckodevelopment/opera-funding` → **Settings → Secrets and variables → Actions** e aggiungere i seguenti **Repository secrets**:
   - `RESEND_API_KEY`: la chiave creata in Resend.
   - `FUNDING_ALERT_RECIPIENT`: indirizzo email privato che deve ricevere le notifiche.
3. Il mittente applicativo predefinito è `Opera+ Funding <notifiche@updates.opera.plus>`; il sottodominio è verificato in Resend. L'alias mittente non richiede una casella di posta propria per **inviare**.
4. La prima esecuzione dopo l'installazione crea la baseline e **non invia email retroattive**. Una successiva scansione con un nuovo bando verificato APERTO invierà il primo riepilogo.

È possibile modificare i due Secrets in qualsiasi momento. Se un Secret è rimosso, non vengono più inviate email, ma la scansione e la pubblicazione della dashboard continuano. Non serve FTP per attivare il motore: i workflow funzionano interamente su GitHub Actions.

## Regole e collaudi

- Invio **solo** quando una nuova scheda diventa confermata APERTA; non inviare annunci di contenuti informativi, opportunità DA VERIFICARE o scadute.
- Nessuna email a ogni scansione in assenza di nuovi bandi. La rilevanza è una **stima**, non prova di ammissibilità; nell'email si rimanda alla fonte originale.
- Un riepilogo comprende fino a 12 schede, con conteggio delle eventuali altre. Nessuna email è inviata per cambiamenti editoriali privi di una nuova apertura confermata.
- In caso di errore del provider, non segnare le opportunità come inviate. I JSON pubblici vengono aggiornati anche se l'email fallisce: la failure del job deve essere visibile in Actions.
- La scansione **non può inviare** se un'origine risulta non disponibile.
- Eseguire `python -m unittest discover -s tests -v` e verificare le prove di baseline, duplicati, errori, escape HTML e limiti.
- Per collaudi manuali utilizzare un indirizzo destinatario di prova e una nuova opportunità testata in ambiente separato; non pubblicare opportunità fittizie nel catalogo pubblico.

**Privacy:** l'indirizzo destinatario è nel Secret GitHub; verrà trasmesso a Resend soltanto quando è necessario inviare l'email. Il registro pubblico contiene solo riferimenti a opportunità già pubbliche.
