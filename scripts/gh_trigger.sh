#!/usr/bin/env bash
# Lancia la workflow di valutazione su GitHub Actions, aspetta che finisca e scarica i risultati.
#
# Uso:
#   scripts/gh_trigger.sh <base_url> <model> [repeats] [issue_da_commentare]
#
# Esempio:
#   scripts/gh_trigger.sh https://mio-server.example/v1 swiss-ai/Apertus-v1.5-8B 3 12
#
# Il runner di GitHub deve poter raggiungere <base_url>: un server esposto su Internet o un
# runner self-hosted (imposta RUNNER=self-hosted). `localhost` del tuo Mac NON è raggiungibile
# dai runner ospitati da GitHub.
#
# Variabili opzionali:  RUNNER (default ubuntu-latest) · DRY_RUN=1 stampa i comandi senza eseguirli
set -euo pipefail

if [[ $# -lt 2 ]]; then
  sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi

BASE_URL=$1
MODEL=$2
REPEATS=${3:-1}
ISSUE=${4:-}
RUNNER=${RUNNER:-ubuntu-latest}
WORKFLOW=eval.yml

run() {
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    printf '+'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}

# 1. Avvia la workflow con gli input richiesti.
run gh workflow run "$WORKFLOW" \
  -f base_url="$BASE_URL" -f model="$MODEL" -f repeats="$REPEATS" \
  -f issue="$ISSUE" -f runner="$RUNNER"

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "+ (poi: gh run list / gh run watch / gh run download)"
  exit 0
fi

# 2. Recupera l'id della run appena creata (la più recente di questa workflow).
sleep 5
RUN_ID=$(gh run list --workflow "$WORKFLOW" --limit 1 --json databaseId --jq '.[0].databaseId')
echo "run id: $RUN_ID"

# 3. Segue l'esecuzione; con --exit-status il comando fallisce se la run fallisce.
gh run watch "$RUN_ID" --exit-status || echo "la run non è andata a buon fine: scarico comunque gli artefatti"

# 4. Scarica i risultati in runs/ci-<id>.
gh run download "$RUN_ID" -D "runs/ci-$RUN_ID"
echo "risultati in runs/ci-$RUN_ID"
