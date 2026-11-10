"""La run sintetica di riferimento (oracolo SQL) deve essere integra e rigiocabile con il 100%."""
import json
from pathlib import Path

import pytest

pytest.importorskip("duckdb")

from agentbench.cli import main  # noqa: E402
from agentbench.compliance import check  # noqa: E402
from agentbench.recording import file_sha256  # noqa: E402
from agentbench.tasks import load_tasks  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "reference_runs" / "demo-oracle-sql"


def test_demo_is_marked_synthetic_and_intact():
    assert (DEMO / "LEGGIMI.md").exists()
    meta = json.loads((DEMO / "meta.json").read_text(encoding="utf-8"))
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
