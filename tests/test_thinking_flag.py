"""`--thinking on|off` passa chat_template_kwargs.enable_thinking (variabile letta dal chat template di Apertus);
senza il flag non viene inviato nulla."""
import json
from pathlib import Path

import pytest

from agentbench.cli import main
from agentbench.report import render_compare
from mock_server import MockServer, final, scripted
from agentbench.tasks import load_tasks

ROOT = Path(__file__).resolve().parent.parent
TASK = [t for t in load_tasks(ROOT / "tasks") if t.id == "ab_no_tool_needed"][0]


def run_cli(tmp_path, name, *flags):
    with MockServer(scripted({TASK.prompt: [final("Paris")]})) as srv:
        with pytest.raises(SystemExit) as e:
            main(["run", "--base-url", srv.url, "--model", "mock", "--only", TASK.id, "--tasks", str(ROOT / "tasks"),
                  "--out", str(tmp_path / name), *flags])
        assert e.value.code == 0
    return srv.requests[0], json.loads((tmp_path / name / "meta.json").read_text())


def test_flag_sets_enable_thinking_in_request_and_meta(tmp_path):
    for value, expected in (("off", False), ("on", True)):
        req, meta = run_cli(tmp_path, value, "--thinking", value)
        assert req["chat_template_kwargs"] == {"enable_thinking": expected}
        assert meta["extra_body"] == {"chat_template_kwargs": {"enable_thinking": expected}}


def test_without_flag_nothing_is_sent(tmp_path):
    req, meta = run_cli(tmp_path, "d")
    assert "chat_template_kwargs" not in req and meta["extra_body"] == {}


def test_flag_merges_with_extra_body_and_compare_shows_it(tmp_path):
    req, _ = run_cli(tmp_path, "m", "--thinking", "off", "--extra-body", '{"chat_template_kwargs": {"x": 1}, "top_k": 5}')
    assert req["chat_template_kwargs"] == {"x": 1, "enable_thinking": False} and req["top_k"] == 5
    run_cli(tmp_path, "d")
    assert "extra_body" in render_compare(tmp_path / "d", tmp_path / "m")
