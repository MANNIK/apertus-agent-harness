# scripts

- `bootstrap.sh`: installa uv e dipendenze dentro la cartella (non tocca il sistema). Non aggiungere installazioni globali.
- `serve_mlx.sh`: avvia `mlx_lm.server` sui pesi in `../../models/...` (variabili `MODEL_DIR`, `PORT`). **Un solo modello alla volta** (32 GB).
- `download_model.sh`: scarica i pesi da Hugging Face con verifica sha256.
- `build_demo.py`: rigenera `reference_runs/demo-oracle` (sintetica, vecchia suite). `gh_publish.sh`, `gh_trigger.sh`: GitHub CLI, **mai eseguiti davvero**: non darli per funzionanti.
- Gli script shell usano `set -euo pipefail`, non stampano chiavi e non scrivono fuori dalla cartella del progetto.

## Da creare (serie W; non esistono ancora)
- Script per **Hugging Face Jobs** (modifica dei pesi, LoRA): solo sviluppo (regola 2). Il token HF si legge da variabile d'ambiente, mai da file, log o messaggi; stampa solo ciò che serve e mai il token.
  Dichiara costi e durata di ogni job (servono per "Adaptation Cost").
- Conversione dei checkpoint modificati in MLX (controlla la sintassi con `mlx_lm convert --help`, non assumerla) e **hash sha256** di ogni checkpoint.
- Ogni script che scarica o scrive pesi lavora fuori dal repository (`../../models/`) e non li committa.
