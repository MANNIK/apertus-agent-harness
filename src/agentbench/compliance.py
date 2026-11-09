"""Controlli di conformità alle regole del hackathon e registro dei modelli (regola 6).

Cosa controlla (e cosa NO):
- Regola 6: ogni modello che compare in una run (o come giudice) è dichiarato in `models.yaml`,
  con versione, licenza e ruolo.
- Regole 3 e 4: nessun modello CHIUSO è dichiarato per le fasi `runtime` o `evaluation`.
- Regola 5: è stata scelta un'architettura target; gli endpoint usati sono locali (altrimenti va dichiarato).
- Regole 3 e 5, in modo statico: il codice dell'harness non importa librerie di rete oltre a httpx nel
  client. Non dimostra l'assenza di chiamate esterne in una soluzione finale: è un controllo sul NOSTRO codice.
- Integrità: le impronte sha256 di results.jsonl e calls.jsonl in meta.json corrispondono ai file.
Non può stabilire se un modello sia davvero open-weights o se la licenza sia quella dichiarata: lo
scrive chi compila il registro, e va verificato sulla fonte.
"""
from __future__ import annotations

import ast
import ipaddress
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from .recording import file_sha256

STAGES = {"development", "runtime", "evaluation"}
TARGETS = {"on-premise", "air-gapped", "sovereign-swiss-cloud"}
FORBIDDEN_IMPORTS = {"requests", "urllib3", "aiohttp", "socket", "smtplib", "ftplib", "http.client",
                     "urllib.request", "websockets", "httpx"}


@dataclass
class Finding:
    level: str  # ERROR | WARN | OK
    rule: str
    message: str


def load_manifest(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data.get("models"), list):
        raise ValueError(f"{path}: manca l'elenco `models`")
    return data


def _manifest_findings(m: dict[str, Any]) -> list[Finding]:
    out: list[Finding] = []
    for e in m["models"]:
        name = e.get("id", "?")
        missing = [k for k in ("id", "name", "version", "license", "role", "stages") if not e.get(k)]
        if "open_weights" not in e:
            missing.append("open_weights")
        if missing:
            out.append(Finding("ERROR", "6", f"{name}: campi mancanti nel registro: {', '.join(missing)}"))
            continue
        bad = set(e["stages"]) - STAGES
        if bad:
            out.append(Finding("ERROR", "6", f"{name}: fasi non valide {sorted(bad)} (ammesse: {sorted(STAGES)})"))
        if not e["open_weights"] and set(e["stages"]) & {"runtime", "evaluation"}:
            out.append(Finding("ERROR", "3/4", f"{name}: modello chiuso dichiarato per {sorted(set(e['stages']) & {'runtime', 'evaluation'})}: "
                                              "a runtime e nella valutazione sono ammessi solo Apertus e modelli open-weights"))
    target = (m.get("deployment") or {}).get("target")
    if target is None:
        out.append(Finding("WARN", "5", "architettura target non dichiarata (deployment.target in models.yaml)"))
    elif target not in TARGETS:
        out.append(Finding("ERROR", "5", f"architettura target '{target}' non valida (ammesse: {sorted(TARGETS)})"))
    else:
        out.append(Finding("OK", "5", f"architettura target dichiarata: {target}"))
    return out


def _find_entry(m: dict[str, Any], model: str) -> dict[str, Any] | None:
    for e in m["models"]:
        if model == e.get("id") or any(frag and frag in model for frag in e.get("match", [])):
            return e
    return None


def is_local_url(url: str) -> bool:
    host = urlparse(url).hostname or ""
    if host in ("localhost", ""):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_private
    except ValueError:
        return "." not in host  # nome di servizio interno (es. un container "vllm")


