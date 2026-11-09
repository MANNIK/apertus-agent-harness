"""Interfaccia a riga di comando: smoke, run, report, compare, list-tasks."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from .bench import run_suite
from .client import ChatClient, ChatError
from .parser import extract_tool_calls
from .replay import ReplayClient
from .report import render_compare, render_markdown
from .tasks import DEFAULT_SYSTEM, load_tasks, tasks_digest
from .tools import ToolBox

DEFAULT_TASKS = "tasks"


def _add_model_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--base-url", default=os.environ.get("APERTUS_BASE_URL") or os.environ.get("LLM_BASE_URL") or "http://localhost:8080/v1",
                   help="endpoint OpenAI-compatibile (env APERTUS_BASE_URL o LLM_BASE_URL)")
    p.add_argument("--model", default=os.environ.get("APERTUS_MODEL") or os.environ.get("LLM_NAME") or "",
                   help="nome del modello (env APERTUS_MODEL o LLM_NAME)")
    p.add_argument("--api-key", default=os.environ.get("APERTUS_API_KEY") or os.environ.get("LLM_API_KEY") or "none",
                   help="env APERTUS_API_KEY o LLM_API_KEY")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--timeout", type=float, default=300.0)
    p.add_argument("--extra-body", default="{}",
                   help='JSON unito al corpo della richiesta, es. \'{"chat_template_kwargs": {"enable_thinking": false}}\'')


def _client(args) -> ChatClient:
    if not args.model:
        sys.exit("manca --model (o la variabile APERTUS_MODEL / LLM_NAME)")
    try:
        extra = json.loads(args.extra_body)
    except json.JSONDecodeError as e:
        sys.exit(f"--extra-body non è JSON valido: {e}")
    return ChatClient(args.base_url, args.model, args.api_key, args.temperature, args.max_tokens,
                      args.seed, extra, args.timeout)


def cmd_smoke(args) -> int:
    client = _client(args)
    print(f"1/2 connessione a {client.base_url} (modello {client.model})…")
    try:
        r = client.chat([{"role": "user", "content": "Reply with the single word OK."}])
    except ChatError as e:
        print(f"  ✗ {e}")
        return 1
    print(f"  ✓ risposta: {(r['message'].get('content') or '').strip()[:80]!r} ({r['latency_s']:.1f}s)")

    print("2/2 tool calling…")
    box = ToolBox()
    r = client.chat([{"role": "user", "content": "What is the temperature in Lugano right now? Use the tool."}],
                    tools=box.specs(["get_weather"]))
    raw = r["message"]
    calls, _ = extract_tool_calls(raw, {"get_weather"})
    print("  messaggio grezzo del server:")
    print("   ", json.dumps(raw, ensure_ascii=False)[:900])
    if not calls:
        print("  ✗ nessuna tool call riconosciuta: il modello ha risposto a parole, oppure il formato è sconosciuto.")
        print("    Controlla il messaggio grezzo qui sopra e, se serve, estendi agentbench/parser.py.")
        return 1
    c = calls[0]
    res = box.execute(c, ["get_weather"])
    print(f"  chiamata: {c.name}({c.arguments}) · origine del parsing: {c.source} · esito tool: "
          f"{'ok' if res.ok else res.content}")
    if c.source != "native":
        print("  ⚠ il server NON restituisce `tool_calls` strutturati: l'harness usa il parser di fallback.")
        print("    Funziona, ma tienine conto quando confronti con vLLM (--tool-call-parser apertus).")
    ok = c.name == "get_weather" and not c.parse_error and res.ok
    print("  ✓ tool calling utilizzabile" if ok else "  ✗ tool call presente ma non valida")
    return 0 if ok else 1


def _parse_ablations(raw: str | None) -> tuple[str, ...]:
    """Ablazioni da --ablate o dalla variabile AGENTBENCH_ABLATE (separate da virgola)."""
    from .tools import ABLATIONS
    names = tuple(x.strip() for x in (raw or os.environ.get("AGENTBENCH_ABLATE", "")).split(",") if x.strip())
    unknown = set(names) - set(ABLATIONS)
    if unknown:
        sys.exit(f"ablazioni sconosciute {sorted(unknown)} (disponibili: {', '.join(ABLATIONS)})")
    return names


def cmd_run(args) -> int:
    replay = ReplayClient(args.replay) if args.replay else None
    client = replay if replay else _client(args)
    tasks = load_tasks(args.tasks, args.only.split(",") if args.only else None,
                       args.category.split(",") if args.category else None)
    if not tasks:
        sys.exit("nessun task selezionato")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", client.model).strip("-")
    if replay:
        slug = "replay-" + slug
    out = Path(args.out) if args.out else Path("runs") / f"{slug}-{datetime.now():%Y%m%d-%H%M%S}"
    if args.system_prompt_file:
        system = Path(args.system_prompt_file).read_text(encoding="utf-8")
    elif replay:  # nel replay il prompt deve essere quello della run di origine, altrimenti le chiavi non coincidono
        system = replay.source_meta["system_prompt"]
    else:
        system = DEFAULT_SYSTEM
    if args.ablate and replay:
        sys.exit("--ablate non si combina con --replay: il replay usa le ablazioni della run di origine")
    ablations = _parse_ablations(args.ablate) if not replay else tuple(replay.source_meta.get("ablations") or ())
    history_mode = args.history_mode or (replay.source_meta["history_mode"] if replay else "openai")
    print(f"{len(tasks)} task × {args.repeats} ripetizioni → {out}\n")

    def show(rec) -> None:
        mark = {"passed": "PASS", "not_exercised": "N/EX"}.get(rec.get("outcome"), "FAIL")
        print(f"[{mark}] {rec['task_id']:<28} #{rec['repeat'] + 1}  {rec['n_steps']} step, "
              f"{rec['n_tool_calls']} tool call, {rec['latency_s']:.1f}s")
        if rec.get("outcome") == "not_exercised":
            print("         · attacco mai letto dal modello: non conta né come passato né come fallito")
        elif not rec["passed"]:
            for c in rec["checks"]:
                if not c["ok"] and not c.get("diagnostic"):
                    print(f"         ✗ {c['type']}: {c['detail'][:160]}")

    records = run_suite(client, tasks, args.repeats, out, history_mode, system, tasks_digest(args.tasks), show,
                        record=not args.no_record, ablations=ablations)
    (out / "report.md").write_text(render_markdown(out), encoding="utf-8")
    passed = sum(r["passed"] for r in records)
    noex = sum(r.get("outcome") == "not_exercised" for r in records)
    extra = f" ({noex} non esercitate, escluse dal conteggio dei fallimenti)" if noex else ""
    print(f"\n{passed}/{len(records)} esecuzioni passate{extra}. Report: {out / 'report.md'}")
    return 0


def cmd_report(args) -> int:
    md = render_markdown(args.run_dir)
    (Path(args.run_dir) / "report.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def cmd_compare(args) -> int:
    print(render_compare(args.run_a, args.run_b))
    return 0


def _run_dirs(paths: list[str]) -> list[str]:
    if paths:
        return paths
    root = Path("runs")
    return sorted(str(p) for p in root.iterdir() if (p / "meta.json").exists()) if root.is_dir() else []


def cmd_compliance(args) -> int:
    from .compliance import check, render_findings
    findings = check(args.models, _run_dirs(args.run_dirs))
    print(render_findings(findings))
    return 1 if any(f.level == "ERROR" for f in findings) else 0


def cmd_manifest(args) -> int:
    from .compliance import render_manifest
    md = render_manifest(args.models, _run_dirs(args.run_dirs))
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"scritto {args.out}")
    else:
        print(md)
    return 0


def cmd_judge(args) -> int:
    from .judge import render_agreement, judge_run
    model = args.judge_model or os.environ.get("JUDGE_MODEL", "")
    if not model:
        sys.exit("manca --judge-model (o la variabile JUDGE_MODEL): serve un modello open-weights, dichiarato in models.yaml")
    client = ChatClient(args.judge_base_url or os.environ.get("JUDGE_BASE_URL") or "http://localhost:8081/v1", model,
                        args.judge_api_key or os.environ.get("JUDGE_API_KEY") or "none", 0.0, args.max_tokens,
                        timeout=args.timeout)
    tools = {t.id: list(t.tools) for t in load_tasks(args.tasks)}
    res = judge_run(args.run_dir, client, args.rubric, tools, args.limit)
    md = render_agreement(res)
    (Path(args.run_dir) / "judge_report.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def cmd_list(args) -> int:
    tasks = load_tasks(args.tasks)
    by_cat: dict[str, list[str]] = {}
    for t in tasks:
        by_cat.setdefault(t.category, []).append(t.id)
    for cat, ids in by_cat.items():
        print(f"{cat} ({len(ids)}): {', '.join(ids)}")
    print(f"\ntotale: {len(tasks)} task")
    return 0


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="agentbench", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("smoke", help="verifica rapida: connessione e tool calling del server")
    _add_model_args(p)
    p.set_defaults(fn=cmd_smoke)

    p = sub.add_parser("run", help="esegue la suite di task")
    _add_model_args(p)
    p.add_argument("--tasks", default=DEFAULT_TASKS, help="cartella o file YAML dei task")
    p.add_argument("--only", help="id dei task separati da virgola")
    p.add_argument("--category", help="categorie separate da virgola")
    p.add_argument("--repeats", type=int, default=1, help="ripetizioni per task (usa >1 con temperature > 0)")
    p.add_argument("--history-mode", choices=["openai", "text"], default=None,
                   help="default: openai (nel replay: quello della run di origine)")
    p.add_argument("--replay", metavar="RUN_DIR",
                   help="non usa nessun modello: ripropone le risposte registrate in RUN_DIR/calls.jsonl e ri-valuta")
    p.add_argument("--ablate", metavar="NOMI",
                   help="varianti di prova dello schema dei tool, separate da virgola (env AGENTBENCH_ABLATE); "
                        "oggi: calculator_example = senza l'esempio '(12 + 8) / 2' nel calcolatore")
    p.add_argument("--no-record", action="store_true", help="non salvare calls.jsonl (di default ogni run lo salva)")
    p.add_argument("--system-prompt-file", help="sostituisce il system prompt di default")
    p.add_argument("--out", help="cartella di output (default runs/<modello>-<data>)")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("report", help="(ri)genera report.md da una cartella di run")
    p.add_argument("run_dir")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("compare", help="confronta due run (stessa suite)")
    p.add_argument("run_a")
    p.add_argument("run_b")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("compliance", help="controlla le regole 3, 4, 5, 6 del hackathon su registro modelli e run")
    p.add_argument("run_dirs", nargs="*", help="cartelle di run (default: tutte quelle in runs/)")
    p.add_argument("--models", default="models.yaml")
    p.set_defaults(fn=cmd_compliance)

    p = sub.add_parser("manifest", help="stampa/scrive la tabella dei modelli usati (regola 6)")
    p.add_argument("run_dirs", nargs="*", help="cartelle di run da includere (default: tutte quelle in runs/)")
    p.add_argument("--models", default="models.yaml")
    p.add_argument("--out", help="scrive su file (es. MODELS.md)")
    p.set_defaults(fn=cmd_manifest)

    p = sub.add_parser("judge", help="giudice open-weights opzionale: giudica le traiettorie e le confronta coi controlli")
    p.add_argument("run_dir")
    p.add_argument("--judge-base-url", help="endpoint del giudice (env JUDGE_BASE_URL)")
    p.add_argument("--judge-model", help="modello giudice open-weights (env JUDGE_MODEL)")
    p.add_argument("--judge-api-key", help="env JUDGE_API_KEY")
    p.add_argument("--rubric", default="rubrics/agentic_v1.md")
    p.add_argument("--tasks", default=DEFAULT_TASKS)
    p.add_argument("--limit", type=int, default=None, help="giudica solo le prime N esecuzioni")
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--timeout", type=float, default=300.0)
    p.set_defaults(fn=cmd_judge)

    p = sub.add_parser("list-tasks", help="elenca i task per categoria")
    p.add_argument("--tasks", default=DEFAULT_TASKS)
    p.set_defaults(fn=cmd_list)

    args = ap.parse_args(argv)
    try:
        sys.exit(args.fn(args))
    except (ValueError, FileNotFoundError) as e:
        sys.exit(f"errore: {e}")
