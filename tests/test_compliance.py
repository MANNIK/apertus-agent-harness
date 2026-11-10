"""Controlli di conformità: devono scattare davvero quando una regola viene violata."""
import json
import shutil
from pathlib import Path

import pytest
import yaml

from agentbench.bench import run_suite
from agentbench.cli import main
from agentbench.client import ChatClient
from agentbench.compliance import check, render_findings, render_manifest, scan_network_imports
from agentbench.tasks import load_tasks
from mock_server import MockServer, final, scripted

ROOT = Path(__file__).resolve().parent.parent
TASK = [t for t in load_tasks(ROOT / "archive" / "agent-suite" / "tasks") if t.id == "sc_weather_it"]


def manifest(tmp_path, **override):
    m = yaml.safe_load((ROOT / "models.yaml").read_text(encoding="utf-8"))
    m.update(override)
    p = tmp_path / "models.yaml"
    p.write_text(yaml.safe_dump(m, allow_unicode=True), encoding="utf-8")
    return p


def make_run(tmp_path, model="/Users/x/models/apertus-v1.5-8b-mlx-bf16", name="run"):
    with MockServer(scripted({TASK[0].prompt: [final("12 °C")]})) as srv:
        run_suite(ChatClient(srv.url, model, retries=0, timeout=10), TASK, 1, tmp_path / name)
    return tmp_path / name


def levels(findings, level):
    return [f.message for f in findings if f.level == level]


def test_shipped_manifest_is_valid_and_run_with_declared_model_passes(tmp_path):
    run = make_run(tmp_path)
    f = check(ROOT / "models.yaml", [run])
    assert not levels(f, "ERROR"), levels(f, "ERROR")
    assert any("non dichiarata" in w for w in levels(f, "WARN"))  # architettura target ancora da scegliere


def test_undeclared_model_in_a_run_is_an_error(tmp_path):
    run = make_run(tmp_path, model="qualche/altro-modello")
    assert any("non dichiarato" in e for e in levels(check(ROOT / "models.yaml", [run]), "ERROR"))


def test_closed_model_declared_for_runtime_or_evaluation_is_an_error(tmp_path):
    m = yaml.safe_load((ROOT / "models.yaml").read_text(encoding="utf-8"))
    m["models"][1]["stages"] = ["development", "evaluation"]  # Claude come giudice: vietato
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(m), encoding="utf-8")
    assert any("modello chiuso" in e for e in levels(check(p, []), "ERROR"))


def test_missing_fields_and_bad_target_are_errors(tmp_path):
    m = yaml.safe_load((ROOT / "models.yaml").read_text(encoding="utf-8"))
    del m["models"][0]["license"]
    m["deployment"]["target"] = "cloud-qualsiasi"
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(m), encoding="utf-8")
    errs = levels(check(p, []), "ERROR")
    assert any("campi mancanti" in e and "license" in e for e in errs) and any("non valida" in e for e in errs)


def test_valid_target_is_recorded_as_ok(tmp_path):
    p = manifest(tmp_path, deployment={"target": "air-gapped"})
    f = check(p, [])
    assert not levels(f, "ERROR") and any("air-gapped" in x.message and x.level == "OK" for x in f)


def test_non_local_endpoint_is_flagged(tmp_path):
    run = make_run(tmp_path)
    meta = json.loads((run / "meta.json").read_text())
    meta["base_url"] = "https://api.example.com/v1"
    meta.pop("files_sha256")
    (run / "meta.json").write_text(json.dumps(meta))
    assert any("NON locale" in w for w in levels(check(ROOT / "models.yaml", [run]), "WARN"))


def _run_with_url(tmp_path, url, model="apertus-v1-5-8b", name="run"):
    run = make_run(tmp_path, model=model, name=name)
    meta = json.loads((run / "meta.json").read_text())
    meta["base_url"] = url
    meta.pop("files_sha256")
    (run / "meta.json").write_text(json.dumps(meta))
    return run


def test_allowed_endpoint_host_has_no_warning(tmp_path):
    run = _run_with_url(tmp_path, "https://gateway.keera.ch/api/v1")
    f = check(ROOT / "models.yaml", [run])
    assert not levels(f, "ERROR") and not any("NON locale" in w for w in levels(f, "WARN"))
    assert any("gateway.keera.ch" in x.message and x.level == "OK" for x in f)