def _run_findings(m: dict[str, Any], run_dir: Path) -> list[Finding]:
    out: list[Finding] = []
    tag = f"[{run_dir.name}]"
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    entry = _find_entry(m, meta["model"])
    if entry is None:
        out.append(Finding("ERROR", "6", f"{tag} modello usato non dichiarato in models.yaml: {meta['model']}"))
    else:
        out.append(Finding("OK", "6", f"{tag} modello dichiarato: {entry['id']}"))
    if is_local_url(meta["base_url"]):
        out.append(Finding("OK", "3/5", f"{tag} endpoint locale: {meta['base_url']}"))
    else:
        out.append(Finding("WARN", "3/5", f"{tag} endpoint NON locale ({meta['base_url']}): va dichiarato come "
                                          "cloud sovrano svizzero o simile e deve essere un servizio ammesso"))
    judge_file = run_dir / "judge_meta.json"
    if judge_file.exists():
        jm = json.loads(judge_file.read_text(encoding="utf-8"))
        je = _find_entry(m, jm["model"])
        if je is None:
            out.append(Finding("ERROR", "4/6", f"{tag} giudice non dichiarato in models.yaml: {jm['model']}"))
        elif not je["open_weights"]:
            out.append(Finding("ERROR", "4", f"{tag} giudice '{je['id']}' non è open-weights"))
        elif "evaluation" not in je["stages"]:
            out.append(Finding("ERROR", "6", f"{tag} giudice '{je['id']}' non dichiara la fase 'evaluation'"))
        else:
            out.append(Finding("OK", "4", f"{tag} giudice open-weights dichiarato: {je['id']}"))
    for name, expected in (meta.get("files_sha256") or {}).items():
        p = run_dir / name
        if not p.exists():
            out.append(Finding("ERROR", "integrità", f"{tag} manca {name}"))
        elif file_sha256(p) != expected:
            out.append(Finding("ERROR", "integrità", f"{tag} {name} è stato modificato dopo la run (sha256 diverso)"))
    return out


def scan_network_imports(src_dir: str | Path) -> list[Finding]:
    out: list[Finding] = []
    for py in sorted(Path(src_dir).glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module)
                names |= {f"{node.module}.{a.name}" for a in node.names}
        allowed = {"httpx"} if py.name == "client.py" else set()
        hits = sorted(n for n in names if n in FORBIDDEN_IMPORTS - allowed)
        if hits:
            out.append(Finding("ERROR", "3/5", f"{py.name} importa librerie di rete: {', '.join(hits)}"))
    if not out:
        out.append(Finding("OK", "3/5", "nessuna libreria di rete importata oltre a httpx in client.py"))
    return out


def check(manifest_path: str | Path, run_dirs: list[str | Path], src_dir: str | Path | None = None) -> list[Finding]:
    m = load_manifest(manifest_path)
    findings = _manifest_findings(m)
    for d in run_dirs:
        findings += _run_findings(m, Path(d))
    findings += scan_network_imports(src_dir or Path(__file__).parent)
    return findings


def render_findings(findings: list[Finding]) -> str:
    icon = {"ERROR": "✗", "WARN": "⚠", "OK": "✓"}
    lines = [f"{icon[f.level]} [regola {f.rule}] {f.message}" for f in findings]
    n_err = sum(f.level == "ERROR" for f in findings)
    n_warn = sum(f.level == "WARN" for f in findings)
    lines.append(f"\n{n_err} errori, {n_warn} avvisi")
    return "\n".join(lines)


def render_manifest(manifest_path: str | Path, run_dirs: list[str | Path] | None = None) -> str:
    m = load_manifest(manifest_path)
    lines = ["# Modelli usati (regola 6)", "",
             "| Modello | Versione | Licenza | Open weights | Fase | Ruolo |", "|---|---|---|---|---|---|"]
    for e in m["models"]:
        lines.append(f"| {e['name']} | {e['version']} | {e['license']} | {'sì' if e['open_weights'] else 'no'} | "
                     f"{', '.join(e['stages'])} | {e['role']} |")
    target = (m.get("deployment") or {}).get("target")
    lines += ["", f"Architettura target (regola 5): {target or 'non ancora dichiarata'}."]
    seen: dict[str, int] = {}
    for d in run_dirs or []:
        meta = json.loads((Path(d) / "meta.json").read_text(encoding="utf-8"))
        seen[meta["model"]] = seen.get(meta["model"], 0) + 1
    if seen:
        lines += ["", "Modelli effettivamente comparsi nelle run analizzate:", ""]
        lines += [f"- `{name}` ({n} run){'' if _find_entry(m, name) else ' — NON DICHIARATO'}" for name, n in sorted(seen.items())]
    return "\n".join(lines) + "\n"
