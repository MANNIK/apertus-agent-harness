"""Genera i task Text-to-SQL "zurich-sql" dai dati reali CC0 (data/zurich/) e dalle specifiche di `zurich_spec.py`.

Deterministico: stessi dati + stesse specifiche + stesso `--n` → stessi file (nessun timestamp, campionamento con seme fisso).
Per ogni istanza: i parametri vengono campionati dai dati reali, la query gold viene ESEGUITA e l'istanza è scartata se il risultato è vuoto,
nullo, a zero (per i conteggi), troppo grande, o se la risposta non è unica (pareggio in testa). Nessun LLM nel punteggio.

Scrive:  tasks/zurich/{dev,val,test}/<schema>.yaml  e  tasks/zurich/SPLITS.json (conteggi, impronte sha256 dei file e dei dati).

Uso:  .venv/bin/python scripts/build_zurich_tasks.py [--n-dev 3 --n-val 3 --n-test 3]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from zurich_spec import DATASETS, MONTHS, READ_TYPES, TEMPLATES, Tpl  # noqa: E402

LANGS = ["de", "fr", "it", "en"]
OUT = ROOT / "tasks" / "zurich"
DATA = ROOT / "data" / "zurich"
MAX_ROWS = 30


def lit(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def init_sql(short: str, placeholder: bool) -> str:
    _, _, file, table, select = DATASETS[short]
    base = "{DATA}" if placeholder else str(ROOT / "data")
    types = f", types={READ_TYPES[short]}" if short in READ_TYPES else ""
    return f"CREATE TABLE {table} AS SELECT {select} FROM read_csv('{base}/zurich/{file}.csv', header=true, sample_size=-1{types})"


def fmt_value(v, lang: str) -> str:
    if isinstance(v, date):
        return v.isoformat() if lang == "en" else v.strftime("%d.%m.%Y")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def render(tpl: Tpl, lang: str, row: dict) -> str:
    vals = {k: fmt_value(v, lang) for k, v in row.items()}
    if "m" in row:
        vals["mon"] = MONTHS[lang][int(row["m"]) - 1]
    return tpl.q[lang].format(**vals)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(n_by_split: dict[str, int]) -> dict[str, dict[str, list[dict]]]:
    out: dict[str, dict[str, list[dict]]] = {"dev": {}, "val": {}, "test": {}}
    manifest = {m["dataset"]: m for m in json.loads((DATA / "MANIFEST.json").read_text(encoding="utf-8"))}
    lang_counter = 0
    for short, (group, split, file, table, _) in DATASETS.items():
        assert manifest[file]["license_id"] == "cc-zero", file
        assert sha256_file(DATA / f"{file}.csv") == manifest[file]["sha256"], f"sha256 diverso per {file}"
        con = duckdb.connect()
        con.execute(init_sql(short, placeholder=False))
        setup = {"sql_init": [init_sql(short, placeholder=True)]}  # stesso oggetto per tutti i task dello schema (ancora YAML)
        tasks: list[dict] = []
        for tpl in TEMPLATES[short]:
            cur = con.execute(tpl.params.format(T=table))
            names = [d[0] for d in cur.description]
            cands = [dict(zip(names, r)) for r in cur.fetchall()]
            cands.sort(key=lambda r: tuple(str(v) for v in r.values()))  # DuckDB non garantisce l'ordine: senza questo il campione cambia a ogni run
            rnd = random.Random(f"{short}:{tpl.key}")
            rnd.shuffle(cands)
            picked, seen_first, seen_q = [], set(), set()
            n = n_by_split[split]
            for relaxed in (False, True):  # prima parametri con primo valore distinto, poi si rilassa
                for row in cands:
                    if len(picked) >= n:
                        break
                    if any(row is p[0] for p in picked):
                        continue
                    first = tuple(row.values())[0]
                    if not relaxed and first in seen_first:
                        continue
                    sqlp = {k: lit(v) for k, v in row.items()}
                    try:
                        gold = tpl.gold.format(T=table, **sqlp)
                        res = con.execute(gold).fetchall()
                    except Exception as e:  # una specifica scritta male deve far fallire la generazione, non passare in silenzio
                        raise SystemExit(f"[{short}/{tpl.key}] gold non eseguibile: {e}\n{gold}")
                    if not res or len(res) > MAX_ROWS or all(all(v is None for v in r) for r in res):
                        continue
                    if len(res) == 1 and len(res[0]) == 1 and res[0][0] == 0:
                        continue  # conteggi a zero: domande banali
                    if tpl.tie and not con.execute(tpl.tie.format(T=table, **sqlp)).fetchone()[0]:
                        continue
                    lang = LANGS[lang_counter % 4]
                    q = render(tpl, lang, row)
                    if q in seen_q:
                        continue
                    seen_q.add(q)
                    seen_first.add(first)
                    lang_counter += 1
                    picked.append((row, gold, res, lang, q))
            if len(picked) < n:
                print(f"  ! {short}/{tpl.key}: solo {len(picked)} istanze su {n} richieste", file=sys.stderr)
            for i, (row, gold, res, lang, q) in enumerate(picked, 1):
                checks: list[dict] = [{"type": "sql_result_match", "gold": gold, **({"order_matters": True} if tpl.order else {})}]
                if len(res) == 1 and len(res[0]) == 1 and isinstance(res[0][0], (int, float)) and not isinstance(res[0][0], bool):
                    v = res[0][0]
                    checks.append({"type": "final_number", "value": float(v), "tol": 0.06 if float(v) != int(v) else 0.0})
                meta = {"language": lang, "schema_id": short, "dataset": file, "split": split, "group": group, "template": tpl.key}
                if tpl.trap:
                    meta["trap"] = tpl.trap
                tasks.append({"id": f"{short}_{tpl.key}_{i}", "category": tpl.cat, "prompt": q, "tools": ["run_sql"],
                              "setup": setup, "max_steps": 6, "meta": meta, "checks": checks})
        con.close()
        out[split][short] = tasks
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-dev", type=int, default=3)
    ap.add_argument("--n-val", type=int, default=3)
    ap.add_argument("--n-test", type=int, default=3)
    args = ap.parse_args()
    built = build({"dev": args.n_dev, "val": args.n_val, "test": args.n_test})

    for split in built:
        d = OUT / split
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.yaml"):
            old.unlink()
        for short, tasks in built[split].items():
            header = ("# GENERATO da scripts/build_zurich_tasks.py: non modificare a mano (le modifiche vanno nelle specifiche e si rigenera).\n"
                      f"# Schema {short}, split {split}. Dati reali CC0 della Città di Zurigo (data/zurich/, vedi docs/dati.md).\n"
                      "# Domande e query gold scritte da Claude (strumento di sviluppo), verificate eseguendo il gold; formulazioni NON riviste da madrelingua.\n")
            (d / f"{short}.yaml").write_text(
                header + yaml.safe_dump(tasks, allow_unicode=True, sort_keys=False, width=100000), encoding="utf-8")

    splits = {}
    manifest = {m["dataset"]: m for m in json.loads((DATA / "MANIFEST.json").read_text(encoding="utf-8"))}
    for split, by_ds in built.items():
        allt = [t for ts in by_ds.values() for t in ts]
        splits[split] = {
            "n_tasks": len(allt),
            "schemas": sorted(by_ds),
            "by_language": dict(sorted(Counter(t["meta"]["language"] for t in allt).items())),
            "by_category": dict(sorted(Counter(t["category"] for t in allt).items())),
            "by_trap": dict(sorted(Counter(t["meta"].get("trap", "none") for t in allt).items())),
            "files": {f"{split}/{s}.yaml": sha256_file(OUT / split / f"{s}.yaml") for s in sorted(by_ds)},
            "data_sha256": {DATASETS[s][2]: manifest[DATASETS[s][2]]["sha256"] for s in sorted(by_ds)},
        }
    (OUT / "SPLITS.json").write_text(json.dumps(splits, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for s, v in splits.items():
        print(f"{s:5} {v['n_tasks']:4} task · {len(v['schemas'])} schemi · lingue {v['by_language']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
