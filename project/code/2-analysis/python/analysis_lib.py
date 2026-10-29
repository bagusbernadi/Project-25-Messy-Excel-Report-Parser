"""Fungsi bersama tahap analisis Project 25: memuat tabel hasil parsing dan kunci jawaban dengan kunci yang sama."""
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "1-data-preparation" / "python"))
import common as C  # noqa: E402

KEY = ["date", "shift", "slot", "station", "size", "metric"]
LAYOUT_OF_FILE = lambda s: int(s.str.extract(r"_G(\d)_")[0].iloc[0]) if len(s) else 0  # noqa: E731


def load_fact():
    f = pd.read_csv(C.PARSED_DIR / "fact_output_tidy.csv")
    f["layout"] = f.source_file.str.extract(r"_G(\d)_")[0].astype(int)
    f["month"] = f.source_file.str.extract(r"_(\d{4}-\d{2})\.")[0]
    return f


def load_truth_long():
    t = pd.read_csv(C.TRUTH_CSV)
    t = t.melt(id_vars=["date", "shift", "slot", "station", "size"], value_vars=["qty_produced", "qty_reject"], var_name="metric", value_name="truth")
    t["metric"] = t.metric.map({"qty_produced": "produced", "qty_reject": "reject"})
    return t


def fact_vs_truth():
    m = load_fact().merge(load_truth_long(), on=KEY, how="outer", validate="one_to_one")
    m["exact"] = m.value == m.truth
    return m


def config_stats(path):
    """Jumlah baris config (tanpa komentar dan baris kosong) dan jumlah kunci pada file YAML."""
    lines = [ln for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")]

    def leaves(x):
        if isinstance(x, dict):
            return sum(leaves(v) for v in x.values())
        if isinstance(x, list):
            return sum(leaves(v) for v in x)
        return 1
    return len(lines), leaves(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def pct(x):
    return float(x)
