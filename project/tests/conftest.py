import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

CODE = Path(__file__).resolve().parents[1] / "code"
for p in (CODE, CODE / "1-data-preparation" / "python", CODE / "2-analysis" / "python"):
    sys.path.insert(0, str(p))
import common as C  # noqa: E402
from parser import load_lookup, load_rules, load_templates, parse_files  # noqa: E402


@pytest.fixture(scope="session")
def sim():
    """Laporan simulasi; dibuat dulu bila belum ada (sekitar 1 menit)."""
    if len(list(C.REPORTS_DIR.glob("*.xlsx"))) != C.N_FILES:
        subprocess.run([sys.executable, str(CODE / "1-data-preparation" / "python" / "01_generate_reports.py")], check=True)
    return C.REPORTS_DIR


@pytest.fixture(scope="session")
def lookup():
    return load_lookup(C.LOOKUP)


@pytest.fixture(scope="session")
def rules():
    return load_rules(C.RULES)


@pytest.fixture(scope="session")
def templates():
    return load_templates(C.TEMPLATES_DIR)


@pytest.fixture(scope="session")
def parsed(sim, templates, lookup, rules):
    return parse_files(sorted(sim.glob("*.xlsx")), templates, lookup, rules)


@pytest.fixture(scope="session")
def truth(sim):
    t = pd.read_csv(C.TRUTH_CSV)
    t = t.melt(id_vars=["date", "shift", "slot", "station", "size"], value_vars=["qty_produced", "qty_reject"], var_name="metric", value_name="truth")
    t["metric"] = t.metric.map({"qty_produced": "produced", "qty_reject": "reject"})
    return t
