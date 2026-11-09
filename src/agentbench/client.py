"""Client minimale per endpoint OpenAI-compatibili (/v1/chat/completions).

Usiamo httpx direttamente (e non l'SDK openai) perché ci serve il messaggio *grezzo* del
server: se il server non converte l'output del modello in `tool_calls`, il testo grezzo è
l'unico modo per capire cosa è successo e per applicare il parser di fallback.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from .recording import Recorder


class ChatError(RuntimeError):
    """Errore di rete o risposta HTTP non valida dal server."""


class ChatClient:
    # Campi extra scritti in meta.json (es. `replay_of` nel replay).
    meta_extra: dict[str, Any] = {}
    recorder: Recorder | None = None

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "none",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        seed: int | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: float = 300.0,
        retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.extra_body = extra_body or {}
        self.retries = retries
        self._http = httpx.Client(timeout=timeout)
        self.meta_extra = {}
        self.recorder = None

    def record_to(self, path) -> None:
        """Da questo momento ogni risposta ricevuta viene salvata (richiesta completa inclusa)."""
        self.recorder = Recorder(path)

    def _body(self, messages: list[dict], tools: list[dict] | None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if tools:
            body["tools"] = tools
        if self.seed is not None:
            body["seed"] = self.seed
        body.update(self.extra_body)  # es. {"chat_template_kwargs": {"enable_thinking": false}}
        return body

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any]:
        """Esegue una richiesta e restituisce message, finish_reason, usage e latenza."""
        url = f"{self.base_url}/chat/completions"
        body = self._body(messages, tools)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            t0 = time.perf_counter()
            try:
                r = self._http.post(url, json=body, headers=headers)
            except httpx.TransportError as e:  # connessione rifiutata, timeout, ecc.
                last_exc = e
                time.sleep(min(2**attempt, 4))
                continue
            latency = time.perf_counter() - t0
            if r.status_code != 200:
                raise ChatError(f"HTTP {r.status_code}: {r.text[:500]}")
            try:
                data = r.json()
                choice = data["choices"][0]
                result = {
                    "message": choice["message"],
                    "finish_reason": choice.get("finish_reason"),
                    "usage": data.get("usage") or {},
                    "latency_s": latency,
                }
            except (ValueError, KeyError, IndexError) as e:
                raise ChatError(f"risposta non valida dal server: {e}; corpo: {r.text[:300]}") from e
            if self.recorder is not None:
                self.recorder.add(body, result, self.model)
            return result
        raise ChatError(f"server non raggiungibile a {url}: {last_exc}")
