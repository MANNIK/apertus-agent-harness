"""Costruisce la run di riferimento SINTETICA `reference_runs/demo-oracle`.

Non è un modello: un server finto risponde con i percorsi corretti scritti in
`tests/test_tasks_solvable.py` (uno per task). Serve a una sola cosa: poter eseguire
`make demo` / `agentbench run --replay reference_runs/demo-oracle` su una macchina senza modello,
senza rete e senza GPU, e verificare che l'harness funzioni (atteso: 33/33).
NON rappresenta le prestazioni di Apertus e non va mai citata come tale.

Uso (dalla radice del progetto):  .venv/bin/python scripts/build_demo.py
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
from agentbench.tasks import load_tasks, tasks_digest  # noqa: E402
from mock_server import MockServer, scripted  # noqa: E402
from test_tasks_solvable import SOLUTIONS  # noqa: E402

MODEL = "demo-oracle-synthetic"
OUT = ROOT / "reference_runs" / "demo-oracle"

NOTE = """# Run sintetica di riferimento

Questa cartella NON contiene i risultati di un modello. È stata prodotta da `scripts/build_demo.py`
con un server finto che esegue i percorsi corretti dei 33 task.

Serve a verificare l'harness senza modello né rete: `make demo` rigioca queste risposte e deve dare 33/33.
Se non dà 33/33, è l'harness (o la suite di task) ad essere cambiato, non un modello.

Non citare mai questi numeri come prestazioni di Apertus.
"""


def main() -> None:
    tasks = load_tasks(ROOT / "tasks")
    scripts = {t.prompt: SOLUTIONS[t.id] for t in tasks}
    if OUT.exists():
        shutil.rmtree(OUT)
    with MockServer(scripted(scripts)) as srv:
        client = ChatClient(srv.url, MODEL, retries=0, timeout=30)
        recs = run_suite(client, tasks, 1, OUT, tasks_digest=tasks_digest(ROOT / "tasks"))
    (OUT / "report.md").write_text(render_markdown(OUT), encoding="utf-8")
    (OUT / "LEGGIMI.md").write_text(NOTE, encoding="utf-8")
    print(f"{sum(r['passed'] for r in recs)}/{len(recs)} → {OUT}")


if __name__ == "__main__":
    main()
