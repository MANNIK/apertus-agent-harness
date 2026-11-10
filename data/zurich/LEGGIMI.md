# Istantanea dei dati della Città di Zurigo (CC0)

Fonte: Open Data Stadt Zürich, https://data.stadt-zuerich.ch/ . Ogni file è un dataset con licenza **CC0** (verificata dall'API del portale al momento dello scaricamento, vedi `MANIFEST.json`).
Il portale aggiorna i dati: questa è un'**istantanea** con sha256 per la riproducibilità. Non modificare i file a mano.
Rigenerare: `.venv/bin/python scripts/fetch_zurich.py --force` (cambierebbe gli sha256 e quindi i task: vedi `docs/dati.md`).
