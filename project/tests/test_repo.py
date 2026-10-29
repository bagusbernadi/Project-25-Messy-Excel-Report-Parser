import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ignored(rel):
    return subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode == 0


def test_generated_data_is_ignored():
    for rel in ("project/data/sim/reports/x.xlsx", "project/data/parsed/fact_output_tidy.csv", "project/parsed.duckdb"):
        assert ignored(rel), rel


def test_samples_and_readme_are_not_ignored():
    assert not ignored("project/data/README.md")
    assert not ignored("project/data/samples/laporan_G1_2026-03.xlsx")


def test_root_index_redirects_to_design_and_report():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "design-and-report/" in html and "location.replace" in html
