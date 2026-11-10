"""Riassume una run Text-to-SQL in Markdown: punteggio primario (execution accuracy rigida) con intervallo di Wilson al 95%, e le misure secondarie/diagnostiche,
per lingua, schema, trappola e categoria. Legge solo `results.jsonl` della run (nessun modello, nessuna rete). Ogni numero citato nei documenti deve venire da qui.

Uso:  .venv/bin/python scripts/summarize_run.py runs/rescored-baseline-orig-dev-r1 [altra_run ...]
Per i numeri definitivi usa la run RICALCOLATA per replay con la definizione di punteggio corrente (vedi docs/analysis_plan.md §13), non la run grezza.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from agentbench.stats import wilson  # noqa: E402


def check(r: dict, kind: str):
    return next((c["ok"] for c in r["checks"] if c["type"] == kind), None)


def pct(k: int, n: int) -> str:
    if n == 0:
        return "—"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% (IC 95% {100 * lo:.0f}–{100 * hi:.0f}%)"


def table(rows: list[dict], key, title: str) -> list[str]:
    g: dict = defaultdict(list)
    for r in rows:
        g[key(r)].append(r)
    out = [f"\n**{title}**\n", "| gruppo | n | primaria (rigida) | rilassata | conclusi |", "|---|---:|---|---:|---:|"]
    for k in sorted(g):
        rs = g[k]
        n = len(rs)
        out.append(f"| {k} | {n} | {pct(sum(1 for r in rs if check(r, 'sql_result_match')), n)} | {sum(1 for r in rs if check(r, 'sql_result_projection'))}/{n} | {sum(1 for r in rs if check(r, 'completed'))}/{n} |")
    return out


def summarize(path: Path) -> str:
    rows = [json.loads(l) for l in (path / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    meta = json.loads((path / "meta.json").read_text(encoding="utf-8"))
    n = len(rows)
    prim = sum(1 for r in rows if check(r, "sql_result_match"))
    rel = sum(1 for r in rows if check(r, "sql_result_projection"))
    done = sum(1 for r in rows if check(r, "completed"))
    fin = [check(r, "final_number") for r in rows if check(r, "final_number") is not None]
    lat = sorted(r["latency_s"] for r in rows)
    out = [f"## {path.name}", "",
           f"- modello `{Path(str(meta.get('model'))).name}` (percorso locale omesso) · extra_body `{meta.get('extra_body')}` · temperatura {meta.get('temperature')} · max_tokens {meta.get('max_tokens')} · task-set digest `{meta.get('tasks_digest')}` · {n} task",
           f"- **Punteggio primario (execution accuracy rigida): {pct(prim, n)}**",
           f"- Rilassata (colonne in più ammesse, diagnostica): {pct(rel, n)} · Conclusi con risposta finale (diagnostica): {pct(done, n)}",
           f"- Numero della risposta finale giusto (diagnostica, solo task con risposta numerica): {pct(sum(fin), len(fin))}",
           f"- Tempo per task: mediano {st.median(lat):.0f} s · p90 {lat[int(0.9 * (n - 1))]:.0f} s · max {lat[-1]:.0f} s · totale {sum(lat) / 3600:.2f} h",
           f"- Chiamate a `run_sql`: {sum(r['n_tool_calls'] for r in rows)} · errori di parsing delle tool call: {sum(r['parse_errors'] for r in rows)} · task senza alcuna query: {sum(1 for r in rows if r['n_tool_calls'] == 0)}",
           f"- Motivi di stop: {dict(Counter(r['stopped'] for r in rows))} · tipi di errore dei tool: {dict(Counter(k for r in rows for k in r['error_kinds']))}"]
    out += table(rows, lambda r: r["meta"]["language"], "Per lingua della domanda")
    out += table(rows, lambda r: r["meta"]["schema_id"], "Per schema")
    out += table(rows, lambda r: r["meta"].get("trap", "nessuna"), "Per trappola")
    out += table(rows, lambda r: r["category"], "Per categoria")
    return "\n".join(out)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(summarize(Path(p)), "\n")
