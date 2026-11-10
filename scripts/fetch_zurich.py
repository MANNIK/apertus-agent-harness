"""Scarica i dataset CSV scelti dal portale Open Data della Città di Zurigo e scrive `data/zurich/MANIFEST.json`.

Per ogni dataset rilegge la licenza dall'API ufficiale (`package_show`) e **si rifiuta di scaricare se non è `cc-zero`** (CC0).
Registra fonte, licenza, impronta sha256, dimensione e data di scaricamento. I file restano in `data/zurich/` e, essendo CC0 e piccoli,
vengono committati come istantanea (il portale li aggiorna: l'istantanea garantisce la riproducibilità; vedi docs/dati.md).

Uso:  .venv/bin/python scripts/fetch_zurich.py [--force]
Rete: solo questo script di sviluppo (non fa parte del pacchetto `agentbench`, che non importa librerie di rete oltre a httpx nel client).
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "zurich"
API = "https://data.stadt-zuerich.ch/api/3/action/package_show?id="
PAGE = "https://data.stadt-zuerich.ch/dataset/"
UA = "agentbench-data-fetch/0.1"
MAX_BYTES = 8_000_000

# (nome del dataset nel portale, nome del file CSV scelto tra le risorse; None = l'unica risorsa CSV)
DATASETS: list[tuple[str, str | None]] = [
    ("bev_bestand_jahr_quartier_od3240", None),
    ("bev_bestand_jahr_kreis_od3242", None),
    ("bev_bestand_jahr_konfession_od3160", None),
    ("bau_whg_mpe_mietpreis_raum_zizahl_gn_jahr_od5161", None),
    ("bau_best_whg_zizahl_jahr_od5062", None),
    ("fd_median_einkommen_quartier_od1003", None),
    ("politik_abstimmungen_seit1933", None),
    ("ugz_luftschadstoffmessung_tageswerte", "ugz_ogd_air_d1_2025.csv"),
    ("ugz_meteodaten_tagesmittelwerte", "ugz_ogd_meteo_d1_2025.csv"),
    ("prd_ssz_fz_motorisierungsgrad_jahr_quartier_od2005", None),
    ("sd_sod_sozialhilfequote_stadtquartier", None),
    ("wir_preise_zik_totalindex_monatswerte_od6001", None),
    ("erz_sr_kennzahlen", None),
    ("sid_srz_od1027_feuerwehr_ausrueckzeit_jahr_stadtkreis", None),
    ("sid_srz_od1036_hilfsfristen_rettungsdienste_jahr_stadtkreis", None),
]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise RuntimeError(f"file oltre {MAX_BYTES} byte: {url}")
    return data


def main() -> int:
    force = "--force" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, wanted in DATASETS:
        pkg = json.loads(get(API + urllib.parse.quote(name)))["result"]
        if pkg.get("license_id") != "cc-zero":
            print(f"✗ {name}: licenza {pkg.get('license_id')!r}, non CC0: NON scaricato", file=sys.stderr)
            return 1
        csvs = [r for r in pkg["resources"] if (r.get("format") or "").upper() == "CSV"]
        if wanted:
            csvs = [r for r in csvs if r["url"].split("/")[-1] == wanted]
        if len(csvs) != 1:
            print(f"✗ {name}: attese 1 risorsa CSV, trovate {len(csvs)} ({[r['url'].split('/')[-1] for r in csvs]})", file=sys.stderr)
            return 1
        res = csvs[0]
        fname = f"{name}.csv"
        dest = OUT / fname
        if dest.exists() and not force:
            data = dest.read_bytes()
            how = "già presente"
        else:
            data = get(res["url"])
            dest.write_bytes(data)
            how = "scaricato"
        manifest.append({
            "dataset": name,
            "title": pkg.get("title"),
            "license_id": pkg["license_id"],
            "license_title": pkg.get("license_title"),
            "source_page": PAGE + name,
            "resource_url": res["url"],
            "resource_file": res["url"].split("/")[-1],
            "file": f"data/zurich/{fname}",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "portal_metadata_modified": pkg.get("metadata_modified"),
            "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        print(f"✓ {name:<62} {len(data):>9} byte  {how}")
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "LEGGIMI.md").write_text(
        "# Istantanea dei dati della Città di Zurigo (CC0)\n\n"
        "Fonte: Open Data Stadt Zürich, https://data.stadt-zuerich.ch/ . Ogni file è un dataset con licenza **CC0** (verificata dall'API del portale al momento dello scaricamento, vedi `MANIFEST.json`).\n"
        "Il portale aggiorna i dati: questa è un'**istantanea** con sha256 per la riproducibilità. Non modificare i file a mano.\n"
        "Rigenerare: `.venv/bin/python scripts/fetch_zurich.py --force` (cambierebbe gli sha256 e quindi i task: vedi `docs/dati.md`).\n",
        encoding="utf-8")
    print(f"\n{len(manifest)} dataset → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
