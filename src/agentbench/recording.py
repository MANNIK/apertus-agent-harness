"""Registrazione di ogni richiesta/risposta del modello, per poterle riprodurre (replay).

Perché serve: una valutazione è riproducibile davvero solo se chiunque (la giuria, un collega)
può rifare i conti senza avere il modello. Ogni run salva in `calls.jsonl` la richiesta
completa (prompt già renderizzato, tool, parametri) e la risposta grezza del server. Con
`agentbench run --replay <cartella>` le stesse risposte vengono riproposte al posto del modello:
l'harness rifà tutto il percorso e ri-valuta i risultati con i controlli attuali.

Chiave della richiesta: impronta (sha256) del corpo SENZA il nome del modello (un percorso
diverso su un altro computer non deve rompere il replay) e con gli id delle tool call sostituiti
da numeri d'ordine (gli id generati dal parser cambiano a ogni esecuzione).
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CALLS_FILE = "calls.jsonl"


def _normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids: dict[str, int] = {}

    def num(raw_id: Any) -> str:
        return f"call-{ids.setdefault(str(raw_id), len(ids))}"

    out = []
    for m in messages:
        m = copy.deepcopy(m)
        for tc in m.get("tool_calls") or []:
            if isinstance(tc, dict) and "id" in tc:
                tc["id"] = num(tc["id"])
        if "tool_call_id" in m:
            m["tool_call_id"] = num(m["tool_call_id"])
        out.append(m)
    return out


def request_key(body: dict[str, Any]) -> str:
    clean = {k: v for k, v in body.items() if k != "model"}
    clean["messages"] = _normalize_messages(clean.get("messages", []))
    blob = json.dumps(clean, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


class Recorder:
    """Aggiunge una riga a `calls.jsonl` per ogni risposta ricevuta (il file è creato vuoto)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def add(self, body: dict[str, Any], response: dict[str, Any], model: str) -> None:
        row = {
            "key": request_key(body),
            "model": model,
            "t": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "request": {k: v for k, v in body.items() if k != "model"},
            "response": response,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_calls(run_dir: str | Path) -> dict[str, list[dict[str, Any]]]:
    """chiave della richiesta -> risposte registrate, nell'ordine in cui sono arrivate."""
    path = Path(run_dir) / CALLS_FILE
    if not path.exists():
        raise FileNotFoundError(f"{path} non esiste: questa run è stata fatta senza registrazione delle risposte")
    calls: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            calls[row["key"]].append(row["response"])
    return calls


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
