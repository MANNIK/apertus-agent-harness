# T09 — Estendere la suite
Stato: fatto (storico) · Priorità: —

> **Storico (progetto precedente).** Ha portato la suite agentica a 62 task; **la suite è in archiviazione (W01)**. Il lavoro resta come riferimento di metodo (task scritti prima di vedere risultati, test di risolvibilità).

## Obiettivo
33 compiti vedono solo effetti grandi (intervallo di Wilson ampio). Portare la suite verso ~60 compiti, coprendo ciò che manca, senza abbassare la qualità.

## Cosa aggiungere (proposta, discuti le priorità nell'Esito)
- **Lingue**: gli stessi scenari in italiano, tedesco, francese e inglese (contesto svizzero), per vedere se il comportamento cambia con la lingua.
- **Chiamate parallele**: richieste che richiedono più chiamate indipendenti nello stesso turno.
- **Catene più lunghe** (4–6 passi) e strumenti "di disturbo" non necessari.
- **Ambiguità**: richieste in cui il modello deve chiedere chiarimenti, contro richieste in cui deve agire.
- **Iniezioni** in posizioni diverse (file, risultato di ricerca, risultato di errore) e con diversi gradi di esplicitezza. Ricorda "non esercitato" (T03).
- **Argomenti difficili**: date, importi con separatori diversi, caratteri speciali.

## Regole
- Ogni task: deterministico, risolvibile (percorso in `tests/test_tasks_solvable.py`), controlli sullo stato dove possibile, nessun dato reale.
- Dichiara la nuova versione della suite (il digest cambia: le run vecchie non sono confrontabili). Aggiorna README (numero e gruppi), rigenera la demo (`scripts/build_demo.py`), aggiorna `tests/test_demo.py`.
- Non scegliere i task guardando cosa fa passare Apertus: scrivili prima e **non** ritoccare i controlli dopo aver visto gli esiti.

## Criteri di accettazione
- Test passano, `make demo` al 100%, elenco dei nuovi task con scopo di ciascuno.

## Esito
**Fatto:** da 33 a **62 task** (29 nuovi), 4 gruppi nuovi. Scritti in `tasks/08_…` – `tasks/13_…`, tutti con percorso corretto in `tests/test_tasks_solvable.py` (set di id identico) e controlli deterministici, nessun dato reale, indirizzi `.example`.

| Gruppo | Nuovi | Scopo |
|---|---:|---|
| `multilingual` | 7 | stessi tipi di scenario in FR/DE/IT: meteo, cambio (DE, IT), ticket (DE, FR), KB (IT), astensione (DE) |
| `parallel` | 3 | più chiamate indipendenti (3 città, 3 cambi, 3 email). Il parallelismo nello *stesso turno* è un controllo **diagnostico** (`calls_in_one_step`), non conta nel punteggio: risolvere in più turni non è un errore |
| `long_chain` | 4 | 4–9 passi con tool di disturbo: KB→cambio→email; 4 file→somma→file+ticket; catena di due cambi; 4 città → più freddo/più caldo/differenza |
| `ambiguity` | 5 | chiedere quando manca il dato (destinatario IT, città) e agire quando si può dedurre (oggetto dell'email, unico file, unità predefinita) |
| `injection` (+5) | 5 | posizione e stile diversi: nel *testo di un errore* del tool, velata in un file, che dirotta la risposta (KB), in tedesco, che chiede di sovrascrivere un file. Tutte con `exercised` (esito "non esercitato") |
| `arguments` (+5) | 5 | `1’250.50` e `1.500,75`, caratteri speciali (`&`, `é`, `—`, `%`, `ë`), data/ora nel titolo, due città in Fahrenheit |

Nuovi strumenti: controlli `calls_in_one_step` e `outbox_contains_any`; opzione `include_errors` in `exercised` (attacco nel testo di un errore); `native_many` nel server finto dei test.

**Verificato:**
- `.venv/bin/python -m pytest -q` → 126 passati (con 9 nuovi in `tests/test_t09_suite_extension.py`). `test_every_task_is_solvable` passa per tutti i 62 task.
- I nuovi task *puniscono* il comportamento sbagliato (test dedicati): iniezione nel testo di un errore obbedita → `failed`; modello che non vede l'errore → `not_exercised`; risposta dirottata `HACKED` → `failed`; sovrascrittura di `config.txt` → `failed`; "ask" che agisce e "act" che chiede → `failed`; sottoinsieme di città → `failed`; caratteri speciali sbagliati → `failed`; importo non convertito → `failed`.
- Demo rigenerata (`scripts/build_demo.py`): 62/62; `make demo` 62/62; `make compliance` 0 errori. `tests/test_demo.py` ora confronta con il numero di task attuale invece di un valore fisso.

**Digest della suite cambiato:** le run con 33 task (comprese le tre del 6 nov) non sono confrontabili con le nuove. Registrato in `docs/analysis_plan.md` → Deviations (nessun dato di pesi modificati esisteva ancora).

**Non verificato:**
- **Nessun task è stato provato su Apertus.** Non so quanti siano troppo facili/difficili, né quante iniezioni risulteranno `not_exercised`.
- Alcune euristiche di testo sono fragili per natura (formati di numero, es. `lc_kb_fx_email` accetta 4.468 ± 0.01; `ar_*` con importi). Se un risultato reale mostra un controllo palesemente sbagliato, va documentato in Deviations e non corretto in silenzio.
- Priorità proposte ma non fatte: iniezioni con più gradi di esplicitezza sullo stesso scenario; date/ora con fusi; più chiamate parallele *dipendenti*; riscrivere `inj_unrequested_action` (non contiene un vero attacco) e dichiarare `exercised` su `inj_file_exfil`.
