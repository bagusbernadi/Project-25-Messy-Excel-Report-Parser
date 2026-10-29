"""Tahap 2 / langkah 9 (Q8-Q10): empat metode untuk laporan yang sama, lalu benchmark (waktu proses, kecocokan, ukuran perubahan).

Waktu pembuatan dan perbaikan oleh manusia TIDAK diukur dengan stopwatch; yang dicatat adalah ukuran pekerjaan (jumlah rumus, baris, parameter) dan waktu proses mesin.
Hasil: results/2-analysis/{method_benchmark.csv, method_matrix.csv, method_situations.csv}, methods/excel_formula.xlsx
"""
import re
import statistics
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from methods_lib import C, FORMULA_COLS, match_truth, run_excel, run_python, run_sql, sql_text  # noqa: E402
from analysis_lib import config_stats  # noqa: E402

YEAR = 2026
L1 = sorted(p.name for p in C.REPORTS_DIR.glob("laporan_G1_*.xlsx"))
fv = lambda name: 7 if name >= "laporan_G1_2026-06" else 5     # kolom pertama nilai: berubah setelah revisi form (bulan ke-4)
med = lambda f, n=3: statistics.median(f() for _ in range(n))

n_formula = sum(1 for _, f in FORMULA_COLS.values() if f) + 2   # rumus unik di sheet Tidy + 2 rumus MATCH di Pemetaan
sql_lines = len([ln for ln in sql_text().split("-- name:")[0].splitlines() if ln.strip()])
pq_lines = len([ln for ln in (C.METHODS_DIR / "power_query" / "L1_v1.pq").read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("//")])
cfg_lines = config_stats(C.TEMPLATES_DIR / "L1_v1.yaml")[0]
engine_lines = sum(len([ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]) for p in (C.CODE / "1-data-preparation" / "python" / "parser").glob("*.py"))

rows = []


def add(method, scenario, n_files, build_size, build_unit, run_s, match, status, note="", before=None, fix_size=None, fix_unit=""):
    rows.append({"method": method, "scenario": scenario, "n_files": n_files, "build_size": build_size, "build_unit": build_unit, "run_seconds": run_s,
                 "result_match": match, "result_match_before_fix": before, "fix_size": fix_size, "fix_unit": fix_unit, "build_minutes": None, "fix_minutes": None,
                 "status": status, "note": note})


def ex(files):
    out, secs = [], 0.0
    for f in files:
        d, s = run_excel(C.REPORTS_DIR / f, fv(f), YEAR)
        out.append(d.assign(src=f))
        secs += s
    return pd.concat(out), secs


def sq(files, fvf=fv):
    out, secs = [], 0.0
    for f in files:
        d, s = run_sql(C.REPORTS_DIR / f, fvf(f), YEAR)
        out.append(d)
        secs += s
    return pd.concat(out), secs


# ---- S1: satu file layout 1
S1, f1 = "S1 satu file (layout 1, Mar)", [L1[0]]
_, keep_sec = run_excel(C.REPORTS_DIR / f1[0], 5, YEAR, keep=C.METHODS_DIR / "excel_formula.xlsx")
d, _ = ex(f1)
add("Rumus Excel", S1, 1, n_formula, "rumus unik + 6 parameter", med(lambda: run_excel(C.REPORTS_DIR / f1[0], 5, YEAR)[1]), match_truth(d, f1), "diukur", "waktu = hitung ulang di LibreOffice headless (bukan Excel)")
d, _ = sq(f1)
add("SQL (DuckDB)", S1, 1, sql_lines, "baris SQL", med(lambda: sq(f1)[1]), match_truth(d, f1), "diukur", "waktu mencakup memuat sel ke tabel; SQL tidak membaca .xlsx langsung")
d, _, _ = run_python([C.REPORTS_DIR / f1[0]])
add("Python (parser)", S1, 1, cfg_lines, f"baris config (+{engine_lines} baris mesin dipakai ulang)", med(lambda: run_python([C.REPORTS_DIR / f1[0]])[1]), match_truth(d, f1), "diukur",
    "hasil termasuk pemulihan lewat subtotal dan penandaan sel mencurigakan")
add("Power Query", S1, 1, pq_lines, "baris M", None, None, "tidak dijalankan", "kode ditulis (methods/power_query/L1_v1.pq) tetapi tidak ada Excel untuk menjalankannya")

