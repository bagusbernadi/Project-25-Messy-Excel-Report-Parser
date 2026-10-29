"""Tahap 1 / langkah 3: parse 36 laporan dengan config YAML menjadi fact_output_tidy, anomaly_log, dan reconciliation.

Hasil: data/parsed/fact_output_tidy.csv (tidak di-commit), results/1-data-preparation/{anomaly_log.csv, reconciliation.csv, file_summary.csv, fact_sample.csv}
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from parser import load_lookup, load_rules, load_templates, parse_files  # noqa: E402

files = sorted(C.REPORTS_DIR.glob("*.xlsx"))
assert len(files) == C.N_FILES, "jalankan 01_generate_reports.py dulu"
out = parse_files(files, load_templates(C.TEMPLATES_DIR), load_lookup(C.LOOKUP), load_rules(C.RULES))
fact, anom, rec, fl = out["fact"], out["anomaly"], out["reconciliation"], out["files"]
fact = fact.sort_values(["date", "shift", "slot", "station", "size", "metric"], kind="stable").reset_index(drop=True)
anom = anom.sort_values(["source_file", "sheet", "cell", "issue_type"], kind="stable").reset_index(drop=True)
rec = rec.sort_values(["source_file", "sheet", "block", "metric", "kind", "report_cell"], kind="stable").reset_index(drop=True)
fact.to_csv(C.PARSED_DIR / "fact_output_tidy.csv", index=False)
anom.to_csv(C.RES_PREP / "anomaly_log.csv", index=False)
rec.to_csv(C.RES_PREP / "reconciliation.csv", index=False)
fact.head(200).to_csv(C.RES_PREP / "fact_sample.csv", index=False)
q = fact.pivot_table(index="source_file", columns="quality", values="value", aggfunc="size", fill_value=0).reindex(columns=["ok", "fixed", "flagged", "missing"], fill_value=0)
a = anom.groupby("source_file").size().rename("anomaly_rows")
fs = fl.set_index("source_file").join(q).join(a).fillna(0).reset_index()
for c in ("ok", "fixed", "flagged", "missing", "anomaly_rows"):
    fs[c] = fs[c].astype(int)
fs.sort_values("source_file").to_csv(C.RES_PREP / "file_summary.csv", index=False)
print(f"fact {len(fact)} baris; anomaly {len(anom)}; reconciliation {len(rec)}")
print(fact.quality.value_counts().to_string())
