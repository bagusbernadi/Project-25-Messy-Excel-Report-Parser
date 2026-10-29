"""Tahap 2 / langkah 11 (Q13, Q14): jam copy-paste yang dihemat per tahun (estimated) dan sel salah yang tertangkap.

Menit copy-paste per laporan dan jumlah laporan per bulan adalah ASUMSI (tidak diukur dengan stopwatch). Waktu proses parser diukur di mesin ini.
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C  # noqa: E402
from methods_lib import run_python  # noqa: E402

paths = sorted(C.REPORTS_DIR.glob("*.xlsx"))
secs = sorted(run_python(paths)[1] for _ in range(3))[1]
per_month = secs / 6                                        # 36 file = 6 bulan
manual_h = C.REPORTS_PER_MONTH * C.COPYPASTE_MIN_PER_REPORT * C.MONTHS_PER_YEAR / 60
auto_h = per_month * C.MONTHS_PER_YEAR / 3600
t = [("Laporan per bulan", C.REPORTS_PER_MONTH, "laporan", "asumsi"), ("Menit copy-paste dan pengecekan per laporan", C.COPYPASTE_MIN_PER_REPORT, "menit", "asumsi"),
     ("Jam copy-paste per tahun", manual_h, "jam", "estimated, simulated"), ("Waktu parser untuk 36 file", secs, "detik", "diukur"),
     ("Waktu parser untuk laporan satu bulan (6 file)", per_month, "detik", "diukur"), ("Jam parser per tahun", auto_h, "jam", "diukur"),
     ("Jam dihemat per tahun", manual_h - auto_h, "jam", "estimated, simulated")]
pd.DataFrame(t, columns=["item", "value", "unit", "basis"]).to_csv(C.RES_ANALYSIS / "impact_time.csv", index=False)
sc = [{"reports_per_month": r, "minutes_per_report": m, "hours_saved_per_year": r * m * 12 / 60} for r in (3, 6, 12, 24) for m in (15, 30, 60)]
pd.DataFrame(sc).to_csv(C.RES_ANALYSIS / "impact_scenarios.csv", index=False)

# Q14: kesalahan yang sengaja ditanam di laporan dan siapa yang menangkapnya
d = pd.read_csv(C.DIRTY_CSV)
a = pd.read_csv(C.RES_PREP / "anomaly_log.csv")
rows = []
import openpyxl  # noqa: E402
wbs = {}
for r in d.itertuples():
    if r.problem in ("duplicate_sheet", "subtotal_typo"):
        eff = True
    else:
        wb = wbs.setdefault(r.file, openpyxl.load_workbook(C.REPORTS_DIR / r.file))
        cur = wb[r.sheet][r.cell].value
        eff = str(cur).strip() != str(int(r.original)) if cur is not None else True
        eff = eff and not (r.problem == "x10" and r.original == 0)
    rows.append({"file": r.file, "sheet": r.sheet, "cell": r.cell, "problem": r.problem, "effective": eff, "layout": int(r.file.split("_G")[1][0])})
x = pd.DataFrame(rows)
caught = a.assign(key=a.source_file + "|" + a.sheet + "|" + a.cell.fillna(""))
x["key"] = x.file + "|" + x.sheet + "|" + x.cell.fillna("")
x["caught"] = x.key.isin(set(caught.key))
x["has_subtotal"] = x.layout.isin([1, 2])
wrong = x[x.effective & x.problem.isin(["text_na", "dash", "x10", "subtotal_typo"])]
rows = [("Sel angka salah atau hilang di laporan (tanpa unit_text dan duplikat)", len(wrong)),
        ("  di file yang punya subtotal (layout 1 dan 2)", int(wrong.has_subtotal.sum())),
        ("  di file tanpa subtotal (layout 3, 4, 6)", int((~wrong.has_subtotal).sum())),
        ("Sel salah yang tercatat di log anomali", int(wrong.caught.sum())),
        ("Sel salah yang lolos tanpa tercatat", int((~wrong.caught).sum())),
        ("Sel berformat teks (unit_text) yang dibersihkan", int(((x.problem == "unit_text") & x.effective).sum())),
        ("Sel salah yang nilainya dipulihkan tepat lewat subtotal", int((a.fix_method == "subtotal").sum())),
        ("Pembanding rekap copy-paste manual (tidak diukur)", None)]
pd.DataFrame(rows, columns=["item", "value"]).to_csv(C.RES_ANALYSIS / "errors_caught.csv", index=False)
x.drop(columns="key").to_csv(C.RES_ANALYSIS / "planted_cells_effective.csv", index=False)
print(pd.DataFrame(t).to_string(index=False)); print(pd.DataFrame(rows).to_string(index=False)); print(x.groupby("problem").agg(n=("effective", "size"), effective=("effective", "sum"), caught=("caught", "sum")))