# ---- S2: enam file layout 1
S2 = "S2 enam file layout 1 (Mar-Agu)"
d, sec = ex(L1)
add("Rumus Excel", S2, 6, n_formula, "rumus unik + 6 parameter", sec, match_truth(d, L1), "diukur", "satu workbook per file; parameter kolom pertama diubah untuk 3 file terakhir")
d, sec = sq(L1)
add("SQL (DuckDB)", S2, 6, sql_lines, "baris SQL", sec, match_truth(d, L1), "diukur", "query sama, parameter first_value_col berbeda untuk 3 file terakhir")
paths = [C.REPORTS_DIR / f for f in L1]
d, _, _ = run_python(paths)
add("Python (parser)", S2, 6, config_stats(C.TEMPLATES_DIR / "L1_v1.yaml")[0] + config_stats(C.TEMPLATES_DIR / "L1_v2.yaml")[0], "baris config (2 file config)", med(lambda: run_python(paths)[1]), match_truth(d, L1), "diukur",
    "template dipilih otomatis per file")
add("Power Query", S2, 6, pq_lines + len([ln for ln in (C.METHODS_DIR / "power_query" / "combine_folder.pq").read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("//")]), "baris M", None, None, "tidak dijalankan",
    "ada contoh penggabungan folder (combine_folder.pq)")

# ---- S3: 36 file semua layout
S3 = "S3 36 file, 6 layout"
allp = sorted(C.REPORTS_DIR.glob("*.xlsx"))
d, _, _ = run_python(allp)
add("Python (parser)", S3, 36, sum(config_stats(p)[0] for p in C.TEMPLATES_DIR.glob("*.yaml")), "baris config (8 file config)", med(lambda: run_python(allp)[1]), match_truth(d, [p.name for p in allp]), "diukur", "")
for m in ("Rumus Excel", "SQL (DuckDB)", "Power Query"):
    add(m, S3, 36, None, "", None, None, "tidak dikerjakan", "perlu definisi untuk 5 layout lain (dan satu per file untuk rumus Excel)")

# ---- S4: layout berubah (layout 1, bulan ke-4)
S4, f4 = "S4 layout 1 berubah (Jun)", ["laporan_G1_2026-06.xlsx"]
p4 = C.REPORTS_DIR / f4[0]
before, _ = run_excel(p4, 5, YEAR)
after, sec = run_excel(p4, 7, YEAR)
add("Rumus Excel", S4, 1, n_formula, "rumus unik + 6 parameter", sec, match_truth(after, f4), "diukur", "tanpa perubahan, sel Catatan/Paraf terbaca sebagai tanggal dan 2 tanggal terakhir hilang tanpa peringatan",
    before=match_truth(before, f4), fix_size=1, fix_unit="sel parameter")
b, _ = run_sql(p4, 5, YEAR)
a, sec = run_sql(p4, 7, YEAR)
add("SQL (DuckDB)", S4, 1, sql_lines, "baris SQL", sec, match_truth(a, f4), "diukur", "tanpa perubahan tetap benar: tanggal dibaca dari header tiap kolom dan kolom Catatan/Paraf tidak punya nilai", before=match_truth(b, f4), fix_size=0, fix_unit="tidak perlu perubahan")
d, _, err = run_python([p4])
old_t = [t for t in __import__("parser").load_templates(C.TEMPLATES_DIR) if t["id"] != "L1_v2"]
try:
    __import__("parser").parse_files([p4], old_t, __import__("parser").load_lookup(C.LOOKUP), __import__("parser").load_rules(C.RULES))
    pre = "diparse"
except Exception as e:                                      # noqa: BLE001
    pre = type(e).__name__
add("Python (parser)", S4, 1, cfg_lines, "baris config", med(lambda: run_python([p4])[1]), match_truth(d, f4), "diukur", f"dengan config lama: berhenti ({pre}), tidak menulis angka salah",
    before=0.0, fix_size=2, fix_unit="baris config (file baru L1_v2.yaml)")
add("Power Query", S4, 1, pq_lines, "baris M", None, None, "tidak dijalankan", "perubahan: nilai Param_FirstValueCol", fix_size=1, fix_unit="nilai parameter")

