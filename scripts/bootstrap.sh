#!/usr/bin/env bash
# Prepara l'ambiente Python del progetto SENZA sporcare il Mac.
#
# Cosa fa:
#   1. Se `uv` non c'è, lo scarica (installer ufficiale astral.sh) dentro  .uv/bin  del progetto.
#   2. Cache di uv e, se serve, Python stesso vanno dentro  .uv/  (non in ~/.cache, non in ~/.local).
#   3. Crea  .venv/  nel progetto e ci installa harness, pytest, mlx-lm e duckdb.
#
# Cosa NON fa: non modifica .zshrc / .zprofile / PATH, non usa sudo, non installa nulla a
# livello globale. Per disinstallare tutto basta cancellare le cartelle  .venv  e  .uv.
#
# Uso (dalla cartella del progetto):   scripts/bootstrap.sh
# Poi si lavora senza uv:               .venv/bin/agentbench smoke
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Tutto ciò che uv scrive di suo resta in .uv/ (cache e installazioni di Python).
export UV_CACHE_DIR="$ROOT/.uv/cache"
export UV_PYTHON_INSTALL_DIR="$ROOT/.uv/python"
# Impedisce all'installer di aggiungere righe ai file di configurazione della shell.
export UV_NO_MODIFY_PATH=1

LOCAL_UV="$ROOT/.uv/bin/uv"

if [ -x "$LOCAL_UV" ]; then
  UV="$LOCAL_UV"
elif command -v uv >/dev/null 2>&1; then
  UV="$(command -v uv)"
  echo "uv già presente ($UV): lo uso, ma cache e Python restano in .uv/"
else
  echo "uv non trovato: lo installo in $ROOT/.uv/bin (solo dentro il progetto)..."
  mkdir -p "$ROOT/.uv"
  INSTALLER="$ROOT/.uv/install.sh"
  curl -LsSf -o "$INSTALLER" https://astral.sh/uv/install.sh
  # UV_UNMANAGED_INSTALL = cartella di destinazione, senza toccare PATH né file della shell.
  UV_UNMANAGED_INSTALL="$ROOT/.uv/bin" sh "$INSTALLER"
  rm -f "$INSTALLER"
  UV="$LOCAL_UV"
fi

echo "uv: $("$UV" --version)"

# Crea .venv e installa le dipendenze del progetto (se serve scarica un Python >= 3.10 in .uv/python).
"$UV" sync --extra dev --extra mlx --extra sql

cat <<MSG

Fatto. Tutto è dentro: $ROOT
  .venv/   ambiente Python del progetto
  .uv/     uv, la sua cache e (se serve) Python

Da ora in poi non serve più uv:
  scripts/serve_mlx.sh                  # terminale A: avvia il server del modello
  .venv/bin/agentbench smoke            # terminale B (dopo gli export stampati da serve_mlx.sh)
  .venv/bin/python -m pytest -q         # test dell'harness
MSG
