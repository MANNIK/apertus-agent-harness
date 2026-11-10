"""La run sintetica di riferimento deve essere integra e rigiocabile con il 100% (62/62)."""
import json
from pathlib import Path

import pytest

from agentbench.cli import main
from agentbench.compliance import check
from agentbench.recording import file_sha256
from agentbench.tasks import load_tasks

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "reference_runs" / "demo-oracle"


def test_demo_is_marked_synthetic_and_intact():
    assert (DEMO / "LEGGIMI.md").exists()
    meta = json.loads((DEMO / "meta.json").read_text())
    assert meta["model"] == "demo-oracle-synthetic"
    for name, digest in meta["files_sha256"].items():
        assert file_sha256(DEMO / name) == digest


def test_demo_replays_all_tasks(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        main(["run", "--replay", str(DEMO), "--out", str(tmp_path / "o"), "--tasks", str(ROOT / "tasks")])
    assert e.value.code == 0
    n = len(load_tasks(ROOT / "tasks"))
    assert f"{n}/{n} esecuzioni passate" in capsys.readouterr().out


def test_demo_has_no_compliance_errors():
    assert not [f for f in check(ROOT / "models.yaml", [DEMO]) if f.level == "ERROR"]
