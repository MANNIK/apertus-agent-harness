#!/usr/bin/env bash
# Pubblica i risultati di una run su GitHub tramite la GitHub CLI (`gh`).
#
# Uso:
#   scripts/gh_publish.sh <run_dir> issue <numero>        commenta un'issue esistente
#   scripts/gh_publish.sh <run_dir> pr <numero>           commenta una pull request
#   scripts/gh_publish.sh <run_dir> new-issue "<titolo>"  apre una nuova issue con il report
#   scripts/gh_publish.sh <run_dir> release <tag>         allega results.jsonl e report.md a una release
#
# Variabili opzionali:
#   DRY_RUN=1   stampa i comandi `gh` invece di eseguirli (utile per controllare prima)
#   LABEL=nome  etichetta da applicare con new-issue (deve già esistere nel repo)
set -euo pipefail

if [[ $# -lt 3 ]]; then
  sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi

RUN_DIR=$1
MODE=$2
TARGET=$3
REPORT="$RUN_DIR/report.md"

# Esegue il comando, oppure lo stampa soltanto se DRY_RUN=1.
run() {
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    printf '+'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}

[[ -d "$RUN_DIR" ]] || { echo "cartella di run non trovata: $RUN_DIR" >&2; exit 1; }
# Se il report non esiste ancora, lo genera dai risultati.
[[ -f "$REPORT" ]] || agentbench report "$RUN_DIR" > /dev/null

case "$MODE" in
  issue)
    run gh issue comment "$TARGET" --body-file "$REPORT" ;;
  pr)
    run gh pr comment "$TARGET" --body-file "$REPORT" ;;
  new-issue)
    args=(gh issue create --title "$TARGET" --body-file "$REPORT")
    [[ -n "${LABEL:-}" ]] && args+=(--label "$LABEL")
    run "${args[@]}" ;;
  release)
    run gh release upload "$TARGET" "$RUN_DIR/results.jsonl" "$REPORT" --clobber ;;
  *)
    echo "modalità sconosciuta: $MODE (usa issue, pr, new-issue o release)" >&2
    exit 2 ;;
esac
