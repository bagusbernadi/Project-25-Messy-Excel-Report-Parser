"""Tahap 3 / langkah 15: one-sheet perbandingan metode (PDF dan PNG), angka dibaca dari CSV hasil."""
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

BLUE, ORANGE, GREY, INK, SOFT = "#1A73E8", "#E8710A", "#9AA0A6", "#202124", "#E8F0FE"
b = pd.read_csv(C.RES_ANALYSIS / "method_benchmark.csv")
sit = pd.read_csv(C.RES_ANALYSIS / "method_situations.csv")
imp = pd.read_csv(C.RES_ANALYSIS / "impact_time.csv").set_index("item").value
acc = pd.read_csv(C.RES_ANALYSIS / "accuracy_summary.csv").set_index("item").value
idn = lambda x, d=0: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
s1 = b[b.scenario.str.startswith("S1")].set_index("method")

fig = plt.figure(figsize=(11.69, 8.27))
fig.patch.set_facecolor("white")
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.add_patch(plt.Rectangle((0, 90), 100, 10, color=BLUE))
ax.text(4, 95.2, "Laporan Excel berantakan: metode mana yang dipakai?", color="white", fontsize=21, fontweight="bold", va="center")
ax.text(4, 91.7, "Project 25 · Messy Excel Report Parser · data simulasi (36 laporan, 6 layout)", color="white", fontsize=10.5, va="center")

y = 85
ax.text(4, y, "Pilih menurut situasi", fontsize=13.5, fontweight="bold", color=INK)
y -= 3.2
for r in sit.itertuples():
    ax.add_patch(plt.Rectangle((4, y - 6.4), 92, 6.4, color=SOFT))
    ax.text(5.5, y - 3.2, "\n".join(textwrap.wrap(r.situation, 38)), fontsize=9.6, va="center", color=INK)
    ax.text(43, y - 3.2, r.recommended_method, fontsize=12.5, fontweight="bold", va="center", color=BLUE)
    ax.text(60, y - 3.2, "\n".join(textwrap.wrap(r.reason, 52)), fontsize=8.7, va="center", color=INK)
    y -= 7.4

y -= 1.5
ax.text(4, y, "Angka yang terukur (satu file layout 1; kunci jawaban diketahui)", fontsize=13.5, fontweight="bold", color=INK)
y -= 3
cols = [("Rumus Excel", 6), ("SQL (DuckDB)", 29), ("Python (parser)", 52), ("Power Query", 75)]
for m, x0 in cols:
    r = s1.loc[m]
    ax.add_patch(plt.Rectangle((x0 - 1.5, y - 17), 21, 17, fill=False, edgecolor=GREY, lw=1))
    ax.text(x0, y - 2.2, m, fontsize=11.5, fontweight="bold", color=BLUE if r.status == "diukur" else GREY)
    if r.status == "diukur":
        ax.text(x0, y - 6.8, f"{idn(r.run_seconds, 2)} detik", fontsize=15, fontweight="bold", color=INK)
        ax.text(x0, y - 9.4, "waktu proses 1 file", fontsize=8, color=GREY)
        ax.text(x0, y - 13, f"{idn(r.result_match * 100, 1)}%", fontsize=15, fontweight="bold", color=INK)
        ax.text(x0, y - 15.4, "sel sama dengan kunci jawaban", fontsize=8, color=GREY)
    else:
        ax.text(x0, y - 8, "ditulis, belum dijalankan", fontsize=9.5, color=ORANGE)
        ax.text(x0, y - 11, "(tidak ada Excel di lingkungan\npengerjaan)", fontsize=8, color=GREY, va="top")
y -= 21
ax.text(4, y, "Hanya parser Python yang membandingkan hasil dengan subtotal laporan: ", fontsize=10, color=INK)
ax.text(4, y - 3, f"{idn(acc['sel ok atau fixed yang sama persis'])} dari {idn(acc['sel berstatus ok atau fixed'])} sel tepercaya sama persis dengan kunci jawaban; "
        f"{idn(acc['sel bermasalah di log (flagged + missing)'])} sel yang meragukan ditandai, tidak ditebak.", fontsize=10, color=INK)
y -= 8
ax.add_patch(plt.Rectangle((4, 4), 92, y - 4, color="#FFF4E5"))
ax.text(6, y - 3.5, f"Estimasi hemat ±{idn(imp['Jam dihemat per tahun'])} jam kerja per tahun", fontsize=13.5, fontweight="bold", color=ORANGE)
ax.text(6, y - 7.2, f"= {idn(imp['Laporan per bulan'])} laporan per bulan × {idn(imp['Menit copy-paste dan pengecekan per laporan'])} menit copy-paste × 12 ÷ 60.   "
        "Label: estimated, simulated (asumsi, bukan hasil stopwatch).", fontsize=9, color=INK)
ax.text(6, 6.2, "Batasan: data simulasi lebih rapi dari laporan nyata. Waktu pembuatan oleh manusia tidak diukur. Power Query belum dijalankan.", fontsize=8.3, color=GREY)
fig.savefig(C.RES_PRESENT / "method_onesheet.pdf")
fig.savefig(C.RES_PRESENT / "method_onesheet.png", dpi=130)
print("one-sheet ditulis")
