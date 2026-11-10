#!/usr/bin/env bash
# Scarica il dataset Swissvotes (CC BY 4.0, Università di Berna / Année Politique Suisse) e verifica lo sha256.
# Licenza verificata il 2026-11-10 sulla pagina https://swissvotes.ch/page/dataset (vedi docs/dati.md).
# Attribuzione richiesta: cita Swissvotes come fonte (il testo di citazione raccomandato sta nei documenti scaricati).
#
# Uso:   scripts/fetch_swissvotes.sh [cartella_destinazione]      (predefinita: data/raw/swissvotes, ignorata da git)
#
# Il file sul sito viene aggiornato nel tempo: se lo sha256 cambia lo script FALLISCE di proposito (riproducibilità).
# In quel caso: guarda cosa è cambiato, aggiorna lo sha256 e la data in docs/dati.md, e rifai gli split.
set -euo pipefail

DEST=${1:-data/raw/swissvotes}
URL="https://swissvotes.ch/page/dataset/swissvotes_dataset.csv"
EXPECTED_SHA256="52a2d219521d5e03768084f1aff5ee20ab624ce9d3f8118e0ba3fa1290c3066e"   # scaricato il 2026-11-10, 2.736.956 byte
MAX_BYTES=52428800   # tetto di sicurezza: 50 MB

mkdir -p "$DEST"
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
curl -fsSL --retry 3 --max-time 180 --max-filesize "$MAX_BYTES" -o "$TMP" "$URL"
GOT=$(shasum -a 256 "$TMP" | awk '{print $1}')
if [[ "$GOT" != "$EXPECTED_SHA256" ]]; then
  echo "✗ sha256 diverso dal previsto." >&2
  echo "  atteso: $EXPECTED_SHA256" >&2
  echo "  ottenuto: $GOT" >&2
  echo "  Il file è stato aggiornato dal sito? Non l'ho salvato. Vedi l'intestazione dello script." >&2
  exit 1
fi
mv "$TMP" "$DEST/swissvotes_dataset.csv"
trap - EXIT
echo "✓ $DEST/swissvotes_dataset.csv (sha256 verificato)"
