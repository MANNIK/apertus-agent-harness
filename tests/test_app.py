"""Applicazione dimostrativa (app/analyst.py) contro un modello finto: schemi, domanda → query → risultato, input non validi, solo localhost."""
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("duckdb")

from agentbench.client import ChatClient  # noqa: E402
from mock_server import MockServer, final, native  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
import analyst  # noqa: E402


def http(port, path, data=None):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=None if data is None else json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


@pytest.fixture
def app():
    def policy(messages, tools, body):
        assert [t["function"]["name"] for t in tools] == ["run_sql"]
        turn = sum(1 for m in messages if m["role"] == "assistant")
        if turn == 0:
            return native("run_sql", {"query": "SELECT SUM(AnzBestWir) AS einwohner FROM bevoelkerung_quartier WHERE StichtagDatJahr = 2023"})
        return final("Nel 2023 la città di Zurigo contava 447082 abitanti.")
    with MockServer(policy) as model:
        client = ChatClient(model.url, "mock-model", retries=0, timeout=10)
        srv = analyst.make_server(client, 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            yield srv.server_address[1], model
        finally:
            srv.shutdown()
            srv.server_close()


def test_server_listens_only_on_localhost(app):
    port, _ = app
    assert analyst.make_server.__doc__ and "127.0.0.1" in analyst.make_server.__doc__
    import socket
    s = socket.socket()
    try:
        assert s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def test_page_has_no_external_resources_and_lists_schemas(app):
    port, _ = app
    code, page = http(port, "/")
    html = page.decode("utf-8")
    assert code == 200 and "http://" not in html and "https://" not in html and "src=" not in html and "innerHTML" not in html
    code, body = http(port, "/api/schemas")
    d = json.loads(body)
    assert code == 200 and d["model"] == "mock-model" and len(d["schemas"]) == 15
    assert "setup" not in d["schemas"]["bevq"] and d["schemas"]["bevq"]["source"].startswith("https://data.stadt-zuerich.ch/")
    assert all(e["language"] in {"de", "fr", "it", "en"} for s in d["schemas"].values() for e in s["examples"])


def test_examples_never_come_from_the_test_split(app):
    port, _ = app
    d = json.loads(http(port, "/api/schemas")[1])
    test_schemas = {"abst", "luft", "wett", "feue", "rett", "kpi"}
    assert all(d["schemas"][s]["examples"] == [] for s in test_schemas)
    assert all(d["schemas"][s]["examples"] for s in ("bevq", "eink"))


def test_ask_runs_the_query_and_returns_table_and_answer(app):
    port, model = app
    code, body = http(port, "/api/ask", {"schema": "bevq", "question": "Wie viele Personen wohnten 2023 in Zürich?"})
    d = json.loads(body)
    assert code == 200 and d["stopped"] == "final" and d["model"] == "mock-model"
    assert d["queries"][0]["ok"] and "SUM(AnzBestWir)" in d["queries"][0]["sql"]
    assert d["columns"] == ["einwohner"] and d["rows"] == [[447082]] and "447082" in d["answer"]
    first_user = next(m["content"] for m in model.requests[0]["messages"] if m["role"] == "user")
    assert first_user.startswith("Database schema (DuckDB):") and "Question: Wie viele Personen" in first_user


def test_invalid_requests_are_rejected_without_calling_the_model(app):
    port, model = app
    assert http(port, "/api/ask", {"schema": "nope", "question": "x"})[0] == 400
    assert http(port, "/api/ask", {"schema": "bevq", "question": ""})[0] == 400
    assert http(port, "/api/ask", {"schema": "bevq", "question": "x" * 501})[0] == 400
    assert http(port, "/nope")[0] == 404
    assert model.requests == []


def test_model_error_is_reported_not_raised():
    with MockServer(lambda m, t, b: 500) as model:
        client = ChatClient(model.url, "mock-model", retries=0, timeout=10)
        srv = analyst.make_server(client, 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            code, body = http(srv.server_address[1], "/api/ask", {"schema": "bevq", "question": "Quanti abitanti?"})
            d = json.loads(body)
            assert code == 200 and d["stopped"] == "error" and d["error"] and d["answer"] == ""
        finally:
            srv.shutdown()
            srv.server_close()
