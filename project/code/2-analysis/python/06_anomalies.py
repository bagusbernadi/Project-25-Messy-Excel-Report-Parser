"""Tahap 2 / langkah 6 (Q2, Q5): Pareto anomali per jenis dan layout; kesulitan tiap template."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C, config_stats, load_fact  # noqa: E402

a = pd.read_csv(C.RES_PREP / "anomaly_log.csv")
a["layout"] = a.source_file.str.extract(r"_G(\d)_")[0].astype(int)
a["issue_type"] = a.issue_type.fillna("")
t = a.groupby("issue_type").agg(n=("cell", "size"), fixed=("action", lambda s: int((s == "fixed").sum())), flagged=("action", lambda s: int((s == "flagged").sum())),
                                dropped=("action", lambda s: int((s == "dropped").sum()))).reset_index().sort_values(["n", "issue_type"], ascending=[False, True], kind="stable")
t["share"] = t.n / t.n.sum()
t["cum_share"] = t.share.cumsum()
t.to_csv(C.RES_ANALYSIS / "anomaly_by_type.csv", index=False)
pv = a.pivot_table(index="issue_type", columns="layout", values="cell", aggfunc="size", fill_value=0).reindex(t.issue_type)
pv.columns = [f"layout{c}" for c in pv.columns]
pv.reset_index().to_csv(C.RES_ANALYSIS / "anomaly_by_layout.csv", index=False)

f = load_fact()
rows = []
for lay in range(1, 7):
    cfgs = sorted(C.TEMPLATES_DIR.glob(f"L{lay}_v*.yaml"))
    st = [config_stats(p) for p in cfgs]
    sub = f[f.layout == lay]
    al = a[a.layout == lay]
    unresolved = int(sub.quality.isin(["flagged", "missing"]).sum())
    rows.append({"layout": lay, "reader": __import__("yaml").safe_load(cfgs[0].read_text(encoding="utf-8"))["reader"], "config_files": len(cfgs),
                 "config_lines": st[0][0], "config_keys": st[0][1], "cells": len(sub), "anomaly_rows": len(al), "anomaly_per_1000_cells": len(al) / len(sub) * 1000,
                 "unresolved_cells": unresolved, "unresolved_per_1000_cells": unresolved / len(sub) * 1000})
d = pd.DataFrame(rows)
d.to_csv(C.RES_ANALYSIS / "template_difficulty.csv", index=False)
print(t.to_string(index=False)); print(d.to_string(index=False))