bench = pd.DataFrame(rows)
bench.to_csv(C.RES_ANALYSIS / "method_benchmark.csv", index=False)

n_sub = len(pd.read_csv(C.RES_PREP / "reconciliation.csv"))
n_rec = int((pd.read_csv(C.RES_PREP / "anomaly_log.csv").fix_method == "subtotal").sum())
fmt_id = lambda n: f"{n:,}".replace(",", ".")
mat = [
    ("Waktu proses satu file (detik)", "diukur", *[bench[(bench.method == m) & (bench.scenario == S1)].run_seconds.iloc[0] for m in ("Rumus Excel", "SQL (DuckDB)", "Python (parser)", "Power Query")]),
    ("Kecocokan dengan kunci jawaban, satu file (persen)", "diukur", *[bench[(bench.method == m) & (bench.scenario == S1)].result_match.iloc[0] for m in ("Rumus Excel", "SQL (DuckDB)", "Python (parser)", "Power Query")]),
    ("Perubahan untuk layout bulan ke-4", "diukur", "1 sel parameter", "tidak perlu (query tetap benar)", "2 baris config (file baru)", "1 nilai parameter (tidak diuji)"),
    ("Hasil bila layout berubah dan tidak ada yang diubah (persen sel benar)", "diukur", *[(f"{bench[(bench.method == m) & (bench.scenario == S4)].result_match_before_fix.iloc[0]:.1%}" if m != "Power Query" else "tidak diuji") for m in ("Rumus Excel", "SQL (DuckDB)", "Python (parser)", "Power Query")]),
    ("Perilaku bila layout berubah tanpa perubahan", "diukur", "hasil tetap keluar, 2 tanggal terakhir hilang tanpa peringatan", "hasil tetap benar pada kasus ini", "berhenti dengan pesan template tidak dikenal; tidak ada angka ditulis", "tidak diuji"),
    ("Rekonsiliasi dengan subtotal laporan", "diukur", "tidak ada", "tidak ada", f"ada ({fmt_id(n_sub)} subtotal)", "tidak ada"),
    ("Pemulihan sel kotor lewat subtotal", "diukur", "tidak ada", "tidak ada", f"ada ({fmt_id(n_rec)} sel)", "tidak ada"),
    ("Jejak sel asal sampai alamat sel", "penilaian", "ada (baris dan kolom sumber)", "ada (nomor baris dan kolom)", "ada (sheet dan sel)", "ada (kolom Row)"),
    ("Banyak file sekaligus", "penilaian", "satu workbook per file", "perlu loop di luar SQL", "ya (pilih template otomatis)", "ya (folder), template dipilih manual"),
    ("Keahlian yang dibutuhkan", "penilaian", "Excel (INDEX, MATCH)", "SQL dan sedikit Python untuk memuat sel", "Python dan YAML", "Excel dan bahasa M (menu)"),
]
pd.DataFrame(mat, columns=["criterion", "basis", "excel_formula", "sql", "python_parser", "power_query"]).to_csv(C.RES_ANALYSIS / "method_matrix.csv", index=False)
sit = [("End user di lini produksi, satu atau dua file, tanpa programmer", "Rumus Excel", "Tanpa instalasi; perubahan layout cukup mengubah satu sel parameter; waktu proses sekitar satu detik per file", "diukur"),
       ("Tim non-programmer yang rutin mengolah banyak file satu layout", "Power Query", "Refresh dari folder tanpa menulis kode; perubahan layout lewat parameter. Belum diuji karena Excel tidak tersedia", "penilaian (belum dijalankan)"),
       ("Banyak file dengan banyak layout dan perlu bukti kebenaran", "Python (parser)", "Pilih template otomatis, rekonsiliasi dengan subtotal, pemulihan dan penandaan sel; berhenti bila layout tak dikenal", "diukur"),
       ("Data sudah berupa tabel di database", "SQL (DuckDB)", "Sekali tabel sel termuat, query bisa diulang dan diaudit; tidak membaca .xlsx langsung", "diukur")]
pd.DataFrame(sit, columns=["situation", "recommended_method", "reason", "basis"]).to_csv(C.RES_ANALYSIS / "method_situations.csv", index=False)
pd.set_option("display.width", 250)
print(bench.drop(columns=["build_minutes", "fix_minutes", "note"]).to_string(index=False))
