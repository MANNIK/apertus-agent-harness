"""Server OpenAI-compatibile finto per i test: risponde seguendo una "policy" scritta nel test.

Una policy è una funzione (messages, tools, body) -> messaggio assistant (dict) oppure un
intero (codice HTTP di errore da restituire). Così i test controllano esattamente cosa "dice"
il modello e verificano che l'harness lo valuti correttamente, senza alcun modello vero.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

Policy = Callable[[list[dict], "list[dict] | None", dict], "dict | int"]


class MockServer:
    def __init__(self, policy: Policy) -> None:
        self.policy = policy
        self.requests: list[dict[str, Any]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:  # niente rumore nei test
                pass

            def _send(self, code: int, obj: dict) -> None:
                data = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                self._send(200, {"data": [{"id": "mock"}]})

            def do_POST(self) -> None:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append(body)
                result = outer.policy(body["messages"], body.get("tools"), body)
                if isinstance(result, int):
                    self._send(result, {"error": "boom"})
                    return
                self._send(200, {
                    "choices": [{"message": result, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                })

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"

    def __enter__(self) -> "MockServer":
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


# ----------------------------------------------------------------------------- messaggi

def native(name: str, args: dict) -> dict:
    """Tool call strutturata, come la restituirebbe vLLM con il parser giusto."""
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": "c1", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}


def prefix(name: str, args: dict) -> dict:
    """Tool call come testo grezzo con i marcatori di Apertus (server senza parser)."""
    return {"role": "assistant", "content": "<|tools_prefix|>" + json.dumps([{name: args}]) + "<|tools_suffix|>"}


def final(text: str) -> dict:
    return {"role": "assistant", "content": text}


def scripted(scripts: dict[str, list[dict]]) -> Policy:
    """Policy che riconosce il task dal primo messaggio utente e risponde con un copione.
    Il turno corrente è il numero di messaggi assistant già presenti nella conversazione."""
    def policy(messages, tools, body):
        user = next(m["content"] for m in messages if m["role"] == "user")
        script = scripts.get(user)
        if script is None:
            return final("(nessun copione per questo prompt)")
        turn = sum(1 for m in messages if m["role"] == "assistant")
        return script[turn] if turn < len(script) else final("done")
    return policy
