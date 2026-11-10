# scripts

- `bootstrap.sh`: installa uv e dipendenze dentro la cartella (non tocca il sistema). Non aggiungere installazioni globali.
- `serve_mlx.sh`: avvia `mlx_lm.server` sui pesi in `../../models/...` (variabili `MODEL_DIR`, `PORT`). **Un solo modello alla volta** (32 GB).
- `download_model.sh`: scarica i pesi da Hugging Face con verifica sha256.
- `build_demo.py` è stato archiviato in `archive/agent-suite/scripts/` (rigenerava `demo-oracle`, vecchia suite). `gh_publish.sh`, `gh_trigger.sh`: GitHub CLI, **mai eseguiti davvero**: non darli per funzionanti.
- Gli script shell usano `set -euo pipefail`, non stampano chiavi e non scrivono fuori dalla cartella del progetto.

## Script del nuovo progetto (10 nov 2026)
- `fetch_zurich.py`: scarica i CSV CC0 della Città di Zurigo, **rilegge la licenza dall'API e rifiuta tutto ciò che non è `cc-zero`**, scrive `data/zurich/MANIFEST.json` (sha256). Rete solo qui (script di sviluppo). Cambiare i dati cambia gli sha256 e quindi i task.
- `zurich_spec.py` (modelli di domanda DE/FR/IT/EN + query gold, un dataset = uno schema = uno split) e `build_zurich_tasks.py` (genera `tasks/zurich/`, esegue ogni gold, scarta le istanze banali o ambigue; deterministico: il test lo verifica). `make zurich-tasks`.
- `build_regression_tasks.py` (set di regressione), `build_demo_sql.py` (demo con oracolo, `make demo`), `power_table.py` (tabelle di potenza del piano di analisi), `fetch_swissvotes.sh` (Swissvotes, CC BY 4.0, sha256 fissato; nessun task scritto).

## Da creare (serie W)
- (Gli strumenti sui pesi indipendenti dal metodo esistono: `src/agentbench/wsp.py`.) Script per **Hugging Face Jobs** (modifica dei pesi, LoRA), non ancora scritti: solo sviluppo (regola 2). Il token HF si legge da variabile d'ambiente, mai da file, log o messaggi; stampa solo ciò che serve e mai il token.
  Dichiara costi e durata di ogni job (servono per "Adaptation Cost").
- Conversione dei checkpoint modificati in MLX (controlla la sintassi con `mlx_lm convert --help`, non assumerla) e **hash sha256** di ogni checkpoint.
- Ogni script che scarica o scrive pesi lavora fuori dal repository (`../../models/`) e non li committa.
