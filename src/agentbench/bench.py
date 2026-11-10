"""Orchestrazione di una run: esegue ogni task N volte e salva i risultati su disco.

Ogni risultato viene scritto subito in `results.jsonl` (una riga per task × ripetizione, con
la traiettoria completa), quindi una run interrotta lascia comunque dati utilizzabili.
`meta.json` registra tutto ciò che serve a riprodurre o confrontare la run.
"""
from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import __version__
from .checks import evaluate, was_exercised
from .client import ChatClient
from .recording import CALLS_FILE, file_sha256
from .runner import run_task
from .sql_env import make_box
from .tasks import DEFAULT_SYSTEM, Task


def _git_sha() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _record(task: Task, repeat: int, traj, checks: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = traj.pairs
    usage = [s.usage for s in traj.steps]
    scored = [c for c in checks if not c.get("diagnostic")]  # i controlli diagnostici non contano
    exercised = was_exercised(task, traj)
    # outcome: passed | failed | not_exercised. `not_exercised` (l'attacco non è mai stato letto dal modello)
    # non è né un successo né un fallimento: `passed` è False, ma i report lo escludono dai denominatori.
    outcome = "not_exercised" if exercised is False else ("passed" if all(c["ok"] for c in scored) else "failed")
    return {
        "task_id": task.id,
        "category": task.category,
        **({"meta": task.meta} if task.meta else {}),  # lingua della domanda, schema, split, trappole: per le analisi a strati
        "repeat": repeat,
        "outcome": outcome,
        "exercised": exercised,
        "passed": outcome == "passed",
        "score": sum(c["ok"] for c in scored) / len(scored),
        "checks": checks,
        "stopped": traj.stopped,
        "error": traj.error,
        "final_text": traj.final_text,
        "n_steps": len(traj.steps),
        "n_tool_calls": len(traj.calls),
        "parse_sources": [c.source for c in traj.calls],
        "parse_errors": sum(1 for c in traj.calls if c.parse_error),
        "error_kinds": [r.error_kind for _, r in pairs if r.error_kind],
        "latency_s": round(sum(s.latency_s for s in traj.steps), 3),
        "prompt_tokens": sum(u.get("prompt_tokens", 0) for u in usage),
        "completion_tokens": sum(u.get("completion_tokens", 0) for u in usage),
        "trajectory": traj.to_dict(),
    }


def run_suite(
    client: ChatClient,
    tasks: list[Task],
    repeats: int,
    out_dir: Path,
    history_mode: str = "openai",
    system_prompt: str = DEFAULT_SYSTEM,
    tasks_digest: str | None = None,
    on_result: Callable[[dict[str, Any]], None] | None = None,
    record: bool = True,
    ablations: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(client, "record_to") and record:
        client.record_to(out_dir / CALLS_FILE)
    meta = {
        "harness_version": __version__,
        "git_sha": _git_sha(),
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "model": client.model,
        "base_url": client.base_url,
        "temperature": client.temperature,
        "max_tokens": client.max_tokens,
        "seed": client.seed,
        "extra_body": client.extra_body,
        "history_mode": history_mode,
        "ablations": sorted(ablations),
        "system_prompt": system_prompt,
        "repeats": repeats,
        "n_tasks": len(tasks),
        "tasks_digest": tasks_digest,
        "recorded_calls": bool(record),
        **getattr(client, "meta_extra", {}),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    records: list[dict[str, Any]] = []
    with (out_dir / "results.jsonl").open("w", encoding="utf-8") as f:
        for task in tasks:
            for rep in range(repeats):
                box = make_box(task.setup, task.tools)  # stato fresco a ogni esecuzione
                try:
                    traj = run_task(client, task, box, history_mode, system_prompt, tuple(ablations))
                    rec = _record(task, rep, traj, evaluate(task, traj, box))
                finally:
                    getattr(box, "close", lambda: None)()  # chiude il database SQL e cancella il file temporaneo
                records.append(rec)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                if on_result:
                    on_result(rec)
    # Impronte dei file di output: chi riceve la cartella può verificare che non sia stata alterata.
    meta["files_sha256"] = {
        name: file_sha256(out_dir / name)
        for name in ("results.jsonl", CALLS_FILE)
        if (out_dir / name).exists()
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return records
