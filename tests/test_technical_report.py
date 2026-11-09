"""La tabella dei modelli nel rapporto tecnico deve essere quella generata dal comando, non scritta a mano."""
from pathlib import Path

from agentbench.compliance import render_manifest

ROOT = Path(__file__).resolve().parent.parent


def test_models_table_in_report_matches_manifest_command():
    text = (ROOT / "docs" / "technical_report.md").read_text(encoding="utf-8")
    block = text.split("<!-- MODELS:BEGIN -->\n", 1)[1].split("<!-- MODELS:END -->", 1)[0]
    assert block == render_manifest(ROOT / "models.yaml", [], "en")


def test_report_has_required_sections_and_no_invented_numbers():
    text = (ROOT / "docs" / "technical_report.md").read_text(encoding="utf-8")
    for h in ("## 1. Core task", "## 2. Models used", "## 3. Deployment architecture", "## 4. Reproducibility",
              "## 5. Method", "## 6. Results", "## 7. Limitations"):
        assert h in text
    results = text.split("## 6. Results", 1)[1].split("## 7.", 1)[0]
    rows = [r for r in results.splitlines() if r.startswith("| ") and not r.startswith("| Item") and not r.startswith("|---")]
    assert rows and all("TBD (run:" in r for r in rows)
