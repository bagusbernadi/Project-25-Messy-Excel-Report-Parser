"""Tahap 3 / langkah 14: siapkan CSV ringkas untuk dashboard (dash_*.csv). Dashboard tidak membaca laporan Excel atau database."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "2-analysis" / "python"))
import common as C  # noqa: E402
from analysis_lib import load_fact  # noqa: E402

f = load_fact()
f["block_month"] = f.month
f["flagged"] = f.quality.isin(["flagged", "missing"]).astype(int)
g = f.groupby(["date", "shift", "station", "size", "block_month", "metric"]).agg(value=("value", "sum"), open_issues=("flagged", "sum")).reset_index()
p = g.pivot_table(index=["date", "shift", "station", "size", "block_month"], columns="metric", values="value", aggfunc="sum").reset_index()
iss = g.groupby(["date", "shift", "station", "size", "block_month"]).open_issues.sum().reset_index()
p = p.merge(iss, on=["date", "shift", "station", "size", "block_month"])
p["ok_qty"] = p["produced"] - p["reject"]
p.rename(columns={"open_issues": "open_cells"}).to_csv(C.RES_PRESENT / "dash_pivot.csv", index=False)
fs = pd.read_csv(C.RES_PREP / "file_summary.csv")
fs.to_csv(C.RES_PRESENT / "dash_files.csv", index=False)
pd.read_csv(C.RES_ANALYSIS / "reconciliation_summary.csv").to_csv(C.RES_PRESENT / "dash_recon_summary.csv", index=False)
r = pd.read_csv(C.RES_PREP / "reconciliation.csv")
r[r.status != "cocok"].to_csv(C.RES_PRESENT / "dash_recon_open.csv", index=False)
pd.read_csv(C.RES_PREP / "anomaly_log.csv").to_csv(C.RES_PRESENT / "dash_anomaly.csv", index=False)
pd.read_csv(C.RES_ANALYSIS / "anomaly_by_type.csv").to_csv(C.RES_PRESENT / "dash_anomaly_type.csv", index=False)
pd.read_csv(C.RES_ANALYSIS / "method_benchmark.csv").to_csv(C.RES_PRESENT / "dash_benchmark.csv", index=False)
pd.read_csv(C.RES_ANALYSIS / "method_situations.csv").to_csv(C.RES_PRESENT / "dash_situations.csv", index=False)
pd.read_csv(C.RES_ANALYSIS / "method_matrix.csv").to_csv(C.RES_PRESENT / "dash_matrix.csv", index=False)
pd.read_csv(C.RES_ANALYSIS / "impact_scenarios.csv").to_csv(C.RES_PRESENT / "dash_impact.csv", index=False)
print("dash_*.csv:", len(list(C.RES_PRESENT.glob("dash_*.csv"))), "| dash_pivot", len(p), "baris")
