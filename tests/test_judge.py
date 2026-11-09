"""Giudice opzionale: formato dei giudizi, confronto con i controlli automatici, rispetto della regola 4."""
import json
from pathlib import Path

import pytest

from agentbench.bench import run_suite
from agentbench.cli import main
from agentbench.client import ChatClient
from agentbench.judge import agreement, judge_run, parse_verdict, render_agreement, render_trajectory
from agentbench.stats import cohen_kappa
from agentbench.tasks import load_tasks
from mock_server import MockServer, final, native, scripted

ROOT = Path(__file__).resolve().parent.parent
TASKS = {t.id: t for t in load_tasks(ROOT / "tasks")}
IDS = ["sc_weather_it", "ms_weather_diff"]
SCRIPTS = {
    TASKS["sc_weather_it"].prompt: [native("get_weather", {"city": "Lugano"}), final("A Lugano ci sono 12 °C.")],
    TASKS["ms_weather_diff"].prompt: [native("get_weather", {"city": "Lugano"}), final("Lugano is warmer.")],  # incompleto: FAIL
}
TOOLS = {i: list(t.tools) for i, t in TASKS.items()}


@pytest.fixture()
def run_dir(tmp_path):
    with MockServer(scripted(SCRIPTS)) as srv:
        recs = run_suite(ChatClient(srv.url, "apertus-test", retries=0, timeout=10), [TASKS[i] for i in IDS], 1, tmp_path / "r")
    assert [r["passed"] for r in recs] == [True, False]
    return tmp_path / "r"


def verdict_policy(answers):
    def policy(messages, tools, body):
        text = messages[-1]["content"]
        key = "A Lugano ci sono" if "A Lugano ci sono" in text else "Lugano is warmer"
        return final(answers[key])
    return policy


def test_parse_verdict_variants():
    assert parse_verdict('{"verdict": "pass", "violated": [], "reason": "ok"}') == ("PASS", [], "ok")
    assert parse_verdict('Certo!\n```json\n{"verdict": "FAIL", "violated": [3], "reason": "inventato"}\n```')[:2] == ("FAIL", [3])
    assert parse_verdict("non so")[0] == "UNPARSEABLE" and parse_verdict('{"verdict": "forse"}')[0] == "UNPARSEABLE"


def test_kappa_known_values():
    assert cohen_kappa(5, 0, 0, 5) == 1.0
    assert abs(cohen_kappa(5, 5, 5, 5)) < 1e-9          # accordo casuale
    assert cohen_kappa(0, 0, 0, 0) is None


def test_trajectory_rendering_shows_calls_and_results(run_dir):
    rec = json.loads((run_dir / "results.jsonl").read_text().splitlines()[0])
    text = render_trajectory(rec["trajectory"])
    assert "CALL get_weather" in text and "RESULT get_weather [ok]" in text


def test_judge_agreeing_with_checks_gives_perfect_agreement_and_saves_metadata(run_dir):
    good = {"A Lugano ci sono": '{"verdict": "PASS", "violated": [], "reason": "ok"}',
            "Lugano is warmer": '{"verdict": "FAIL", "violated": [3], "reason": "manca Zurigo"}'}
    with MockServer(verdict_policy(good)) as srv:
        client = ChatClient(srv.url, "qwen-judge-open", retries=0, timeout=10)
        res = judge_run(run_dir, client, ROOT / "rubrics" / "agentic_v1.md", TOOLS)
    a = agreement(res["rows"])
    assert a["n"] == 2 and a["agree"] == 1.0 and a["kappa"] == 1.0
    meta = json.loads((run_dir / "judge_meta.json").read_text())
    assert meta["model"] == "qwen-judge-open" and meta["temperature"] == 0.0 and len(meta["rubric_sha256"]) == 64
    assert meta["same_model_as_tested"] is False
    assert len((run_dir / "judge.jsonl").read_text().splitlines()) == 2


def test_lenient_judge_is_exposed_as_disagreement(run_dir):
    lenient = {k: '{"verdict": "PASS", "violated": [], "reason": "sembra ok"}' for k in ("A Lugano ci sono", "Lugano is warmer")}
    with MockServer(verdict_policy(lenient)) as srv:
        res = judge_run(run_dir, ChatClient(srv.url, "j", retries=0, timeout=10), ROOT / "rubrics" / "agentic_v1.md", TOOLS)
    a = agreement(res["rows"])
    assert a["agree"] == 0.5 and [r["task_id"] for r in a["auto_fail_judge_pass"]] == ["ms_weather_diff"]
    assert "controlli troppo severi" in render_agreement(res) and "ms_weather_diff" in render_agreement(res)


def test_same_model_as_tested_is_warned(run_dir):
    good = {"A Lugano ci sono": '{"verdict": "PASS"}', "Lugano is warmer": '{"verdict": "FAIL"}'}
    with MockServer(verdict_policy(good)) as srv:
        res = judge_run(run_dir, ChatClient(srv.url, "apertus-test", retries=0, timeout=10), ROOT / "rubrics" / "agentic_v1.md", TOOLS)
    assert res["meta"]["same_model_as_tested"] and "coincide con il modello sotto test" in render_agreement(res)


def test_unparseable_and_failed_judgements_are_not_counted_as_agreement(run_dir):
    with MockServer(lambda m, t, b: final("boh")) as srv:
        res = judge_run(run_dir, ChatClient(srv.url, "j", retries=0, timeout=10), ROOT / "rubrics" / "agentic_v1.md", TOOLS)
    a = agreement(res["rows"])
    assert a["n"] == 0 and a["unusable"] == 2 and "Nessun giudizio utilizzabile" in render_agreement(res)


def test_cli_judge_writes_report(run_dir, capsys):
    good = {"A Lugano ci sono": '{"verdict": "PASS"}', "Lugano is warmer": '{"verdict": "FAIL"}'}
    with MockServer(verdict_policy(good)) as srv:
        with pytest.raises(SystemExit) as e:
            main(["judge", str(run_dir), "--judge-base-url", srv.url, "--judge-model", "qwen-judge-open",
                  "--rubric", str(ROOT / "rubrics" / "agentic_v1.md"), "--tasks", str(ROOT / "tasks")])
    assert e.value.code == 0 and (run_dir / "judge_report.md").exists() and "Accordo: 100%" in capsys.readouterr().out


def test_closed_model_as_judge_fails_compliance(run_dir):
    from agentbench.compliance import check
    (run_dir / "judge_meta.json").write_text(json.dumps({"model": "claude-sonnet-5-5"}))
    assert any("giudice" in f.message and f.level == "ERROR" for f in check(ROOT / "models.yaml", [run_dir]))
