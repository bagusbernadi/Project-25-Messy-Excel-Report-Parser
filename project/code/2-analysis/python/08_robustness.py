"""Tahap 2 / langkah 8 (Q6, Q7): uji skenario perubahan layout; berapa baris config yang diubah."""
import difflib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C, config_stats  # noqa: E402
from scenarios import run_all  # noqa: E402

df = run_all()
df.to_csv(C.RES_ANALYSIS / "robustness_scenarios.csv", index=False)

rows = []
for lay, a, b in ((1, "L1_v1", "L1_v2"), (3, "L3_v1", "L3_v2")):
    ta = (C.TEMPLATES_DIR / f"{a}.yaml").read_text(encoding="utf-8").splitlines()
    tb = (C.TEMPLATES_DIR / f"{b}.yaml").read_text(encoding="utf-8").splitlines()
    ch = [ln for ln in difflib.unified_diff(ta, tb, lineterm="", n=0) if ln.startswith("+") and not ln.startswith("+++")]
    subst = [ln for ln in ch if not ln[1:].startswith(("id:", "description:"))]
    rows.append({"layout": lay, "from_config": a, "to_config": b, "lines_in_new_file": config_stats(C.TEMPLATES_DIR / f"{b}.yaml")[0], "lines_changed": len(ch), "lines_changed_excluding_id_description": len(subst),
                 "python_lines_changed": 0})
new_t = []
for p in sorted(C.TEMPLATES_DIR.glob("*_v1.yaml")):
    new_t.append(config_stats(p)[0])
rows.append({"layout": 0, "from_config": "(tidak ada)", "to_config": "template baru dari nol (rata-rata 6 template v1)", "lines_in_new_file": round(sum(new_t) / len(new_t)), "lines_changed": round(sum(new_t) / len(new_t)),
             "lines_changed_excluding_id_description": round(sum(new_t) / len(new_t)) - 2, "python_lines_changed": 0})
pd.DataFrame(rows).to_csv(C.RES_ANALYSIS / "config_changes.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print(df[["id", "scenario", "old_config", "new_config", "config_lines_changed", "lookup_lines_changed"]].to_string(index=False)); print(pd.DataFrame(rows).to_string(index=False))
