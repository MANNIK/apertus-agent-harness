"""Dataset Text-to-SQL "zurich-sql" (dati reali CC0): licenze, impronte, split per schema, gold risolvibili, rigenerazione e protezione del test set."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml

pytest.importorskip("duckdb")

from agentbench.checks import CHECKS, Ctx  # noqa: E402
from agentbench.cli import main  # noqa: E402
from agentbench.sql_env import make_box  # noqa: E402
from agentbench.tasks import load_tasks  # noqa: E402
from agentbench.types import ToolCall, Trajectory  # noqa: E402
from mock_server import MockServer, final  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "tasks" / "zurich"
DATA = ROOT / "data" / "zurich"
SPLITS = json.loads((ZH / "SPLITS.json").read_text(encoding="utf-8"))
BY_SPLIT = {s: load_tasks(ZH / s) for s in ("dev", "val", "test")}
ALL = [t for ts in BY_SPLIT.values() for t in ts]
MANIFEST = {m["dataset"]: m for m in json.loads((DATA / "MANIFEST.json").read_text(encoding="utf-8"))}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_every_dataset_is_cc0_and_matches_its_recorded_hash():
    assert MANIFEST
    for name, m in MANIFEST.items():
        assert m["license_id"] == "cc-zero" and m["license_title"], name
        assert m["source_page"].startswith("https://data.stadt-zuerich.ch/dataset/")
        assert sha(ROOT / m["file"]) == m["sha256"] and (ROOT / m["file"]).stat().st_size == m["bytes"], name


def test_task_files_match_the_recorded_fingerprints_and_counts():
    for split, info in SPLITS.items():
        assert info["n_tasks"] == len(BY_SPLIT[split])
        for rel, digest in info["files"].items():
            assert sha(ZH / rel) == digest, rel
        for fname, digest in info["data_sha256"].items():
            assert MANIFEST[fname]["sha256"] == digest


def test_splits_are_disjoint_by_task_id_schema_dataset_and_domain_group():
    ids = [t.id for t in ALL]
    assert len(ids) == len(set(ids)) and len(ALL) >= 200
    for key in ("schema_id", "dataset", "group"):
        seen: dict[str, str] = {}
        for split, tasks in BY_SPLIT.items():
            for v in {t.meta[key] for t in tasks}:
                assert seen.setdefault(v, split) == split, f"{key}={v} compare in {seen[v]} e in {split}"


def test_task_format_and_labels():
    for split, tasks in BY_SPLIT.items():
        for t in tasks:
            assert t.tools == ["run_sql"] and t.meta["split"] == split and t.id.startswith(t.meta["schema_id"] + "_")
            assert t.meta["language"] in {"de", "fr", "it", "en"} and t.meta["dataset"] in MANIFEST
            assert "{DATA}" in t.setup["sql_init"][0] and t.prompt.strip()
            assert [c["type"] for c in t.checks][:2] == ["sql_result_match", "sql_result_projection"]
            primary = [c for c in t.checks if not c.get("diagnostic")]
            assert [c["type"] for c in primary] == ["sql_result_match"], "il punteggio primario è solo l'execution accuracy rigida"
            assert all(c.get("diagnostic") for c in t.checks if c["type"] in ("sql_result_projection", "final_number"))


def test_languages_are_balanced_in_each_split():
    for split, info in SPLITS.items():
        counts = info["by_language"]
        assert set(counts) == {"de", "fr", "it", "en"} and max(counts.values()) - min(counts.values()) <= 3, (split, counts)


def test_all_gold_queries_run_on_the_real_data_and_pass_their_own_check():
    bad = []
    for t in ALL:
        box = make_box(t.setup, t.tools)
        try:
            spec = next(c for c in t.checks if c["type"] == "sql_result_match")
            r = box.execute(ToolCall("c1", "run_sql", {"query": spec["gold"]}, "native"), t.tools)
            ok = r.ok and CHECKS["sql_result_match"](spec, Ctx(Trajectory(), box))[0]
            res = box.last_result
            if not ok or not res.rows or all(all(v is None for v in row) for row in res.rows):
                bad.append(t.id)
        finally:
            box.close()
    assert not bad, bad


def test_a_wrong_answer_fails_on_real_data():
    t = next(t for t in BY_SPLIT["dev"] if t.id == "bevq_pop_1")
    spec = next(c for c in t.checks if c["type"] == "sql_result_match")
    box = make_box(t.setup, t.tools)
    try:
        assert box.execute(ToolCall("c1", "run_sql", {"query": "SELECT AnzBestWir + 1 FROM bevoelkerung_quartier LIMIT 1"}, "native"), t.tools).ok
        assert not CHECKS["sql_result_match"](spec, Ctx(Trajectory(), box))[0]
    finally:
        box.close()


def test_task_files_are_up_to_date_with_the_spec_and_the_data():
    """Rigenerare dalle specifiche e dai dati deve dare esattamente i task salvati (nessuna modifica a mano, nessuna deriva)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_zurich_tasks as gen
    built = gen.build({"dev": 3, "val": 3, "test": 3})
    for split, by_ds in built.items():
        for short, tasks in by_ds.items():
            on_disk = yaml.safe_load((ZH / split / f"{short}.yaml").read_text(encoding="utf-8"))
            assert on_disk == tasks, f"{split}/{short}.yaml non coincide con la rigenerazione"


def test_test_split_is_protected_unless_final_test_is_given(tmp_path):
    one = BY_SPLIT["test"][0].id
    with pytest.raises(SystemExit) as e:
        main(["run", "--base-url", "http://127.0.0.1:1/v1", "--model", "m", "--tasks", str(ZH / "test"), "--only", one, "--out", str(tmp_path / "a")])
    assert "FINALE" in str(e.value.code) and "--final-test" in str(e.value.code)
    assert not (tmp_path / "a").exists()
    # dev e val non sono protetti; con --final-test il test parte
    with MockServer(lambda m, t, b: final("x")) as srv:
        with pytest.raises(SystemExit) as e2:
            main(["run", "--base-url", srv.url, "--model", "m", "--tasks", str(ZH / "test"), "--only", one, "--final-test", "--out", str(tmp_path / "b")])
    assert (tmp_path / "b" / "results.jsonl").exists() and e2.value.code in (0, 1)


def test_dataset_has_traps_and_several_categories():
    traps = Counter(t.meta.get("trap", "none") for t in ALL)
    assert {"cross_lingual_schema", "text_numbers", "missing_value_marker", "multiple_bases", "trailing_whitespace", "time_type"} <= set(traps)
    assert len({t.category for t in ALL}) >= 6
