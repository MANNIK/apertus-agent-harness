# scripts

- `bootstrap.sh`: installa uv e dipendenze dentro la cartella (non tocca il sistema). Non aggiungere installazioni globali.
- `serve_mlx.sh`: avvia `mlx_lm.server` sui pesi in `../../models/...` (variabili `MODEL_DIR`, `PORT`).
- `download_model.sh`: scarica i pesi da Hugging Face con verifica sha256.
- `build_demo.py`: rigenera `reference_runs/demo-oracle` (sintetica). `gh_publish.sh`, `gh_trigger.sh`: GitHub CLI, **mai eseguiti davvero**: non darli per funzionanti.
- Gli script shell usano `set -euo pipefail`, non stampano chiavi e non scrivono fuori dalla cartella del progetto.
