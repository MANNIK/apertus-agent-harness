"""Report in Markdown (pensato per essere incollato in un commento GitHub) e confronto tra run."""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .stats import fmt_ci, mcnemar_exact

MAX_REPORT_CHARS = 60_000  # i commenti GitHub arrivano a 65.536 caratteri


def load_run(run_dir: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    d = Path(run_dir)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in (d / "results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return meta, records


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def task_rates(records: list[dict[str, Any]]) -> dict[str, float]:
    """task_id -> frazione di ripetizioni passate."""
    by_task: dict[str, list[bool]] = defaultdict(list)
    for r in records:
        by_task[r["task_id"]].append(r["passed"])
    return {t: sum(v) / len(v) for t, v in by_task.items()}


def category_rows(records: list[dict[str, Any]]) -> list[tuple[str, int, float, float]]:
    """(categoria, n_task, pass@1, quota di task passati in TUTTE le ripetizioni)."""
    cats: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        cats[r["category"]].append(r)
    rows = []
    for cat, recs in cats.items():
        rates = task_rates(recs)
        rows.append((cat, len(rates), sum(r["passed"] for r in recs) / len(recs),
                     sum(1 for v in rates.values() if v == 1.0) / len(rates)))
    return rows


def tool_health(records: list[dict[str, Any]]) -> dict[str, Any]:
    sources: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    n_calls = 0
    for r in records:
        sources.update(r["parse_sources"])
        kinds.update(r["error_kinds"])
        n_calls += r["n_tool_calls"]
    invalid = kinds["unknown_tool"] + kinds["bad_args"]
    return {"n_calls": n_calls, "sources": sources, "kinds": kinds,
            "valid_rate": (1 - invalid / n_calls) if n_calls else None}


def render_markdown(run_dir: str | Path) -> str:
    meta, records = load_run(run_dir)
    lines = [f"## Agent harness · `{meta['model']}`", ""]
    lines.append(
        f"{meta['n_tasks']} task × {meta['repeats']} ripetizioni · temperatura {meta['temperature']} · "
        f"history `{meta['history_mode']}` · suite `{meta.get('tasks_digest')}` · {meta['started_utc']}"
    )
    lines += ["", "| Categoria | Task | Pass@1 | Task sempre passati |", "|---|---:|---:|---:|"]
    for cat, n, p1, allp in sorted(category_rows(records)):
        lines.append(f"| {cat} | {n} | {_pct(p1)} | {_pct(allp)} |")
    total = sum(r["passed"] for r in records) / len(records) if records else 0
    lines.append(f"| **Totale** | {len({r['task_id'] for r in records})} | **{_pct(total)}** | |")
    n_pass = sum(r["passed"] for r in records)
    lines += ["", f"Esecuzioni passate: {fmt_ci(n_pass, len(records))}. L'intervallo di Wilson assume esecuzioni "
              "indipendenti: con più ripetizioni dello stesso task è ottimistico."]

    h = tool_health(records)
    lat = [r["latency_s"] for r in records]
    lines += ["", "### Salute delle tool call", "", "| Metrica | Valore |", "|---|---|"]
    lines.append(f"| Tool call totali | {h['n_calls']} |")
    if h["n_calls"]:
        lines.append(f"| Chiamate valide (tool esistente, argomenti conformi) | {_pct(h['valid_rate'])} |")
        src = ", ".join(f"{k}: {v}" for k, v in h["sources"].most_common())
        lines.append(f"| Origine del parsing | {src} |")
        lines.append(f"| Errori: tool inventato / argomenti errati / errori del tool | "
                     f"{h['kinds']['unknown_tool']} / {h['kinds']['bad_args']} / {h['kinds']['tool_error']} |")
    if lat:
        lines.append(f"| Latenza mediana per task | {statistics.median(lat):.1f}s |")
    lines.append(f"| Passi medi per task | {statistics.mean(r['n_steps'] for r in records):.1f} |" if records else "")

    failing = [r for r in records if not r["passed"]]
    lines += ["", f"### Fallimenti ({len(failing)} esecuzioni)", ""]
    shown = 0
    for r in failing:
        bad = [c for c in r["checks"] if not c["ok"]]
        body = "\n".join(f"- **{c['type']}**: {c['detail']}" for c in bad)
        final = (r["final_text"] or "").strip().replace("\n", " ")[:300]
        block = (f"<details><summary><code>{r['task_id']}</code> ({r['category']}, ripetizione {r['repeat'] + 1})"
                 f"</summary>\n\n{body}\n\nRisposta finale: _{final or '(vuota)'}_\n\n</details>")
        if sum(len(x) for x in lines) + len(block) > MAX_REPORT_CHARS:
            lines.append(f"_…altri {len(failing) - shown} fallimenti omessi: vedi `results.jsonl`._")
            break
        lines.append(block)
        shown += 1
    if not failing:
        lines.append("Nessun fallimento.")
    return "\n".join(lines) + "\n"


def _config_diff(meta_a: dict, meta_b: dict) -> list[str]:
    """Righe Markdown con le impostazioni che differiscono tra le due run.

    Un confronto è interpretabile solo sapendo cosa è cambiato: se cambiano più cose insieme
    (modello, prompt, temperatura…) l'effetto non è attribuibile a una sola. Il system prompt,
    lungo, è mostrato come impronta (sha256 abbreviato) e lunghezza."""
    import hashlib

    def show(key: str, meta: dict) -> str:
        v = meta.get(key)
        if key == "system_prompt" and isinstance(v, str):
            return f"sha {hashlib.sha256(v.encode()).hexdigest()[:8]} ({len(v)} car.)"
        return "—" if v is None else str(v)

    keys = ["model", "temperature", "max_tokens", "seed", "extra_body", "history_mode", "system_prompt"]
    rows = [(k, show(k, meta_a), show(k, meta_b)) for k in keys if meta_a.get(k) != meta_b.get(k)]
    if not rows:
        return ["Configurazione identica nelle due run (stesso modello, prompt e parametri).", ""]
    out = ["**Cosa cambia tra A e B**", "", "| Impostazione | A | B |", "|---|---|---|"]
    out += [f"| {k} | `{a}` | `{b}` |" for k, a, b in rows]
    if len(rows) > 1:
        out += ["", "> ⚠️ Cambia più di una impostazione: l'effetto non è attribuibile a una sola."]
    return out + [""]


def render_compare(dir_a: str | Path, dir_b: str | Path) -> str:
    meta_a, rec_a = load_run(dir_a)
    meta_b, rec_b = load_run(dir_b)
    lines = [f"## Confronto: `{meta_a['model']}` (A) vs `{meta_b['model']}` (B)", ""]
    lines += _config_diff(meta_a, meta_b)
    if meta_a.get("tasks_digest") != meta_b.get("tasks_digest"):
        lines += ["> ⚠️ Le due run usano suite di task diverse: il confronto vale solo per i task in comune.", ""]
    ca = {c: p1 for c, _, p1, _ in category_rows(rec_a)}
    cb = {c: p1 for c, _, p1, _ in category_rows(rec_b)}
    lines += ["| Categoria | A | B | Δ |", "|---|---:|---:|---:|"]
    for cat in sorted(set(ca) | set(cb)):
        a, b = ca.get(cat), cb.get(cat)
        d = f"{100 * (b - a):+.0f} pt" if a is not None and b is not None else "—"
        lines.append(f"| {cat} | {_pct(a) if a is not None else '—'} | {_pct(b) if b is not None else '—'} | {d} |")
    ra, rb = task_rates(rec_a), task_rates(rec_b)
    common = ra.keys() & rb.keys()
    pa, pb = sum(r["passed"] for r in rec_a), sum(r["passed"] for r in rec_b)
    better = sum(1 for t in common if rb[t] >= 0.5 > ra[t])
    worse = sum(1 for t in common if ra[t] >= 0.5 > rb[t])
    lines += ["", "### Esito complessivo", "",
              f"- A: {fmt_ci(pa, len(rec_a))}", f"- B: {fmt_ci(pb, len(rec_b))}",
              f"- Task migliorati: {better} · peggiorati: {worse} · test esatto di McNemar, due code: "
              f"p = {mcnemar_exact(better, worse):.3f}"
              + (" (task considerati passati se superati almeno nella metà delle ripetizioni)"
                 if len(rec_a) != len(ra) or len(rec_b) != len(rb) else ""),
              "- Un p-value alto con pochi task discordanti non dimostra che A e B siano uguali: "
              "dice solo che questi dati non bastano per distinguerli."]
    changed = sorted(((t, ra[t], rb[t]) for t in ra.keys() & rb.keys() if ra[t] != rb[t]), key=lambda x: x[2] - x[1])
    lines += ["", f"### Task che cambiano esito ({len(changed)})", ""]
    if changed:
        lines += ["| Task | A | B | |", "|---|---:|---:|---|"]
        for t, a, b in changed:
            lines.append(f"| `{t}` | {_pct(a)} | {_pct(b)} | {'🔻 regressione' if b < a else '🔺 miglioramento'} |")
    else:
        lines.append("Nessuna differenza task per task.")
    return "\n".join(lines) + "\n"
