"""Costruisce la run di riferimento SINTETICA `reference_runs/demo-oracle-sql`.

Non è un modello: un server finto esegue la query gold di ciascun task sintetico (`tasks/demo_sales.yaml`) e risponde con i valori trovati.
Serve a una sola cosa: poter eseguire `make demo` / `agentbench run --replay reference_runs/demo-oracle-sql` senza modello, senza rete e senza GPU,
e verificare che l'harness funzioni (atteso: 100%). NON rappresenta le prestazioni di Apertus e non va mai citata come tale.
Richiede l'extra `sql` (DuckDB).

Uso (dalla radice del progetto):  .venv/bin/python scripts/build_demo_sql.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from agentbench.bench import run_suite  # noqa: E402
from agentbench.client import ChatClient  # noqa: E402
from agentbench.report import render_markdown  # noqa: E402
from agentbench.sql_env import SQL_SYSTEM, make_box  # noqa: E402
from agentbench.tasks import load_tasks, tasks_digest  # noqa: E402
from mock_server import MockServer, final, native  # noqa: E402

MODEL = "demo-oracle-synthetic"
OUT = ROOT / "reference_runs" / "demo-oracle-sql"

NOTE = """# Run sintetica di riferimento (Text-to-SQL)

Questa cartella NON contiene i risultati di un modello. È stata prodotta da `scripts/build_demo_sql.py` con un server finto
che esegue la query gold di ogni task sintetico di `tasks/demo_sales.yaml` e risponde con i valori trovati.

Serve a verificare l'harness senza modello né rete: `make demo` rigioca queste risposte e deve dare il 100%.
Se non lo dà, è l'harness (o l'insieme di task) ad essere cambiato, non un modello.

Non citare mai questi numeri come prestazioni di Apertus.
"""


def gold_of(task) -> tuple[str, bool]:
    spec = next(c for c in task.checks if c["type"] == "sql_result_match")
    return spec["gold"], bool(spec.get("order_matters"))


def oracle_scripts(tasks) -> dict[str, list[dict]]:
    scripts = {}
    for t in tasks:
        gold, _ = gold_of(t)
        box = make_box(t.setup, t.tools)
        try:
            rows = box.gold_result(gold).rows
        finally:
            box.close()
        scripts[t.prompt] = [native("run_sql", {"query": gold}), final("Result: " + "; ".join(", ".join(str(v) for v in r) for r in rows))]
    return scripts


def policy_for(scripts):
    def policy(messages, tools, body):
        user = next(m["content"] for m in messages if m["role"] == "user")
        for question, script in scripts.items():
            if f"Question: {question}" in user:
                turn = sum(1 for m in messages if m["role"] == "assistant")
                return script[turn] if turn < len(script) else final("done")
        return final("(nessun copione per questo prompt)")
    return policy


def main() -> None:
    tasks = load_tasks(ROOT / "tasks")
    if OUT.exists():
        shutil.rmtree(OUT)
    with MockServer(policy_for(oracle_scripts(tasks))) as srv:
        client = ChatClient(srv.url, MODEL, retries=0, timeout=30)
        recs = run_suite(client, tasks, 1, OUT, system_prompt=SQL_SYSTEM, tasks_digest=tasks_digest(ROOT / "tasks"))
    (OUT / "report.md").write_text(render_markdown(OUT), encoding="utf-8")
    (OUT / "LEGGIMI.md").write_text(NOTE, encoding="utf-8")
    print(f"{sum(r['passed'] for r in recs)}/{len(recs)} → {OUT}")


if __name__ == "__main__":
    main()
