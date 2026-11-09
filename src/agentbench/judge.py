"""Giudice automatico OPZIONALE, con modelli open-weights (regola 4 del hackathon).

Il punteggio ufficiale dell'harness resta quello deterministico di `checks.py`. Il giudice serve a
due cose: (1) leggere il testo libero, dove le euristiche sono deboli; (2) tarare i controlli
automatici: i disaccordi tra giudice e controlli indicano dove un controllo è troppo severo o
troppo indulgente. Per essere riproducibile salva modello, endpoint, impronta del rubric e del
prompt, temperatura 0 e la risposta grezza di ogni giudizio.

Il giudice deve essere dichiarato in models.yaml come open-weights con fase `evaluation`
(`agentbench compliance` lo verifica). Se coincide con il modello sotto test, avvisa.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .client import ChatClient, ChatError
from .recording import CALLS_FILE  # noqa: F401  (nome del file registrato, per coerenza con le run)
from .stats import cohen_kappa

JUDGE_FILE = "judge.jsonl"
JUDGE_META = "judge_meta.json"
USER_TEMPLATE = "USER REQUEST:\n{prompt}\n\nTOOLS OFFERED: {tools}\n\nTRAJECTORY:\n{trajectory}\n\nFINAL ANSWER:\n{final}\n"
SKIP_CATEGORIES = {"judge"}  # task in cui è Apertus a fare il giudice: non c'è una traiettoria da giudicare


def _clip(text: Any, n: int = 600) -> str:
    t = str(text).replace("\n", " ")
    return t if len(t) <= n else t[:n] + "…"


def render_trajectory(traj: dict[str, Any]) -> str:
    lines: list[str] = []
    for s in traj.get("steps", []):
        if s.get("assistant_text"):
            lines.append(f"assistant: {_clip(s['assistant_text'])}")
        for c in s.get("tool_calls", []):
            lines.append(f"CALL {c.get('name')}({json.dumps(c.get('arguments'), ensure_ascii=False)})")
        for t in s.get("tool_results", []):
            lines.append(f"RESULT {t.get('name')} [{'ok' if t.get('ok') else 'ERROR'}]: {_clip(t.get('content'))}")
    return "\n".join(lines) or "(no tool calls)"


def build_prompt(record: dict[str, Any], tools: list[str]) -> str:
    traj = record["trajectory"]
    user = next((m["content"] for m in traj.get("messages", []) if m.get("role") == "user"), "")
    return USER_TEMPLATE.format(prompt=user, tools=", ".join(tools) or "(none)",
                                trajectory=render_trajectory(traj), final=record.get("final_text") or "(empty)")


def parse_verdict(text: str) -> tuple[str, list[Any], str]:
    """(PASS|FAIL|UNPARSEABLE, punti violati, motivazione)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            v = str(obj.get("verdict", "")).strip().upper()
            if v in ("PASS", "FAIL"):
                return v, list(obj.get("violated") or []), str(obj.get("reason", ""))
        except (ValueError, AttributeError):
            pass
    return "UNPARSEABLE", [], _clip(text, 200)


def judge_run(run_dir: str | Path, client: ChatClient, rubric_path: str | Path, tools_by_task: dict[str, list[str]],
              limit: int | None = None) -> dict[str, Any]:
    run_dir = Path(run_dir)
    rubric = Path(rubric_path).read_text(encoding="utf-8")
    meta = {
        "judge_model": client.model, "model": client.model, "base_url": client.base_url, "temperature": client.temperature,
        "rubric": str(rubric_path), "rubric_sha256": hashlib.sha256(rubric.encode()).hexdigest(),
        "user_template_sha256": hashlib.sha256(USER_TEMPLATE.encode()).hexdigest(),
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    source = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    meta["same_model_as_tested"] = client.model == source.get("model")
    records = [json.loads(x) for x in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    records = [r for r in records if r["category"] not in SKIP_CATEGORIES and r.get("outcome") != "not_exercised"][:limit]
    rows = []
    with (run_dir / JUDGE_FILE).open("w", encoding="utf-8") as f:
        for r in records:
            prompt = build_prompt(r, tools_by_task.get(r["task_id"], []))
            try:
                resp = client.chat([{"role": "system", "content": rubric}, {"role": "user", "content": prompt}])
                raw = resp["message"].get("content") or ""
                verdict, violated, reason = parse_verdict(raw)
            except ChatError as e:
                raw, verdict, violated, reason = "", "ERROR", [], str(e)
            row = {"task_id": r["task_id"], "repeat": r["repeat"], "category": r["category"], "auto_passed": r["passed"],
                   "judge_verdict": verdict, "violated": violated, "reason": reason, "raw": raw}
            rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta["n_judged"] = len(rows)
    (run_dir / JUDGE_META).write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"meta": meta, "rows": rows}


def agreement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in rows if r["judge_verdict"] in ("PASS", "FAIL")]
    bp = sum(r["auto_passed"] and r["judge_verdict"] == "PASS" for r in valid)
    auto_only = [r for r in valid if r["auto_passed"] and r["judge_verdict"] == "FAIL"]  # forse falso positivo dei controlli
    judge_only = [r for r in valid if not r["auto_passed"] and r["judge_verdict"] == "PASS"]  # forse controllo troppo severo
    bf = sum((not r["auto_passed"]) and r["judge_verdict"] == "FAIL" for r in valid)
    n = len(valid)
    return {"n": n, "unusable": len(rows) - n, "agree": (bp + bf) / n if n else None,
            "kappa": cohen_kappa(bp, len(auto_only), len(judge_only), bf),
            "both_pass": bp, "both_fail": bf, "auto_pass_judge_fail": auto_only, "auto_fail_judge_pass": judge_only}


def render_agreement(res: dict[str, Any]) -> str:
    a = agreement(res["rows"])
    m = res["meta"]
    lines = [f"## Giudice `{m['model']}` contro i controlli automatici", ""]
    if m.get("same_model_as_tested"):
        lines += ["> ⚠️ Il giudice coincide con il modello sotto test: i giudizi sono poco affidabili.", ""]
    if not a["n"]:
        return "\n".join(lines + ["Nessun giudizio utilizzabile."]) + "\n"
    kappa = "n/d" if a["kappa"] is None else f"{a['kappa']:.2f}"
    lines += [f"- Giudizi utilizzabili: {a['n']} (non utilizzabili: {a['unusable']})",
              f"- Accordo: {100 * a['agree']:.0f}% · kappa di Cohen: {kappa}",
              f"- Entrambi PASS: {a['both_pass']} · entrambi FAIL: {a['both_fail']}",
              f"- Controlli PASS, giudice FAIL (possibili successi falsi): {len(a['auto_pass_judge_fail'])}",
              f"- Controlli FAIL, giudice PASS (possibili controlli troppo severi): {len(a['auto_fail_judge_pass'])}", ""]
    for title, items in (("Controlli PASS, giudice FAIL", a["auto_pass_judge_fail"]),
                         ("Controlli FAIL, giudice PASS", a["auto_fail_judge_pass"])):
        if items:
            lines += [f"### {title}", ""] + [f"- `{r['task_id']}` #{r['repeat'] + 1}: {r['reason']}" for r in items] + [""]
    lines += ["Il giudice è un modello: va validato a mano su un campione prima di fidarsi dei suoi verdetti."]
    return "\n".join(lines) + "\n"
