#!/usr/bin/env bash
# Avvia il server mlx-lm (API OpenAI-compatibile) con il modello scaricato nella cartella del progetto.
# Va lanciato sul Mac, in un terminale che resta aperto. Poi, in un altro terminale, usa l'harness.
#
# Uso:  scripts/serve_mlx.sh            (porta 8080)
#       PORT=8090 scripts/serve_mlx.sh
#       MODEL_DIR=/altro/percorso scripts/serve_mlx.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MODEL_DIR="${MODEL_DIR:-$HERE/../../models/apertus-v1.5-8b-mlx-bf16}"
PORT="${PORT:-8080}"

[[ -d "$MODEL_DIR" ]] || { echo "modello non trovato: $MODEL_DIR" >&2; exit 1; }
MODEL_DIR="$(cd "$MODEL_DIR" && pwd)"   # percorso assoluto e normalizzato
# Preferisce il venv del progetto (installato con `uv sync --extra mlx`): niente va fuori dalla cartella.
VENV_BIN="$HERE/../.venv/bin"
if [[ -x "$VENV_BIN/mlx_lm.server" ]]; then
  SERVER="$VENV_BIN/mlx_lm.server"
elif command -v mlx_lm.server >/dev/null; then
  SERVER="$(command -v mlx_lm.server)"
else
  echo "mlx-lm non trovato. Dalla cartella del progetto esegui:  uv sync --extra dev --extra mlx" >&2
  exit 1
fi

echo "Server su http://localhost:$PORT/v1"
echo "Nel terminale dell'harness esporta:"
echo "  export APERTUS_BASE_URL=http://localhost:$PORT/v1"
echo "  export APERTUS_MODEL=\"$MODEL_DIR\""
echo
exec "$SERVER" --model "$MODEL_DIR" --port "$PORT"
