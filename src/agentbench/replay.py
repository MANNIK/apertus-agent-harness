"""Client che non parla con nessun modello: ripropone le risposte registrate da una run precedente."""
from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .client import ChatClient, ChatError
from .recording import load_calls, request_key


class ReplayMiss(ChatError):
    """La richiesta non corrisponde a nessuna risposta registrata (prompt, tool o parametri diversi)."""


class ReplayClient(ChatClient):
    """Stessa interfaccia di ChatClient. Modello, temperatura, ecc. sono quelli della run di origine."""

    def __init__(self, run_dir: str | Path) -> None:
        run_dir = Path(run_dir)
        meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        super().__init__(
            meta["base_url"], meta["model"], "none", meta["temperature"], meta["max_tokens"],
            meta.get("seed"), meta.get("extra_body") or {}, retries=0,
        )
        self.source_meta = meta
        self.meta_extra = {"replay_of": str(run_dir)}
        self._calls = load_calls(run_dir)
        self._served: Counter[str] = Counter()

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any]:
        body = self._body(messages, tools)
        key = request_key(body)
        queue = self._calls.get(key, [])
        n = self._served[key]
        if n >= len(queue):
            raise ReplayMiss(
                f"replay: nessuna risposta registrata per questa richiesta (chiave {key}). "
                "Sono cambiati prompt di sistema, task, tool o parametri rispetto alla run di origine?"
            )
        self._served[key] += 1
        resp = copy.deepcopy(queue[n])
        if self.recorder is not None:
            self.recorder.add(body, resp, self.model)
        return resp
