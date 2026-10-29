"""Tahap 2 / langkah 5 (Q4): bandingkan nilai hasil parsing dengan data rapi asli (ground truth), sel per sel."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C, fact_vs_truth  # noqa: E402

m = fact_vs_truth()
assert len(m) == 54000 and m.value.notna().sum() + m.value.isna().sum() == 54000
m["layout"] = m.layout.astype(int)
n = len(m)
ok_fix = m.quality.isin(["ok", "fixed"])
flag = m[m.quality == "flagged"]
summ = [("sel nilai pada kunci jawaban", n), ("sel yang ada di hasil parsing", int(m.quality.notna().sum())),
        ("sel sama persis dengan kunci jawaban", int(m.exact.sum())), ("persen sama persis", m.exact.mean()),
        ("sel berstatus ok atau fixed", int(ok_fix.sum())), ("sel ok atau fixed yang sama persis", int(m[ok_fix].exact.sum())),
        ("persen ok atau fixed yang sama persis", m[ok_fix].exact.mean()),
        ("sel berstatus fixed", int((m.quality == "fixed").sum())), ("sel fixed yang sama persis", int(m[m.quality == "fixed"].exact.sum())),
        ("sel berstatus flagged (nilai dipertahankan, mencurigakan)", len(flag)), ("sel flagged yang bernilai 10 kali kunci jawaban", int((flag.value == flag.truth * 10).sum())),
        ("sel berstatus missing (tidak ada nilai)", int((m.quality == "missing").sum())),
        ("sel bermasalah di log (flagged + missing)", int(m.quality.isin(["flagged", "missing"]).sum())),
        ("sel salah yang lolos tanpa tanda (ok atau fixed tetapi beda dari kunci)", int((ok_fix & ~m.exact).sum()))]
pd.DataFrame(summ, columns=["item", "value"]).to_csv(C.RES_ANALYSIS / "accuracy_summary.csv", index=False)

g = m.groupby("layout")
by = pd.DataFrame({"cells": g.size(), "exact": g.exact.sum(), "ok": g.quality.apply(lambda s: (s == "ok").sum()), "fixed": g.quality.apply(lambda s: (s == "fixed").sum()),
                   "flagged": g.quality.apply(lambda s: (s == "flagged").sum()), "missing": g.quality.apply(lambda s: (s == "missing").sum())}).reset_index()
by["exact_rate"] = by.exact / by.cells
by["unflagged_exact_rate"] = [m[(m.layout == l) & ok_fix].exact.mean() for l in by.layout]
by.to_csv(C.RES_ANALYSIS / "accuracy_by_layout.csv", index=False)

q = m.groupby("quality").agg(cells=("exact", "size"), exact=("exact", "sum")).reset_index()
q["exact_rate"] = q.exact / q.cells
q.to_csv(C.RES_ANALYSIS / "accuracy_by_quality.csv", index=False)
print(pd.DataFrame(summ).to_string(index=False)); print(by.to_string(index=False))
