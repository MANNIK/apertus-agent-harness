"""Analista dei dati aperti svizzeri (W10): applicazione dimostrativa self-hosted.

L'utente sceglie un dataset della Città di Zurigo (CC0), scrive una domanda in DE/FR/IT/EN; **Apertus** (originale o modificato, servito da un endpoint
OpenAI-compatibile LOCALE) scrive la query SQL, che il codice esegue su un database **DuckDB in sola lettura**; l'app mostra la query, la tabella dei
risultati e la risposta del modello. Chi fa cosa: Apertus = capire la domanda, scegliere tabelle/colonne, scrivere SQL, spiegare il risultato;
codice deterministico = costruire il database, eseguire la query (sola lettura, timeout, limiti), mostrare i risultati. Nessun altro modello, nessuna API esterna.

Sicurezza e sovranità: il server ascolta SOLO su 127.0.0.1; la pagina non carica nulla dall'esterno (niente CDN, font o script remoti); il testo del modello
viene inserito nella pagina come testo (mai come HTML). L'unica connessione in uscita è quella verso l'endpoint del modello (variabile APERTUS_BASE_URL).

Uso (dalla radice del progetto, con il server del modello acceso, es. `scripts/serve_mlx.sh`):
    export APERTUS_BASE_URL=http://localhost:8080/v1 APERTUS_MODEL="<percorso o nome del modello>"
    .venv/bin/python app/analyst.py [--port 8765] [--thinking off]
Poi apri http://127.0.0.1:8765/ . Un modello alla volta: per confrontare originale e modificato riavvia il server del modello con l'altro checkpoint.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml

from agentbench.client import ChatClient, ChatError
from agentbench.runner import run_task
from agentbench.sql_env import SQL_SYSTEM, SqlBox
from agentbench.tasks import Task

ROOT = Path(__file__).resolve().parent.parent
MAX_QUESTION = 500
MAX_ROWS_SHOWN = 200
_MODEL_LOCK = threading.Lock()  # un solo modello locale: una domanda alla volta


def load_schemas() -> dict[str, dict[str, Any]]:
    """Schemi disponibili, ricavati dai file dei task (setup del DB, titolo dal manifesto dei dati, domande d'esempio da dev/val)."""
    manifest = {m["dataset"]: m for m in json.loads((ROOT / "data" / "zurich" / "MANIFEST.json").read_text(encoding="utf-8"))}
    out: dict[str, dict[str, Any]] = {}
    for f in sorted((ROOT / "tasks" / "zurich").glob("*/*.yaml")):
        tasks = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        if not tasks:
            continue
        meta = tasks[0]["meta"]
        entry = out.setdefault(meta["schema_id"], {
            "id": meta["schema_id"], "title": manifest[meta["dataset"]]["title"], "source": manifest[meta["dataset"]]["source_page"],
            "setup": tasks[0]["setup"], "examples": []})
        if meta["split"] in ("dev", "val"):  # gli esempi non vengono dal test set
            entry["examples"] = [{"language": t["meta"]["language"], "question": t["prompt"]} for t in tasks[:4]]
    return out


def ask(client: ChatClient, schema: dict[str, Any], question: str) -> dict[str, Any]:
    """Una domanda → il ciclo agentico del progetto (stesso codice delle valutazioni) → risultato serializzabile."""
    task = Task(id="app", category="app", prompt=question, checks=[], tools=["run_sql"], setup=schema["setup"], max_steps=6)
    box = SqlBox(schema["setup"])
    try:
        t0 = time.time()
        with _MODEL_LOCK:
            traj = run_task(client, task, box, default_system=SQL_SYSTEM)
        queries = [{"sql": c.arguments.get("query", ""), "ok": r.ok, "message": "" if r.ok else r.content} for c, r in traj.pairs if c.name == "run_sql"]
        res = box.last_result
        rows = [[None if v is None else (v if isinstance(v, (int, float, str, bool)) else str(v)) for v in row] for row in (res.rows[:MAX_ROWS_SHOWN] if res else [])]
        return {"answer": traj.final_text, "queries": queries, "columns": res.columns if res else [], "rows": rows,
                "n_rows": len(res.rows) if res else 0, "steps": len(traj.steps), "stopped": traj.stopped, "error": traj.error,
                "seconds": round(time.time() - t0, 1), "model": client.model}
    finally:
        box.close()


PAGE = """<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Analista dei dati aperti svizzeri</title>
<style>
:root{color-scheme:light dark;--bg:#fff;--fg:#1c1c1e;--mut:#6b6b70;--line:#d8d8dc;--acc:#b3001b;--card:#f5f5f7}
@media (prefers-color-scheme:dark){:root{--bg:#161618;--fg:#f2f2f4;--mut:#a0a0a8;--line:#3a3a3f;--acc:#ff5a6e;--card:#222226}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}main{max-width:900px;margin:0 auto;padding:16px}
h1{font-size:1.4rem;margin:.2em 0}small,.mut{color:var(--mut)}select,textarea,button{font:inherit;width:100%;box-sizing:border-box;margin:.3em 0;padding:.5em;
border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg)}button{background:var(--acc);color:#fff;border:0;cursor:pointer}button:disabled{opacity:.5}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;margin:12px 0}pre{white-space:pre-wrap;margin:0;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{border:1px solid var(--line);padding:4px 8px;text-align:left}.wrap{overflow-x:auto}
.chips button{width:auto;margin:2px 4px 2px 0;background:var(--card);color:var(--fg);border:1px solid var(--line);font-size:.85rem}.err{color:var(--acc)}
</style></head><body><main>
<h1>Analista dei dati aperti svizzeri</h1>
<p class="mut">Apertus scrive la query SQL, il codice la esegue in locale su un database in sola lettura. Nessun dato lascia questo computer.</p>
<label>Dataset (Città di Zurigo, CC0)<select id="schema"></select></label><small id="src" class="mut"></small>
<div class="chips" id="ex"></div>
<label>Domanda (DE / FR / IT / EN)<textarea id="q" rows="3" maxlength="500"></textarea></label>
<button id="go">Chiedi</button><div id="status" class="mut"></div><div id="out"></div>
<p class="mut" id="model"></p></main>
<script>
const $=id=>document.getElementById(id);let schemas={};
function el(t,txt,cls){const e=document.createElement(t);if(txt!==undefined)e.textContent=txt;if(cls)e.className=cls;return e}
async function init(){const r=await fetch('/api/schemas');schemas=await r.json();const s=$('schema');
 Object.values(schemas.schemas).forEach(x=>{const o=el('option',x.title);o.value=x.id;s.appendChild(o)});$('model').textContent='Modello: '+schemas.model;pick()}
function pick(){const x=schemas.schemas[$('schema').value];$('src').textContent='Fonte: '+x.source;const ex=$('ex');ex.replaceChildren();
 x.examples.forEach(e=>{const b=el('button',e.language.toUpperCase()+' · '+e.question);b.onclick=()=>{$('q').value=e.question};ex.appendChild(b)})}
$('schema').onchange=pick;
$('go').onclick=async()=>{const q=$('q').value.trim();if(!q)return;$('go').disabled=true;$('status').textContent='Apertus sta lavorando… (può richiedere decine di secondi)';$('out').replaceChildren();
 try{const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:$('schema').value,question:q})});const d=await r.json();
  if(d.error&&!d.queries){$('out').appendChild(el('p',d.error,'err'))}else{show(d)}}catch(e){$('out').appendChild(el('p','Errore: '+e,'err'))}
 $('go').disabled=false;$('status').textContent=''};
function show(d){const o=$('out');
 const a=el('div',undefined,'card');a.appendChild(el('strong','Risposta'));a.appendChild(el('pre',d.answer||'(nessuna risposta finale: '+d.stopped+')'));o.appendChild(a);
 d.queries.forEach((x,i)=>{const c=el('div',undefined,'card');c.appendChild(el('strong','Query '+(i+1)+(x.ok?'':' (errore)')));c.appendChild(el('pre',x.sql));
  if(!x.ok)c.appendChild(el('pre',x.message,'err'));o.appendChild(c)});
 if(d.columns.length){const c=el('div',undefined,'card');c.appendChild(el('strong','Risultato dell\\'ultima query riuscita ('+d.n_rows+' righe)'));const w=el('div',undefined,'wrap');const t=el('table');
  const h=el('tr');d.columns.forEach(k=>h.appendChild(el('th',k)));t.appendChild(h);
  d.rows.forEach(r=>{const tr=el('tr');r.forEach(v=>tr.appendChild(el('td',v===null?'NULL':String(v))));t.appendChild(tr)});w.appendChild(t);c.appendChild(w);o.appendChild(c)}
 o.appendChild(el('p',d.steps+' passi · '+d.seconds+' s · '+d.model,'mut'))}
init();
</script></body></html>"""


def make_handler(client: ChatClient, schemas: dict[str, dict[str, Any]]):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:  # niente rumore, e niente domande dell'utente nei log
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj: Any) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self) -> None:
            if self.path == "/":
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/api/schemas":
                public = {k: {x: v[x] for x in ("id", "title", "source", "examples")} for k, v in schemas.items()}
                self._json(200, {"schemas": public, "model": client.model})
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self) -> None:
            if self.path != "/api/ask":
                return self._send(404, b"not found", "text/plain")
            try:
                n = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(min(n, 10_000)) or b"{}")
                schema, question = schemas.get(str(data.get("schema"))), str(data.get("question", "")).strip()
            except (ValueError, UnicodeDecodeError):
                return self._json(400, {"error": "richiesta non valida"})
            if schema is None:
                return self._json(400, {"error": "dataset sconosciuto"})
            if not question or len(question) > MAX_QUESTION:
                return self._json(400, {"error": f"la domanda deve avere da 1 a {MAX_QUESTION} caratteri"})
            try:
                self._json(200, ask(client, schema, question))
            except ChatError as e:
                self._json(502, {"error": f"il modello non risponde: {e}"})

    return Handler


