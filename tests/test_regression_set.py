"""Set di regressione general-v0.1 (W13): ogni item ha una risposta corretta che passa i suoi controlli e una risposta vuota che fallisce."""
from pathlib import Path

import pytest

from agentbench.checks import CHECKS, Ctx
from agentbench.cli import main
from agentbench.tasks import load_tasks
from agentbench.types import Trajectory

ROOT = Path(__file__).resolve().parent.parent
TASKS = {t.id: t for t in load_tasks(ROOT / "tasks" / "regression")}
GOOD = {
    "train_arrival": "11:05", "notebooks": "21", "bottles": "12 litres", "stickers": "36", "mult": "391", "percent": "36", "discount": "120",
    "division": "125", "cm": "250", "minutes": "210", "aare": "Bern", "albula": "Thusis und St. Moritz", "marie": "Genève", "pears": "2",
    "dog": "Hund", "brot": "pain", "maison": "casa", "acqua": "water", "capital": "Bern", "cantons": "26", "biggest_city": "Zurich",
    "language": "tedesco", "json": '{"name": "Anna", "age": 30}', "three_colours": "rot, grün, blau", "seven": "sept", "eu": "no",
    "opposite": "cold", "spider": "8", "tuesday": "mercredi", "week": "7", "sort": "2, 4, 7, 9", "plural": "Häuser", "prime": "No",
    "nine_nine": "81", "contrary": "piccolo", "fractions": "3/4",
}


def passes(task, text):
    traj = Trajectory(final_text=text)
    return all(CHECKS[c["type"]](c, Ctx(traj, None))[0] for c in task.checks)


def test_set_shape_and_labels():
    assert len(TASKS) == 36 and {t.id.removeprefix("reg_") for t in TASKS.values()} == set(GOOD)
    splits = {t.meta["split"] for t in TASKS.values()}
    assert splits == {"regression_sanity", "regression_final"}
    assert {t.meta["language"] for t in TASKS.values()} == {"de", "fr", "it", "en"}
    assert all(t.tools == [] for t in TASKS.values())


@pytest.mark.parametrize("name", sorted(GOOD))
def test_correct_answer_passes_and_empty_answer_fails(name):
    t = TASKS[f"reg_{name}"]
    assert passes(t, GOOD[name]), t.prompt
    assert not passes(t, "I don't know."), t.prompt


def test_final_regression_set_is_protected(tmp_path):
    with pytest.raises(SystemExit) as e:
        main(["run", "--base-url", "http://127.0.0.1:1/v1", "--model", "m", "--tasks", str(ROOT / "tasks" / "regression"), "--out", str(tmp_path / "x")])
    assert "--final-test" in str(e.value.code) and not (tmp_path / "x").exists()