def test_unknown_and_lookalike_hosts_are_flagged(tmp_path):
    for url in ("https://api.example.com/v1", "https://gateway.keera.ch.evil.example/api/v1",
                "https://evil-gateway.keera.ch/api/v1", "https://example.com/gateway.keera.ch"):
        run = _run_with_url(tmp_path, url, name="r" + str(abs(hash(url))))
        assert any("NON locale" in w for w in levels(check(ROOT / "models.yaml", [run]), "WARN")), url


def test_hosted_models_are_matched_exactly(tmp_path):
    for model in ("apertus-v1-5-8b", "apertus-v1-5-70b"):
        run = _run_with_url(tmp_path, "https://gateway.keera.ch/api/v1", model=model, name=model)
        assert not levels(check(ROOT / "models.yaml", [run]), "ERROR"), model
    # la variante -thinking non è dichiarata: non deve essere scambiata per apertus-v1-5-8b
    run = _run_with_url(tmp_path, "https://gateway.keera.ch/api/v1", model="apertus-v1-5-8b-thinking", name="think")
    assert any("non dichiarato" in e and "thinking" in e for e in levels(check(ROOT / "models.yaml", [run]), "ERROR"))


def test_tampered_results_are_detected(tmp_path):
    run = make_run(tmp_path)
    original = (run / "results.jsonl").read_text()
    tampered = original.replace('"task_id": "sc_weather_it"', '"task_id": "sc_weather_xx"')
    assert tampered != original  # la modifica deve esserci davvero
    (run / "results.jsonl").write_text(tampered)
    assert any("sha256" in e for e in levels(check(ROOT / "models.yaml", [run]), "ERROR"))


def test_judge_must_be_declared_open_weights(tmp_path):
    run = make_run(tmp_path)
    (run / "judge_meta.json").write_text(json.dumps({"model": "claude-sonnet-5-5"}))
    errs = levels(check(ROOT / "models.yaml", [run]), "ERROR")
    assert any("giudice" in e and "non è open-weights" in e for e in errs)
    (run / "judge_meta.json").write_text(json.dumps({"model": "sconosciuto-14b"}))
    assert any("giudice non dichiarato" in e for e in levels(check(ROOT / "models.yaml", [run]), "ERROR"))


def test_network_import_scan_flags_forbidden_modules(tmp_path):
    src = tmp_path / "src"
    shutil.copytree(ROOT / "src" / "agentbench", src, ignore=shutil.ignore_patterns("__pycache__"))
    assert not levels(scan_network_imports(src), "ERROR")  # il codice attuale è pulito
    (src / "tools.py").write_text("import requests\nimport socket\n" + (src / "tools.py").read_text())
    msg = " ".join(levels(scan_network_imports(src), "ERROR"))
    assert "tools.py" in msg and "requests" in msg and "socket" in msg
    (src / "client.py").write_text("import urllib3\n" + (src / "client.py").read_text())
    assert any("client.py" in e for e in levels(scan_network_imports(src), "ERROR"))


def test_manifest_lists_models_and_flags_undeclared_ones(tmp_path):
    ok = make_run(tmp_path, name="a")
    bad = make_run(tmp_path, model="altro/modello", name="b")
    md = render_manifest(ROOT / "models.yaml", [ok, bad])
    assert "Claude Sonnet 5.5" in md and "Apertus v1.5 8B" in md
    assert md.count("NON DICHIARATO") == 1 and "`altro/modello` (1 run) — NON DICHIARATO" in md


def test_cli_compliance_exit_code(tmp_path, capsys):
    run = make_run(tmp_path, model="altro/modello")
    with pytest.raises(SystemExit) as e:
        main(["compliance", str(run), "--models", str(ROOT / "models.yaml")])
    assert e.value.code == 1 and "✗" in capsys.readouterr().out
    run2 = make_run(tmp_path, name="ok")
    with pytest.raises(SystemExit) as e:
        main(["compliance", str(run2), "--models", str(ROOT / "models.yaml")])
    assert e.value.code == 0