def make_server(client: ChatClient, port: int = 8765) -> ThreadingHTTPServer:
    """Server locale: ascolta SOLO su 127.0.0.1."""
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(client, load_schemas()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--base-url", default=os.environ.get("APERTUS_BASE_URL") or os.environ.get("LLM_BASE_URL"))
    ap.add_argument("--model", default=os.environ.get("APERTUS_MODEL") or os.environ.get("LLM_NAME"))
    ap.add_argument("--api-key", default=os.environ.get("APERTUS_API_KEY") or os.environ.get("LLM_API_KEY") or "none")
    ap.add_argument("--thinking", choices=["on", "off"], default="off", help="ragionamento di Apertus (stesso significato delle valutazioni)")
    ap.add_argument("--timeout", type=float, default=600.0)
    args = ap.parse_args()
    if not args.base_url or not args.model:
        sys.exit("servono l'endpoint e il modello: APERTUS_BASE_URL e APERTUS_MODEL (oppure --base-url e --model)")
    extra = {"chat_template_kwargs": {"enable_thinking": args.thinking == "on"}}
    client = ChatClient(args.base_url, args.model, args.api_key, 0.0, 1024, None, extra, args.timeout)
    srv = make_server(client, args.port)
    print(f"Analista su http://127.0.0.1:{srv.server_address[1]}/  · modello: {client.model} · endpoint: {client.base_url}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
