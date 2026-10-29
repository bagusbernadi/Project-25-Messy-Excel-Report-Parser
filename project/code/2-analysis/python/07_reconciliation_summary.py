"""Tahap 2 / langkah 7 (Q3): ringkasan rekonsiliasi subtotal laporan vs total hasil parsing."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C  # noqa: E402

r = pd.read_csv(C.RES_PREP / "reconciliation.csv")
r["layout"] = r.source_file.str.extract(r"_G(\d)_")[0].astype(int)
rows = []
for (lay, kind), g in r.groupby(["layout", "kind"]):
    rows.append({"layout": lay, "kind": kind, "subtotals": len(g), "match_raw": int((g.status == "cocok").sum()), "match_final": int((g.status_final == "cocok").sum()),
                 "recovered_this": int((g.resolution == "dipulihkan dari subtotal ini").sum()), "recovered_other": int((g.resolution == "dipulihkan lewat subtotal lain").sum()),
                 "open_bad_cells": int((g.resolution == "selisih: sel bermasalah belum bisa dipastikan").sum()), "suspect_subtotal": int((g.resolution == "selisih: subtotal dicurigai").sum())})
s = pd.DataFrame(rows)
s["match_rate_raw"] = s.match_raw / s.subtotals
s["match_rate_final"] = s.match_final / s.subtotals
s.to_csv(C.RES_ANALYSIS / "reconciliation_summary.csv", index=False)
typos = r[r.resolution == "selisih: subtotal dicurigai"][["source_file", "sheet", "report_cell", "report_total", "parsed_total_final", "diff_final", "block"]]
typos.to_csv(C.RES_ANALYSIS / "reconciliation_typos.csv", index=False)
print(s.to_string(index=False)); print(typos.to_string(index=False))
