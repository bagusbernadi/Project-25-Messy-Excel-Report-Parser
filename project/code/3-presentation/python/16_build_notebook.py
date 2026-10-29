"""Tahap 3 / langkah 16: buat dan jalankan notebook analisis Q1-Q15 (results/3-presentation/analysis.ipynb) dari CSV hasil."""
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

M, K = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
    M("# Project 25: Messy Excel Report Parser\n\nAnalisis Q1-Q15. Semua tabel dibaca dari `results/` (hasil skrip Python dan SQL). Data adalah simulasi: 36 laporan Excel buatan dengan kunci jawaban."),
    K("""from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
ROOT = Path.cwd()
while not (ROOT / 'results').exists():
    ROOT = ROOT.parent
R = lambda f: pd.read_csv(next((ROOT / 'results' / d / f) for d in ('1-data-preparation', '2-analysis', '3-presentation') if (ROOT / 'results' / d / f).exists()))
pd.options.display.float_format = '{:.6g}'.format
pd.options.display.max_colwidth = 70
plt.rcParams.update({'figure.figsize': (9, 3.4), 'axes.spines.top': False, 'axes.spines.right': False})
BLUE, GREY, ORANGE = '#1A73E8', '#9AA0A6', '#E8710A'"""),
    M("## Q1. Masalah layout dan jumlah file yang terkena"),
    K("R('layout_taxonomy.csv')"),
    M("## Q2. Template mana yang paling sulit"),
    K("R('template_difficulty.csv')"),
    M("## Q3. Rekonsiliasi: subtotal laporan vs jumlah hasil parsing"),
    K("display(R('reconciliation_summary.csv')); R('reconciliation_typos.csv')"),
    M("## Q4. Kecocokan dengan data rapi asli"),
    K("display(R('accuracy_summary.csv')); R('accuracy_by_layout.csv')"),
    M("## Q5. Pareto anomali per jenis dan layout"),
    K("t = R('anomaly_by_type.csv'); display(t)\nfig, ax = plt.subplots(); ax.bar(t.issue_type, t.n, color=BLUE); plt.xticks(rotation=30); plt.show()\nR('anomaly_by_layout.csv')"),
    M("## Q6-Q7. Perubahan layout: apa yang terjadi dan berapa baris config yang diubah"),
    K("display(R('robustness_scenarios.csv')[['id','scenario','old_config','new_config','config_lines_changed','lookup_lines_changed','python_lines_changed']]); R('config_changes.csv')"),
    M("## Q8-Q10. Empat metode (waktu proses adalah waktu mesin; waktu pembuatan manusia tidak diukur)"),
    K("display(R('method_benchmark.csv').drop(columns=['build_minutes','fix_minutes','note'])); display(R('method_matrix.csv')); R('method_situations.csv')"),
    M("## Q11. Pivot dari tabel tidy vs kunci jawaban dan total laporan"),
    K("p = R('pivot_vs_truth.csv'); display(p[['station','block_month','produced_diff_pct','reject_rate_diff_pp','missing_cells','flagged_cells']].head(12)); R('pivot_vs_report_totals.csv')"),
    M("## Q12. Pola setelah enam laporan bulanan digabung"),
    K("display(R('station_reject_rate.csv')); display(R('trend_slopes.csv')); R('rate_by_size_shift.csv')"),
    K("r = R('station_reject_rate.csv'); plt.bar(r.station, r.reject_rate * 100, color=BLUE); plt.xticks(rotation=40, ha='right'); plt.ylabel('reject rate (%)'); plt.show()"),
    M("## Q13-Q14. Dampak waktu (asumsi, estimated) dan sel salah yang tertangkap"),
    K("display(R('impact_time.csv')); display(R('impact_scenarios.csv').pivot(index='reports_per_month', columns='minutes_per_report', values='hours_saved_per_year')); R('errors_caught.csv')"),
    M("## Q15. Kejadian yang ditanam: terdeteksi?"),
    K("display(R('validation_planted.csv')); R('validation_checks.csv')"),
    M("## Cek silang SQL vs pandas"),
    K("x = R('crosscheck_sql.csv'); print(f\"{int(x.match.sum())} dari {len(x)} pemeriksaan cocok\"); x"),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
out = C.RES_PRESENT / "analysis.ipynb"
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(C.ROOT)}}).execute()
nbf.write(nb, out)
errs = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.output_type == "error"]
print("notebook", out.name, len(nb.cells), "sel;", len(errs), "error")
assert not errs
