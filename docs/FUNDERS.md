# Registro finanziatori e programmi

La gerarchia canonica è **finanziatore → programma → opportunità**. La fonte di verità versionata è `config/funders.json`; gli elementi già presenti in `config/sources.json` sono fonti di scoperta, non necessariamente erogatori.

- Ogni finanziatore ha un ID permanente, tipologia, territorio e stato di verifica. Un nome nel registro **non dimostra** che Opera+ sia ammissibile.
- Ogni programma identifica l'eventuale pagina ufficiale e un canale di candidatura; `monitoring=existing-source` indica il crawler già attivo. `monitoring=direct` è una **pagina censita ma non ancora scandita** e non deve essere visualizzata come controllata.
- Le opportunità vengono associate solo mediante `source_id` esplicito. Le opportunità provenienti da aggregatori (Vol.To) **non vengono attribuite** all'aggregatore come finanziatore; richiedono riconciliazione su fonte ufficiale.
- `scan-status.json` contiene il registro pubblico `funder_monitoring` con stato effettivo di controllo, senza dati riservati. I dati dell'associazione e le note operative restano fuori dal registro.
- I programmi senza un canale pubblico verificato sono anagrafica da approfondire, **non opportunità aperte**. Non inventare scadenze o creare schede opportunità da semplici pagine istituzionali.
- Per edizioni annuali e finestre multiple mantenere gli ID di opportunità già governati da `public_ids.py`; non usare il nome del programma come identificativo della candidatura.

## Evoluzioni da completare

1. Validare le pagine ufficiali di tutti i finanziatori e ampliare il censimento territoriale (Province e Comuni).
2. Estendere lo scanner con controlli sicuri e programmati per i programmi `direct`, con discovery di bandi effettivi e rilevamento modifiche.
3. Le viste pubbliche Finanziatori e Monitoraggio programmi sono implementate: utilizzano `scan-status.json > funder_monitoring`, espongono solo informazioni pubbliche e mantengono il filtro iniziale `Aperte`. Quando il report pubblicato è precedente all'introduzione del registro, mostrano un messaggio esplicito senza simulare la copertura.
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

**Limite di questa iterazione:** vengono monitorate le modifiche e individuati i link candidati, ma non viene ancora generata automaticamente una nuova scheda dal solo mutamento della pagina. Per creare un'opportunità serve un collegamento ufficiale, la verifica delle condizioni e il normale pipeline di adeguatezza, senza attribuire aperture fittizie. Non vengono inviate notifiche email per semplici variazioni della pagina.

### Collaudi aggiuntivi
- Eseguire `python -m unittest tests/test_programme_monitor.py` oppure la suite completa.
- Prima scansione: `baseline_created=true`, `changed=false` per pagine raggiungibili.
- Scansione successiva: `changed=true` solo se il contenuto rilevante cambia.
- Simulare robots.txt negato e verificare `error` senza cancellare la baseline.
