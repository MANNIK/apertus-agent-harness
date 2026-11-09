"""Registrazione e replay: la stessa run si può rifare senza modello, e la modifica di una
qualunque parte della richiesta viene segnalata invece di essere ignorata."""
import json
from pathlib import Path

import pytest

from agentbench.bench import run_suite
from agentbench.cli import main
from agentbench.client import ChatClient
from agentbench.recording import CALLS_FILE, file_sha256, request_key
from agentbench.replay import ReplayClient
from agentbench.tasks import load_tasks
from mock_server import MockServer, final, native, prefix, scripted

ROOT = Path(__file__).resolve().parent.parent
TASKS = {t.id: t for t in load_tasks(ROOT / "tasks")}
P = {tid: t.prompt for tid, t in TASKS.items()}
IDS = ["sc_weather_it", "ms_weather_diff", "er_flaky_weather"]
SCRIPTS = {
    P["sc_weather_it"]: [prefix("get_weather", {"city": "Lugano"}), final("A Lugano ci sono 12 °C.")],
    P["ms_weather_diff"]: [native("get_weather", {"city": "Lugano"}), native("get_weather", {"city": "Zurich"}),
                           final("Lugano is warmer: 12°C vs 8°C, a difference of 4 degrees.")],
    P["er_flaky_weather"]: [native("get_weather", {"city": "Lugano"}), final("The weather service failed.")],
}


def live_run(out: Path):
    with MockServer(scripted(SCRIPTS)) as srv:
        client = ChatClient(srv.url, "modello-sul-mio-mac", retries=0, timeout=10)
        return run_suite(client, [TASKS[i] for i in IDS], 1, out)


def test_live_run_records_every_call_and_file_hashes(tmp_path):
    recs = live_run(tmp_path / "a")
    rows = [json.loads(x) for x in (tmp_path / "a" / CALLS_FILE).read_text().splitlines()]
    assert len(rows) == sum(r["n_steps"] for r in recs)
    assert {"key", "model", "request", "response"} <= set(rows[0]) and "model" not in rows[0]["request"]
    meta = json.loads((tmp_path / "a" / "meta.json").read_text())
    assert meta["files_sha256"]["calls.jsonl"] == file_sha256(tmp_path / "a" / CALLS_FILE)
    assert meta["recorded_calls"] is True


def test_replay_reproduces_results_without_any_server(tmp_path):
    live = {r["task_id"]: r for r in live_run(tmp_path / "a")}
    # il server finto è già chiuso: se il replay provasse la rete fallirebbe
    client = ReplayClient(tmp_path / "a")
    again = {r["task_id"]: r for r in run_suite(client, [TASKS[i] for i in IDS], 1, tmp_path / "b")}
    assert {k: v["passed"] for k, v in live.items()} == {k: v["passed"] for k, v in again.items()}
    assert {k: v["final_text"] for k, v in live.items()} == {k: v["final_text"] for k, v in again.items()}
    assert json.loads((tmp_path / "b" / "meta.json").read_text())["replay_of"] == str(tmp_path / "a")
    # il replay registra a sua volta (si può rifare il replay di un replay): stesse chiavi, stesse risposte.
    # Il testo grezzo delle richieste può differire solo per gli id casuali delle tool call.
    def rows(d):
        return [(r["key"], r["response"]) for r in map(json.loads, (d / CALLS_FILE).read_text().splitlines())]
    assert rows(tmp_path / "b") == rows(tmp_path / "a")


def test_text_format_calls_with_random_ids_still_match(tmp_path):
    """Le tool call in testo ottengono un id casuale dal parser: la chiave non deve dipendere da esso."""
    live_run(tmp_path / "a")
    client = ReplayClient(tmp_path / "a")
    rec = run_suite(client, [TASKS["sc_weather_it"]], 1, tmp_path / "b")[0]
    assert rec["passed"] and rec["parse_sources"] == ["prefix_tag"]


def test_changed_system_prompt_is_a_replay_miss_not_a_silent_pass(tmp_path):
    live_run(tmp_path / "a")
    client = ReplayClient(tmp_path / "a")
    rec = run_suite(client, [TASKS["sc_weather_it"]], 1, tmp_path / "b", system_prompt="Altro prompt")[0]
    assert rec["stopped"] == "error" and "replay" in rec["error"] and not rec["passed"]


def test_request_key_ignores_model_name_and_call_ids_but_not_content():
    base = {"model": "A", "temperature": 0.0, "messages": [
        {"role": "user", "content": "ciao"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "x1", "type": "function", "function": {"name": "f", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "x1", "content": "ok"}]}
    other = json.loads(json.dumps(base))
    other["model"] = "B"
    other["messages"][1]["tool_calls"][0]["id"] = "zzz"
    other["messages"][2]["tool_call_id"] = "zzz"
    assert request_key(base) == request_key(other)
    other["messages"][2]["content"] = "diverso"
    assert request_key(base) != request_key(other)


def test_same_request_repeated_is_served_in_order(tmp_path):
    scripts = {P["sc_weather_it"]: [final("uno")]}
    with MockServer(lambda m, t, b: final("risposta")) as srv:
        client = ChatClient(srv.url, "m", retries=0, timeout=10)
        run_suite(client, [TASKS["ab_no_tool_needed"]], 3, tmp_path / "a")  # 3 ripetizioni, stessa richiesta
    rc = ReplayClient(tmp_path / "a")
    recs = run_suite(rc, [TASKS["ab_no_tool_needed"]], 3, tmp_path / "b")
    assert [r["stopped"] for r in recs] == ["final"] * 3
    with pytest.raises(Exception):
        rc.chat([{"role": "system", "content": "x"}])  # richiesta mai vista


def test_cli_replay_needs_no_model_and_reuses_recorded_prompt(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("APERTUS_MODEL", raising=False)
    monkeypatch.delenv("LLM_NAME", raising=False)
    live_run(tmp_path / "a")
    with pytest.raises(SystemExit) as e:
        main(["run", "--replay", str(tmp_path / "a"), "--tasks", str(ROOT / "tasks"),
              "--only", ",".join(IDS), "--out", str(tmp_path / "b")])
    assert e.value.code == 0
    assert "2/3 esecuzioni passate" in capsys.readouterr().out  # er_flaky_weather era un FAIL anche nell'originale


def test_replay_of_run_without_recording_explains_itself(tmp_path):
    with MockServer(scripted(SCRIPTS)) as srv:
        client = ChatClient(srv.url, "m", retries=0, timeout=10)
        run_suite(client, [TASKS["sc_weather_it"]], 1, tmp_path / "a", record=False)
    with pytest.raises(FileNotFoundError, match="senza registrazione"):
        ReplayClient(tmp_path / "a")


def test_llm_env_variables_are_accepted(monkeypatch):
    monkeypatch.delenv("APERTUS_BASE_URL", raising=False)
    monkeypatch.delenv("APERTUS_MODEL", raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "http://example.invalid/v1")
    monkeypatch.setenv("LLM_NAME", "swiss-ai/Apertus-v1.5-8B")
    from agentbench import cli
    import argparse
    p = argparse.ArgumentParser()
    cli._add_model_args(p)
    a = p.parse_args([])
    assert a.base_url == "http://example.invalid/v1" and a.model == "swiss-ai/Apertus-v1.5-8B"
