#!/usr/bin/env bash
# Scarica un modello da Hugging Face con curl e verifica gli SHA-256 dei file pesanti.
# Riprendibile: se si interrompe, rilanciarlo continua da dove si era fermato.
#
# Uso:   scripts/download_model.sh <repo_id> <cartella_destinazione> [revisione]
# Esempio:
#   scripts/download_model.sh tokimoa/apertus-v1.5-8b-mlx-bf16 ../models/apertus-v1.5-8b-mlx-bf16
#
# Non serve alcun token per i repository pubblici. Per quelli "gated" (es. swiss-ai/Apertus-v1.5-8B)
# usa invece `hf auth login` e `hf download`, dopo aver accettato le condizioni sul sito.
# Scarica sempre un commit preciso (la revisione viene risolta in uno SHA e salvata nel manifesto).
set -euo pipefail

if [[ $# -lt 2 ]]; then
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi
REPO=$1
DEST=$2
REV=${3:-main}
mkdir -p "$DEST"

# 1. Manifesto: nome, dimensione e sha256 di ogni file, alla revisione richiesta.
META=$(mktemp)
curl -fsS --retry 3 "https://huggingface.co/api/models/$REPO/revision/$REV?blobs=true" -o "$META"
python3 - "$META" > "$DEST/.manifest.tsv" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print("#sha\t" + d["sha"])
for s in d["siblings"]:
    print("\t".join([s["rfilename"], str(s.get("size") or 0), (s.get("lfs") or {}).get("sha256", "")]))
PY
rm -f "$META"
SHA=$(awk -F'\t' '$1=="#sha"{print $2}' "$DEST/.manifest.tsv")
echo "repo: $REPO  revisione: $SHA"

sha256_of() {  # Linux: sha256sum, macOS: shasum
  if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi
}
size_of() { wc -c < "$1" | tr -d ' '; }

# 2. Scarica ogni file (curl -C - riprende un download parziale), poi controlla dimensione e hash.
while IFS=$'\t' read -r FILE SIZE HASH; do
  [[ "$FILE" == "#sha" ]] && continue
  mkdir -p "$DEST/$(dirname "$FILE")"
  if [[ -f "$DEST/$FILE" && "$(size_of "$DEST/$FILE")" == "$SIZE" ]]; then
    echo "già presente: $FILE"
  else
    echo "scarico: $FILE ($SIZE byte)"
    curl -fL -C - --retry 5 --retry-delay 5 --retry-connrefused \
      -o "$DEST/$FILE.part" "https://huggingface.co/$REPO/resolve/$SHA/$FILE"
    mv "$DEST/$FILE.part" "$DEST/$FILE"
  fi
  if [[ "$(size_of "$DEST/$FILE")" != "$SIZE" ]]; then
    echo "ERRORE dimensione: $FILE" >&2; exit 1
  fi
  if [[ -n "$HASH" ]]; then
    MARK="$DEST/.verified.${FILE//\//_}"   # segno "già verificato": evita di ricalcolare l'hash a ogni ripresa
    if [[ -f "$MARK" && "$(cat "$MARK")" == "$HASH" ]]; then
      echo "sha256 già verificato: $FILE"
    elif [[ "$(sha256_of "$DEST/$FILE")" == "$HASH" ]]; then
      echo "$HASH" > "$MARK"; echo "sha256 ok: $FILE"
    else
      echo "ERRORE sha256: $FILE" >&2; exit 1
    fi
  fi
done < "$DEST/.manifest.tsv"
echo "COMPLETATO: $DEST"
