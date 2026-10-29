"""Membuat design-and-report/index.html (Report Project versi 2) dari page_v1.html dan CSV hasil.

- Pane Design diambil apa adanya dari page_v1.html (dicek identik).
- Semua angka di Report berasal dari project/results/*.csv lewat helper I/D/P (report_lib.py) dan diaudit di akhir.
Jalankan dari folder mana saja:  python design-and-report/src/build_report.py
"""
import re
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "project" / "code"))
sys.path.insert(0, HERE.as_posix())
from common import DB_PATH, RES_ANALYSIS, RES_PREP, RES_PRESENT, result  # noqa: E402
from report_lib import (BLUE, D, cs, GREY, HI, I, NO, OK, P, PART, SOFT, audit, bars, esc, gbars, hbars,  # noqa: E402
                        legend, pareto_svg, pill, qa, table)
from report_lib import REG  # noqa: E402

R = lambda n: pd.read_csv(result(n))
PRIO = {1: "Utama", 2: "Pendukung", 3: "Utama", 4: "Utama", 5: "Utama", 6: "Utama", 7: "Pendukung", 8: "Utama", 9: "Utama", 10: "Pendukung",
        11: "Utama", 12: "Pendukung", 13: "Utama", 14: "Tambahan", 15: "Utama"}
QT = {1: "Masalah layout apa saja yang ada di laporan, dan seberapa sering tiap masalah muncul?",
      2: "Template mana yang paling sulit dibaca otomatis, dan kenapa?",
      3: "Apakah total hasil parsing sama dengan subtotal di laporan untuk setiap blok data?",
      4: "Berapa persen nilai hasil parsing yang sama persis dengan data asli sebelum laporan dibuat berantakan?",
      5: "Jenis anomali sel apa yang paling sering muncul (angka bertipe teks, desimal koma, sel kosong), dan di template mana?",
      6: "Apakah parser tetap benar saat layout berubah, misalnya kolom baru, blok bergeser, atau sheet bulan baru?",
      7: "Berapa banyak perubahan config yang dibutuhkan untuk menambah satu template baru, tanpa mengubah kode Python?",
      8: "Dari rumus Excel, Power Query, Python, dan SQL, mana yang paling cepat dibuat, paling tahan perubahan layout, dan paling mudah dirawat?",
      9: "Metode mana yang paling cocok untuk end user, untuk tim non-programmer, dan untuk banyak file sekaligus?",
      10: "Berapa lama waktu proses tiap metode untuk 1 file dibanding 36 file?",
      11: "Apakah pivot dari tabel tidy (output dan yield per stasiun per bulan) sama dengan angka di laporan asli?",
      12: "Pola apa yang baru terlihat setelah data 6 bulan digabung, misalnya tren yield per stasiun dan model?",
      13: "Berapa jam copy-paste yang bisa dihemat per tahun?",
      14: "Berapa banyak salah salin yang tertangkap rekonsiliasi dibanding rekap copy-paste biasa?",
      15: "Apakah semua kejadian yang sengaja ditanam (anomali, subtotal salah, perubahan layout, sheet ganda) terdeteksi?"}
SEC = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 5, 11: 6, 12: 6, 13: 7, 14: 7, 15: 8}
WARN = set()


def Q(n, ans, warn=False):
    if warn:
        WARN.add(n)
    return qa(f"Q{n}", QT[n], PRIO[n], ans, "Terjawab dengan catatan" if warn else "Terjawab", warn)


mk = lambda *a: "".join(a)

# ---------------------------------------------------------------- data
prof = R("data_profile.csv").set_index("item")["value"]
tx, tfeat, fsum = R("layout_taxonomy.csv"), R("layout_features.csv"), R("file_summary.csv")
recon, fsmp = R("reconciliation.csv"), R("fact_sample.csv")
acc = R("accuracy_summary.csv")
accv = list(acc["value"])
acc_l, acc_q = R("accuracy_by_layout.csv"), R("accuracy_by_quality.csv")
an_t, an_l = R("anomaly_by_type.csv"), R("anomaly_by_layout.csv")
rsum, rtypo = R("reconciliation_summary.csv"), R("reconciliation_typos.csv")
tdiff, cfgc, rob = R("template_difficulty.csv"), R("config_changes.csv"), R("robustness_scenarios.csv")
mb, mm, ms = R("method_benchmark.csv"), R("method_matrix.csv"), R("method_situations.csv")
pvr, pvt = R("pivot_vs_report_totals.csv"), R("pivot_vs_truth.csv")
st_rate, slopes, rsz = R("station_reject_rate.csv"), R("trend_slopes.csv"), R("rate_by_size_shift.csv")
imp, isc, ec = R("impact_time.csv").set_index("item"), R("impact_scenarios.csv"), R("errors_caught.csv")
vplant, vchk, cx, peff = R("validation_planted.csv"), R("validation_checks.csv"), R("crosscheck_sql.csv"), R("planted_cells_effective.csv")
con = duckdb.connect(str(DB_PATH), read_only=True)
dbt = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("fact_output_tidy", "anomaly_log", "reconciliation", "truth_output")}
pivot_all, pivot_trusted = (float(x) for x in con.execute(
    "SELECT SUM(value) FILTER (WHERE metric='produced'), SUM(value) FILTER (WHERE metric='produced' AND quality IN ('ok','fixed')) FROM fact_output_tidy").fetchone())
con.close()
pt = subprocess.run([sys.executable, "-m", "pytest", str(REPO / "project" / "tests"), "-q", "-p", "no:cacheprovider"], capture_output=True, text=True)
m_ = re.search(r"(\d+) passed", pt.stdout)
n_tests = int(m_.group(1)) if m_ else 0
assert pt.returncode == 0 and n_tests > 0, pt.stdout[-500:]

N_FILES, N_CELLS = int(prof["file laporan"]), int(accv[0])
n_exact, n_okfix, n_fixed, n_flag, n_miss, n_bad = int(accv[2]), int(accv[4]), int(accv[7]), int(accv[9]), int(accv[11]), int(accv[12])
assert int(accv[13]) == 0 and accv[6] == 1.0 and int(accv[5]) == n_okfix == N_CELLS - n_bad
n_sub = int(rsum.subtotals.sum())
m_raw, m_fin = int(rsum.match_raw.sum()), int(rsum.match_final.sum())
rs = rsum.set_index(["layout", "kind"])
n_anom = int(an_t.n.sum())
at = an_t.set_index("issue_type")
n_recov = int(ec.value.iloc[6])
errs_total = int(ec.value.iloc[0])
sec_lay = {int(r.layout): r for r in tdiff.itertuples()}
bm = mb.set_index(["method", "scenario"])
S1, S2, S3, S4 = "S1 satu file (layout 1, Mar)", "S2 enam file layout 1 (Mar-Agu)", "S3 36 file, 6 layout", "S4 layout 1 berubah (Jun)"
XL, SQ, PY, PQ = "Rumus Excel", "SQL (DuckDB)", "Python (parser)", "Power Query"
ev_ = lambda m, s, c: bm.loc[(m, s), c]
manual_min, reports_mo = imp.loc["Menit copy-paste dan pengecekan per laporan"].value, imp.loc["Laporan per bulan"].value
saved_h, parser_s36 = imp.loc["Jam dihemat per tahun"].value, imp.loc["Waktu parser untuk 36 file"].value
parser_s6, parser_h = imp.loc["Waktu parser untuk laporan satu bulan (6 file)"].value, imp.loc["Jam parser per tahun"].value
copy_h = imp.loc["Jam copy-paste per tahun"].value
ok_cx = int(cx.match.sum())
eff = peff[peff.effective]
n_planted_log, n_planted_eff = len(peff), len(eff)
dirty_eff = int(vplant[vplant.fact_id == 5].detected.sum())
pvr1, pvr2 = pvr[pvr.layout == 1], pvr[pvr.layout == 2]
n_trust_cells = n_okfix

# ---- pemeriksaan (assert) sebelum menulis
assert (vchk.result == "lulus").all() and cx.match.all() and (rob.old_stopped_safely).all()
assert rtypo.shape[0] == 2 and int(rsum.suspect_subtotal.sum()) == 2 and m_fin == 4164
assert at.loc["subtotal_mismatch", "n"] == 2 and at.loc["duplicate_sheet", "n"] == 1 and n_anom == len(pd.read_csv(result("anomaly_log.csv")))
assert int(vplant[vplant.fact_id != 5].recall.min()) == 1 and (vplant.recall.dropna() == 1).all()
assert int(vchk[vchk.question == "Q15"].n_pass.iloc[0]) == n_anom
assert (rob.python_lines_changed == 0).all()
assert pvr2.same_after_repair.all() and not pvr1.same_after_repair.any()
assert abs(n_okfix + n_flag + n_miss - N_CELLS) == 0

# ---------------------------------------------------------------- 1. data
kpc = lambda c, v, l, d: f'<div class="card kpi" style="--h:var(--{c}H)"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'
rp1 = mk(
    '<div class="kpis">',
    kpc("navy", I(N_FILES), "file laporan Excel", f"{I(prof['layout'])} layout x {I(prof['bulan'])} bulan; {I(prof['sheet'])} sheet, {I(prof['merged cell'])} merged cell."),
    kpc("amber", I(N_CELLS), "nilai di tabel tidy", f"{I(dbt['truth_output'])} baris kunci x 2 metrik (produced, reject); 10 stasiun, 3 ukuran botol, 2 shift, 3 slot."),
    kpc("teal", I(n_anom), "baris anomali tercatat", f"{I(n_planted_eff)} kejadian benar-benar tertanam; {I(n_planted_log - n_planted_eff)} sel 'blank' tidak benar-benar kosong."),
    kpc("plum", I(n_sub), "subtotal laporan dicocokkan", f"{I(m_fin)} cocok sesudah pemulihan sel ({P(m_fin / n_sub, 1)})."),
    kpc("rose", P(n_exact / N_CELLS, 1), "nilai sama dengan kunci jawaban", f"Semua {I(n_okfix)} nilai ok atau fixed benar; {I(n_bad)} nilai ditandai di log."),
    kpc("sky", I(n_tests), "tes pytest lulus", "Per jenis pembaca, rekonsiliasi, akurasi, dan skenario perubahan layout."),
    '</div><h3>1.1 Data simulasi: laporan Excel berantakan dari data rapi</h3>')
tb11 = [["Enam layout dengan masalah berbeda", f"{I(N_FILES)} file", f"{I(vplant.detected.iloc[0])} file dikenali template-nya", "Template dikenali dari isi sel, bukan nama file"],
        ["Perubahan layout di bulan ke-4", "Layout 1 dan 3 (12 file bulan ke-4 sampai ke-6)", f"{I(vplant.detected.iloc[1])} file memakai config yang benar", "Config revisi: <code>L1_v2</code> dan <code>L3_v2</code>"],
        ["Subtotal salah ketik", I(vplant.planted.iloc[2]), f"{I(vplant.detected.iloc[2])} tercatat", "Keduanya di layout 2"],
        ["Sheet bulan disalin (ganda)", I(vplant.planted.iloc[3]), f"{I(vplant.detected.iloc[3])} dibuang", "Dikenali dari nama salinan dan kemiripan isi"],
        ["Sel angka kotor (n/a, '-', kali 10, ada satuan)", f"{I(vplant.planted.iloc[4:8].sum())} sel berubah", f"{I(dirty_eff)} tercatat", "Tidak ada desimal koma pada data ini"],
        ["Sel kosong ('blank')", f"{I(len(peff[peff.problem == 'blank']))} sel dicatat pembuat data", f"{I(vplant.detected.iloc[8])} berubah di file", "Pembuat data v1 tidak benar-benar mengosongkan sel"]]
rp1 += '<div class="card"><h4>Tabel 1.1a. Kejadian yang ditanam dan yang ditemukan</h4>' + table(["Jenis", "Ditanam (ground truth)", "Ditemukan parser", "Keterangan"], tb11) + \
    f'<p>Data dibuat skrip dengan seed tetap (v1, 28 Okt 2026). Data rapi {I(dbt["truth_output"])} baris dituang ke {I(N_FILES)} file; karena data rapinya diketahui, hasil parser dicocokkan sel per sel. Hash SHA-256 seluruh berkas sama dengan daftar di repo DataCenter.</p></div>'
rp1 += '<div class="card"><h4>Tabel 1.1b. Profil file laporan</h4>' + table(
    ["Ukuran", "Nilai"], [[cs(k_), I(v)] for k_, v in prof.items()]) + '</div>'
sm = fsmp.head(6)
rp1 += '<div class="card"><h4>Tabel 1.1c. Contoh isi <code>fact_output_tidy</code> (6 baris pertama; kolom <code>source_*</code> dipendekkan)</h4>' + table(
    ["Tanggal", "Shift", "Slot", "Stasiun", "Ukuran", "Metrik", "Nilai", "Kualitas", "Sel asal"],
    [[r.date, r.shift, I(r.slot), cs(r.station), cs(r.size), r.metric, I(r.value), r.quality, f"<code>{r.source_file.split('_')[1]}_{r.source_file.split('_')[2][:7]}!{r.source_cell}</code>"] for r in sm.itertuples()]) + \
    '<p>Satu baris = satu nilai. Setiap nilai bisa dilacak sampai file, sheet, dan alamat sel asal.</p></div>'
rp1 += '<h3>1.2 Tabel di database (<code>parsed.duckdb</code>)</h3><div class="card"><h4>Tabel 1.2a. Isi database</h4>' + table(
    ["Objek", "Baris", "Isi"],
    [["fact_output_tidy", I(dbt["fact_output_tidy"]), "Hasil parser: satu nilai per baris, dengan kualitas (ok, fixed, flagged, missing) dan alamat sel asal."],
     ["anomaly_log", I(dbt["anomaly_log"]), "Satu sel atau sheet bermasalah, jenis masalah, tindakan, dan nilai hasil."],
     ["reconciliation", I(dbt["reconciliation"]), "Satu subtotal laporan dibanding jumlah hasil parsing, sebelum dan sesudah pemulihan."],
     ["truth_output", I(dbt["truth_output"]), "Kunci jawaban (data rapi). Hanya untuk validasi, bukan analisis."],
     ["v_fact_wide, v_fact_trusted", "2", "View: satu baris per kunci dengan kolom produced, reject, ok; dan hanya nilai tepercaya (ok atau fixed)."]]) + \
    '<p><code>method_benchmark</code> pada rancangan disimpan sebagai CSV (<code>results/2-analysis/method_benchmark.csv</code>), tidak sebagai tabel database.</p>' + \
    '<h4>Tabel 1.2b. Pemeriksaan setelah parsing</h4>' + table(
    ["Pemeriksaan", "Hasil"],
    [["Jumlah sel hasil parsing = kunci jawaban, tanpa kunci ganda", f"{I(N_CELLS)} dari {I(N_CELLS)} {OK('Lulus')}"],
     ["Nilai ok atau fixed yang beda dari kunci jawaban", f"{I(0)} dari {I(n_okfix)} {OK('Lulus')}"],
     ["Setiap file cocok dengan tepat satu template", f"{I(N_FILES)} dari {I(N_FILES)} {OK('Lulus')}"],
     ["Parsing dua kali menghasilkan tabel identik (SHA-256)", OK("Lulus")],
     ["Anomali tercatat yang bukan sel tertanam (positif palsu)", f"{I(0)} dari {I(n_anom)} {OK('Lulus')}"],
     ["Cek silang SQL vs pandas", f"{I(ok_cx)} dari {I(len(cx))} {OK('Cocok')}"],
     ["Tes otomatis (pytest)", f"{I(n_tests)} lulus"]]) + '</div>'
FILES = {"anomaly_log": ("Satu sel atau sheet bermasalah dan tindakannya", "Q5, Q15"), "data_profile": ("Profil file laporan", "Data"), "fact_sample": ("Contoh 200 baris tabel tidy", "Data"),
         "file_summary": ("Ringkasan per file: kualitas sel dan anomali", "Q3, Q4"), "layout_features": ("Ciri layout per file (merged, subtotal, sheet, dan sebagainya)", "Q1"),
         "layout_taxonomy": ("Jenis masalah layout dan jumlah file", "Q1"), "reconciliation": ("Satu subtotal dibanding hasil parsing", "Q3"),
         "accuracy_by_layout": ("Akurasi menurut layout", "Q4"), "accuracy_by_quality": ("Akurasi menurut kualitas sel", "Q4"), "accuracy_summary": ("Ringkasan akurasi terhadap kunci jawaban", "Q4"),
         "anomaly_by_layout": ("Jenis anomali menurut layout", "Q5"), "anomaly_by_type": ("Pareto jenis anomali", "Q5"), "config_changes": ("Baris config yang diubah", "Q7"),
         "crosscheck_sql": ("SQL vs pandas", "Semua"), "errors_caught": ("Salah salin yang tertangkap", "Q14"), "impact_scenarios": ("Jam dihemat menurut asumsi", "Q13"), "impact_time": ("Waktu parser (diukur) dan copy-paste (asumsi)", "Q13"),
         "method_benchmark": ("Empat metode pada beberapa skenario", "Q8, Q10"), "method_matrix": ("Perbandingan metode menurut kriteria", "Q8"), "method_situations": ("Metode yang disarankan per situasi", "Q9"),
         "pivot_vs_report_totals": ("Pivot vs total laporan per file", "Q11"), "pivot_vs_truth": ("Pivot per stasiun dan bulan vs kunci jawaban", "Q11"), "planted_cells_effective": ("Sel tertanam yang benar-benar berubah", "Q15"),
         "rate_by_size_shift": ("Reject rate menurut ukuran dan shift", "Q12"), "reconciliation_summary": ("Match rate menurut layout", "Q3"), "reconciliation_typos": ("Dua subtotal salah ketik", "Q3, Q15"),
         "robustness_scenarios": ("Sembilan skenario perubahan layout", "Q6"), "station_reject_rate": ("Reject rate per stasiun", "Q12"), "template_difficulty": ("Ukuran config dan sel belum terselesaikan per layout", "Q2"),
         "trend_slopes": ("Kemiringan reject rate per stasiun", "Q12"), "validation_checks": ("Pemeriksaan validitas", "Q4, Q6, Q15"), "validation_planted": ("Kejadian tertanam vs terdeteksi", "Q15")}
resfiles = sorted(p for d in (RES_PREP, RES_ANALYSIS) for p in d.glob("*.csv"))
miss = [p.stem for p in resfiles if p.stem not in FILES]
assert not miss, f"CSV hasil belum didokumentasikan di FILES: {miss}"
assert all((p.stem in FILES) for p in resfiles) and set(FILES) == {p.stem for p in resfiles}
rp1 += '<div class="card"><h4>Tabel 1.2c. Data hasil analisis (<code>project/results/</code>)</h4>' + table(
    ["File", "Isi", "Baris", "Menjawab"], [[f"<code>{p.stem}.csv</code>", FILES[p.stem][0], I(len(pd.read_csv(p))), FILES[p.stem][1]] for p in resfiles]) + \
    f'<p>{I(len(resfiles))} file CSV, ditambah {I(len(list(RES_PRESENT.glob("dash_*.csv"))))} CSV data dashboard, notebook, dan one-sheet. Tabel tidy lengkap ({I(N_CELLS)} baris) ada di database dan <code>project/data/parsed/</code>, tidak di-commit.</p></div>'
rp1 += '<h3>1.3 Angka kunci (KPI)</h3><div class="card"><h4>Tabel 1.3. Ukuran kinerja (definisi di <code>project/docs/metrics.md</code>)</h4>' + table(
    ["Ukuran", "Hasil", "Keterangan"],
    [["Nilai sama persis dengan kunci jawaban", f"{I(n_exact)} dari {I(N_CELLS)} ({P(n_exact / N_CELLS, 1)})", f"Nilai ok atau fixed: {I(n_okfix)} dari {I(n_okfix)} benar; {I(n_bad)} nilai ditandai"],
     ["Subtotal cocok", f"{P(m_raw / n_sub, 1)} menjadi {P(m_fin / n_sub, 1)}", f"{I(m_raw)} menjadi {I(m_fin)} dari {I(n_sub)}, sebelum dan sesudah pemulihan sel"],
     ["Kejadian tertanam yang terdeteksi", "100%", f"{I(n_planted_eff)} kejadian nyata; {I(0)} positif palsu"],
     ["Baris config untuk layout bulan ke-4", f"{I(rob.config_lines_changed.iloc[0])} baris", "Tanpa mengubah kode Python"],
     ["Waktu parser, 36 file", f"{D(parser_s36, 1)} detik", "Terukur; rumus Excel dan SQL satu file sekitar satu detik"],
     ["Jam copy-paste dihemat per tahun", f"{D(saved_h, 0)} jam", "estimated, simulated (asumsi)"]]) + \
    '<p>Contoh pada halaman Design memakai angka karangan, bukan hasil data ini.</p></div>'

# ---------------------------------------------------------------- 2. business questions
SHORT = {"merged_header": "Header digabung (merged cell)", "multi_table": "Beberapa tabel dalam satu sheet", "subtotal_inside": "Subtotal di tengah data", "dates_as_columns": "Tanggal sebagai kolom",
         "hidden_or_footnote": "Baris tersembunyi atau catatan kaki", "inconsistent_labels": "Label tidak seragam", "sheet_per_period": "Satu sheet per minggu", "text_numbers": "Angka bertipe teks",
         "extra_columns": "Kolom catatan atau paraf"}
txi = tx.set_index("problem")
reader_lab = {"date_columns": "Tanggal sebagai kolom", "date_shift_groups": "Blok per tanggal dan shift", "wide_groups": "Kelompok kolom lebar", "flat": "Tabel datar"}
s21 = mk('<h3 id="sec21">2.1 Masalah layout dan kesulitan template <span class="qlist">Q1, Q2</span></h3><div class="card">',
         Q(1, f"Ada {I(len(tx))} jenis masalah layout pada {I(N_FILES)} file (rancangan memperkirakan enam). Paling sering: header digabung, beberapa tabel dalam satu sheet, dan subtotal di tengah data, masing-masing di {I(txi.loc['merged_header', 'files'])} file. "
              f"Tanggal sebagai kolom, baris tersembunyi atau catatan kaki, label tidak seragam, satu sheet per minggu, dan angka bertipe teks masing-masing di {I(txi.loc['dates_as_columns', 'files'])} file. "
              f"Kolom catatan atau paraf hanya muncul di {I(txi.loc['extra_columns', 'files'])} file (layout 1, bulan ke-4 sampai ke-6). Satu layout bisa memuat beberapa masalah sekaligus."),
         Q(2, f"Paling sulit adalah layout 6 (header digabung, baris tersembunyi, dan catatan kaki): {I(sec_lay[6].unresolved_cells)} sel ({D(sec_lay[6].unresolved_per_1000_cells, 1)} per 1.000 sel) tidak bisa dipastikan nilainya. "
              f"Layout 3 dan 4 menyusul ({D(sec_lay[3].unresolved_per_1000_cells, 1)} per 1.000 sel). Penyebabnya bukan config yang lebih besar (semuanya {I(tdiff.config_lines.min())} sampai {I(tdiff.config_lines.max())} baris), "
              f"tetapi tidak adanya subtotal untuk memulihkan sel kotor: layout 2 yang punya total baris dan subtotal hanya {D(sec_lay[2].unresolved_per_1000_cells, 2)} per 1.000 sel, layout 1 yang punya subtotal {D(sec_lay[1].unresolved_per_1000_cells, 1)}. "
              f"Layout 5 tidak punya anomali karena pembuat data tidak mengotori layout itu. Jumlah anomali per 1.000 sel sama (sekitar {D(sec_lay[1].anomaly_per_1000_cells, 0)}) di layout yang dikotori."),
         '<h4>Grafik 2.1a. Jumlah file menurut jenis masalah layout</h4>',
         hbars([(SHORT[r.problem], r.files, BLUE, f"{SHORT[r.problem]}: {I(r.files)} file") for r in tx.itertuples()], lambda v: I(v), "File menurut jenis masalah layout", 14),
         '<h4>Tabel 2.1b. Masalah layout menurut layout (jumlah file)</h4>',
         table(["Masalah", "Total file"] + [f"Layout {i}" for i in range(1, 7)],
               [[cs(r.description), I(r.files)] + [I(getattr(r, f"layout{i}")) if getattr(r, f"layout{i}") else "-" for i in range(1, 7)] for r in tx.itertuples()]),
         '<h4>Tabel 2.1c. Config dan sel belum terselesaikan per layout</h4>',
         table(["Layout", "Jenis pembaca", "File config", "Baris config", "Sel", "Baris anomali", "Sel belum terselesaikan", "Per 1.000 sel"],
               [[I(r.layout), reader_lab[r.reader], I(r.config_files), I(r.config_lines), I(r.cells), I(r.anomaly_rows), I(r.unresolved_cells), D(r.unresolved_per_1000_cells, 1)] for r in tdiff.itertuples()]),
         '<p>Sel belum terselesaikan = sel berstatus flagged (nilai dipertahankan, mencurigakan) atau missing (tidak ada nilai).</p></div>')

lab_rec = {(1, "subtotal"): "Layout 1: subtotal", (2, "row_total"): "Layout 2: total baris", (2, "subtotal"): "Layout 2: subtotal"}
s22 = mk('<h3 id="sec22">2.2 Rekonsiliasi dan akurasi <span class="qlist">Q3, Q4</span></h3><div class="card">',
         Q(3, f"Tidak semua, tetapi hampir: {I(m_fin)} dari {I(n_sub)} subtotal ({P(m_fin / n_sub, 1)}) cocok sesudah pemulihan sel, naik dari {I(m_raw)} ({P(m_raw / n_sub, 1)}) sebelum pemulihan. "
              f"Total baris layout 2 cocok {P(rs.loc[(2, 'row_total'), 'match_rate_final'], 0)}. Dari {I(n_sub - m_fin)} yang tidak cocok, {I(rsum.suspect_subtotal.sum())} adalah subtotal salah ketik yang sengaja ditanam (keduanya ditemukan), "
              f"dan {I(rsum.open_bad_cells.sum())} memuat sel yang tidak bisa dipastikan (layout 1: {I(rs.loc[(1, 'subtotal'), 'open_bad_cells'])}, layout 2: {I(rs.loc[(2, 'subtotal'), 'open_bad_cells'])}). Layout 3, 4, 5, dan 6 tidak punya subtotal sehingga tidak bisa direkonsiliasi."),
         Q(4, f"{P(n_exact / N_CELLS, 1)}: {I(n_exact)} dari {I(N_CELLS)} nilai sama persis dengan data rapi asli. Nilai yang parser anggap tepercaya (ok atau fixed, {I(n_okfix)} nilai) benar semuanya ({P(1, 0)}), termasuk {I(n_fixed)} nilai yang dibersihkan atau dipulihkan. "
              f"Sisanya {I(n_bad)} nilai ditandai di log: {I(n_flag)} flagged (semuanya bernilai 10 kali kunci jawaban) dan {I(n_miss)} missing. Tidak ada nilai salah yang lolos tanpa tanda."),
         '<h4>Grafik 2.2a. Subtotal yang cocok sebelum dan sesudah pemulihan sel</h4>',
         hbars([(f"{lab_rec[(r.layout, r.kind)]}, {w}", v, c, f"{lab_rec[(r.layout, r.kind)]}, {w}: {P(v, 1)}") for r in rsum.itertuples()
                for w, v, c in (("sebelum", r.match_rate_raw, GREY), ("sesudah", r.match_rate_final, BLUE))], lambda v: P(v, 1), "Match rate subtotal", 1.12),
         legend([(GREY, "Sebelum pemulihan sel"), (BLUE, "Sesudah pemulihan sel")]),
         '<h4>Tabel 2.2b. Rekonsiliasi menurut jenis subtotal</h4>',
         table(["Jenis", "Subtotal", "Cocok sebelum", "Cocok sesudah", "Dipulihkan oleh subtotal ini", "Sel belum pasti", "Salah ketik", "Match rate sesudah"],
               [[lab_rec[(r.layout, r.kind)], I(r.subtotals), I(r.match_raw), I(r.match_final), I(r.recovered_this), I(r.open_bad_cells), I(r.suspect_subtotal), P(r.match_rate_final, 1)] for r in rsum.itertuples()]),
         '<h4>Tabel 2.2c. Dua subtotal salah ketik yang ditemukan</h4>',
         table(["File", "Sel laporan", "Total di laporan", "Jumlah hasil parsing", "Selisih"], [[f"<code>{r.source_file}</code>", f"<code>{r.report_cell}</code>", I(r.report_total), I(r.parsed_total_final), "-" + I(abs(r.diff_final))] for r in rtypo.itertuples()]),
         '<h4>Tabel 2.2d. Akurasi menurut layout</h4>',
         table(["Layout", "Nilai", "Sama persis", "Ok", "Fixed", "Flagged", "Missing", "Sama persis (semua)", "Sama persis (ok atau fixed)"],
               [[I(r.layout), I(r.cells), I(r.exact), I(r.ok), I(r.fixed), I(r.flagged), I(r.missing), P(r.exact_rate, 1), P(r.unflagged_exact_rate, 0)] for r in acc_l.itertuples()]),
         '<h4>Tabel 2.2e. Akurasi menurut kualitas sel</h4>',
         table(["Kualitas", "Nilai", "Sama persis", "Persen"], [[r.quality, I(r.cells), I(r.exact), P(r.exact_rate, 0)] for r in acc_q.itertuples()]),
         '<p>Flagged dan missing sengaja tidak dihitung sebagai benar: nilainya dipertahankan atau dikosongkan agar manusia memeriksanya.</p></div>')

vital_ = [bool(s > 0.01) for s in an_t.share]
s23 = mk('<h3 id="sec23">2.3 Anomali sel <span class="qlist">Q5</span></h3><div class="card">',
         Q(5, f"Empat jenis hampir sama banyak: tanda '-' ({I(at.loc['dash', 'n'])}), teks 'n/a' ({I(at.loc['text_na', 'n'])}), angka kali 10 ({I(at.loc['outlier', 'n'])}), dan angka dengan satuan seperti '120 btl' ({I(at.loc['unit_text', 'n'])}); "
              f"keempatnya {P(an_t.cum_share.iloc[3], 1)} dari {I(n_anom)} baris anomali, ditambah {I(at.loc['subtotal_mismatch', 'n'])} subtotal salah ketik dan {I(at.loc['duplicate_sheet', 'n'])} sheet ganda. "
              f"Di setiap layout yang dikotori jenisnya merata (layout 1 sampai 4: {I(an_l.layout1[0])} per jenis; layout 6: {I(an_l.layout6[0])} dan {I(an_l.layout6[2])}); layout 5 tidak punya anomali. "
              f"Desimal koma tidak ada karena pembuat data tidak menanamnya, dan sel kosong tidak benar-benar berubah. Yang selalu bisa dibersihkan adalah angka dengan satuan ({I(at.loc['unit_text', 'fixed'])} dari {I(at.loc['unit_text', 'n'])})."),
         '<h4>Grafik 2.3a. Pareto jenis anomali</h4>',
         pareto_svg([r.issue_type for r in an_t.itertuples()], list(an_t.share), list(an_t.cum_share), vital_,
                    [f"{r.issue_type}: {I(r.n)} baris ({P(r.share, 1)}), dipulihkan atau dibersihkan {I(r.fixed)}, ditandai {I(r.flagged)}" for r in an_t.itertuples()], "Pareto jenis anomali"),
         legend([(BLUE, "Jenis dengan porsi di atas 1%"), (SOFT, "Lainnya")]),
         '<h4>Tabel 2.3b. Jenis anomali dan tindakan</h4>',
         table(["Jenis", "Baris", "Fixed", "Flagged", "Dropped", "Porsi", "Kumulatif"], [[r.issue_type, I(r.n), I(r.fixed), I(r.flagged), I(r.dropped), P(r.share, 1), P(r.cum_share, 1)] for r in an_t.itertuples()]),
         '<h4>Tabel 2.3c. Jenis anomali menurut layout</h4>',
         table(["Jenis"] + [f"Layout {i}" for i in (1, 2, 3, 4, 6)], [[r.issue_type] + [I(getattr(r, f"layout{i}")) for i in (1, 2, 3, 4, 6)] for r in an_l.itertuples()]),
         '<p>Arti jenis: <code>dash</code> tanda "-" menggantikan angka, <code>text_na</code> teks "n/a", <code>outlier</code> angka bernilai 10 kali wajar, <code>unit_text</code> angka dengan satuan. Tindakan fixed = nilai dipulihkan lewat subtotal atau dibersihkan; flagged = perlu dicek manusia.</p></div>')

rb = rob.set_index("id")
s24 = mk('<h3 id="sec24">2.4 Ketahanan terhadap perubahan layout <span class="qlist">Q6, Q7</span></h3><div class="card">',
         Q(6, f"Ya, dalam arti parser tidak pernah menulis angka salah. Dari {I(len(rob))} skenario perubahan layout ({I(2)} nyata dari bulan ke-4, {I(7)} sintetis), config lama menghentikan parser dengan pesan yang jelas pada {I(int(rob.old_stopped_safely.sum()) - 1)} skenario, "
              f"dan satu skenario (sheet catatan tambahan) tetap terbaca benar. Dengan config baru, seluruh sel tepercaya cocok dengan kunci jawaban pada setiap skenario (misalnya {cs(rb.loc['R1', 'new_config'])}). "
              f"Perubahan yang dibutuhkan hanya 0 sampai {I(rob.config_lines_changed.max())} baris config atau {I(1)} baris kamus nama stasiun, dan {I(rob.python_lines_changed.max())} baris Python. Perubahan struktur yang belum punya jenis pembaca (di luar empat jenis) tetap butuh kode baru."),
         Q(7, f"Layout 1 dan 3 bulan ke-4: file config baru {I(cfgc.lines_in_new_file.iloc[0])} baris dengan {I(cfgc.lines_changed.iloc[0])} baris berbeda dari versi lama ({I(cfgc.lines_changed_excluding_id_description.iloc[0])} di luar id dan deskripsi), {I(cfgc.python_lines_changed.iloc[0])} baris Python. "
              f"Template baru dari nol rata-rata {I(cfgc.lines_in_new_file.iloc[2])} baris config ({I(cfgc.lines_changed_excluding_id_description.iloc[2])} di luar id dan deskripsi). Waktu penyesuaian oleh manusia tidak diukur dengan stopwatch; yang dicatat adalah jumlah baris.", warn=True),
         '<h4>Tabel 2.4a. Skenario perubahan layout</h4>',
         table(["ID", "Jenis", "Skenario", "Config lama", "Config baru", "Baris config diubah", "Baris kamus", "Baris Python"],
               [[r.id, r.kind, cs(r.scenario), cs(r.old_config), cs(r.new_config), I(r.config_lines_changed), I(r.lookup_lines_changed), I(r.python_lines_changed)] for r in rob.itertuples()]),
         '<p>R1 dan R2 adalah perubahan nyata dari generator (bulan ke-4); S1 sampai S7 dibuat dengan mengubah salinan file. Pesan berhenti: <code>UnknownTemplate</code> (tidak ada template cocok) atau <code>UnknownLabel</code> (nama tidak dikenal). Parser tidak menebak.</p>',
         '<h4>Tabel 2.4b. Baris config yang diubah</h4>',
         table(["Perubahan", "Baris di file baru", "Baris berbeda", "Di luar id dan deskripsi", "Baris Python diubah"],
               [[cs(r.to_config) if r.layout == 0 else f"Layout {I(r.layout)}: {r.from_config} menjadi {cs(r.to_config)}", I(r.lines_in_new_file), I(r.lines_changed), I(r.lines_changed_excluding_id_description), I(r.python_lines_changed)] for r in cfgc.itertuples()]),
         '</div>')

sec_ = lambda m, s: float(ev_(m, s, "run_seconds"))


def mcell(row, x):
    """Sel tabel perbandingan metode: baris 0 detik, baris 1 persen, selain itu teks (angka ribuan dibiarkan)."""
    if pd.isna(x):
        return "-"
    if row == 0:
        return D(float(x), 2)
    if row == 1:
        return P(float(x), 1)
    s = str(x)
    s = re.sub(r"(?<=\d)\.(?=\d{1,2}(?!\d))", ",", s)
    for tok in re.findall(r"\d+(?:[.,]\d+)*", s):
        REG.add(tok)
    return esc(s)

s25 = mk('<h3 id="sec25">2.5 Empat metode dibandingkan <span class="qlist">Q8, Q9, Q10</span></h3><div class="card">',
         Q(8, f"Tidak ada satu pemenang. Ukuran pekerjaan membuat file layout 1: SQL {I(ev_(SQ, S1, 'build_size'))} baris, rumus Excel {I(ev_(XL, S1, 'build_size'))} rumus unik, Python {I(ev_(PY, S1, 'build_size'))} baris config (memakai {I(496)} baris mesin yang dibuat sekali), dan Power Query {I(ev_(PQ, S1, 'build_size'))} baris M (tidak dijalankan). "
              f"Saat layout bulan ke-4 berubah tanpa diubah apa pun: SQL tetap benar ({P(ev_(SQ, S4, 'result_match_before_fix'), 1)}), rumus Excel jalan tetapi hanya {P(ev_(XL, S4, 'result_match_before_fix'), 1)} benar dan dua tanggal terakhir hilang tanpa peringatan, "
              f"Python berhenti dan tidak menulis apa pun. Sesudah perbaikan: SQL {I(0)} perubahan, Excel {I(1)} sel parameter, Python {I(2)} baris config ({P(ev_(PY, S4, 'result_match'), 1)} benar). "
              f"Hanya parser Python yang merekonsiliasi dengan subtotal ({I(n_sub)}) dan memulihkan sel ({I(n_recov)}); Excel dan SQL berhenti di {P(ev_(XL, S1, 'result_match'), 1)} karena sel kotor tidak dibersihkan. Waktu pembuatan oleh manusia tidak diukur, dan Power Query tidak dijalankan karena tidak ada Excel.", warn=True),
         Q(9, f"Untuk end user dengan satu atau dua file: rumus Excel. Untuk tim non-programmer dengan banyak file satu layout: Power Query (penilaian, belum dijalankan). Untuk banyak file dengan banyak layout dan perlu bukti kebenaran: parser Python. Untuk data yang sudah berupa tabel di database: SQL. "
              f"Dasar tiap saran ada di tabel 2.5d; hanya Power Query yang berdasar penilaian.", warn=True),
         Q(10, f"Satu file layout 1: parser Python {D(sec_(PY, S1), 2)} detik, SQL {D(sec_(SQ, S1), 2)} detik, rumus Excel {D(sec_(XL, S1), 2)} detik (hitung ulang LibreOffice, bukan Excel). Enam file: {D(sec_(PY, S2), 2)}, {D(sec_(SQ, S2), 1)}, dan {D(sec_(XL, S2), 1)} detik. "
              f"Untuk 36 file dengan enam layout hanya parser Python yang dikerjakan: {D(sec_(PY, S3), 1)} detik ({D(sec_(PY, S3) / 36, 2)} detik per file). Rumus Excel dan SQL perlu definisi untuk lima layout lain dan tidak dikerjakan; Power Query tidak dijalankan.", warn=True),
         '<h4>Grafik 2.5a. Waktu proses menurut metode (detik)</h4>',
         gbars(["Satu file (S1)", "Enam file (S2)"], [("Rumus Excel", GREY, [sec_(XL, S1), sec_(XL, S2)]), ("SQL (DuckDB)", SOFT, [sec_(SQ, S1), sec_(SQ, S2)]), ("Python (parser)", BLUE, [sec_(PY, S1), sec_(PY, S2)])],
               lambda v: D(v, 1), "Waktu proses empat metode", rot=0, h=260),
         legend([(GREY, "Rumus Excel (LibreOffice)"), (SOFT, "SQL (DuckDB)"), (BLUE, "Python (parser)")]),
         '<h4>Tabel 2.5b. Benchmark menurut skenario</h4>',
         table(["Metode", "Skenario", "File", "Ukuran pekerjaan", "Waktu (detik)", "Cocok kunci jawaban", "Status"],
               [[r.method, cs(r.scenario), I(r.n_files), f"{I(r.build_size)} {cs(r.build_unit)}" if pd.notna(r.build_size) else "-", D(r.run_seconds, 2) if pd.notna(r.run_seconds) else "-",
                 P(r.result_match, 1) if pd.notna(r.result_match) else "-", r.status] for r in mb.itertuples()]),
         '<p>Waktu pembuatan dan perbaikan oleh manusia (<code>build_minutes</code>, <code>fix_minutes</code>) kosong karena tidak diukur. Waktu Excel adalah hitung ulang LibreOffice; waktu SQL termasuk memuat sel ke tabel.</p>',
         '<h4>Tabel 2.5c. Perbandingan menurut kriteria</h4>',
         table(["Kriteria", "Dasar", "Rumus Excel", "SQL", "Python (parser)", "Power Query"],
               [[cs(r.criterion), r.basis] + [mcell(r.Index, x) for x in (r.excel_formula, r.sql, r.python_parser, r.power_query)] for r in mm.itertuples()]),
         '<h4>Tabel 2.5d. Metode yang disarankan per situasi</h4>',
         table(["Situasi", "Metode", "Alasan", "Dasar"], [[cs(r.situation), f"<b>{r.recommended_method}</b>", cs(r.reason), r.basis] for r in ms.itertuples()]),
         '</div>')

s26 = mk('<h3 id="sec26">2.6 Setelah data rapi: pivot dan pola <span class="qlist">Q11, Q12</span></h3><div class="card">',
         Q(11, f"Sebagian. Layout 2: pivot sama persis dengan total laporan pada {I(pvr2.same_after_repair.sum())} dari {I(len(pvr2))} file, setelah sel kotor dipulihkan lewat subtotal. Layout 1: tidak ({I(pvr1.same_after_repair.sum())} dari {I(len(pvr1))} file); selisih sesudah pemulihan sampai {P((pvr1.diff_final / pvr1.report_total).abs().max(), 2)} per file, "
              f"karena nilai flagged (kali 10) tetap ikut dijumlahkan dan sel missing tidak. Total produksi pada pivot semua nilai {I(pivot_all)} botol, sedangkan hanya nilai tepercaya {I(pivot_trusted)} botol (selisih {P((pivot_all - pivot_trusted) / pivot_trusted, 1)}). "
              f"Terhadap kunci jawaban, per stasiun per bulan ({I(len(pvt))} sel pivot): selisih output terbesar {P(pvt.produced_diff_pct.abs().max(), 1)} dan reject rate terbesar {D(pvt.reject_rate_diff_pp.abs().max(), 2)} poin persentase. Layout 3 sampai 6 tidak punya total laporan untuk dibandingkan.", warn=True),
         Q(12, f"Tidak ada tren: kemiringan reject rate per stasiun paling besar {D(slopes.slope_pp_per_block.abs().max(), 3)} poin persentase per bulan. Yang terlihat adalah perbedaan antarstasiun: {cs(st_rate.station.iloc[0])} {P(st_rate.reject_rate.iloc[0], 2)} tertinggi dan {cs(st_rate.station.iloc[-1])} {P(st_rate.reject_rate.iloc[-1], 2)} terendah, "
              f"selisih {D(st_rate.reject_rate.iloc[0] / st_rate.reject_rate.iloc[-1], 1)} kali. Ukuran botol ({P(rsz.reject_rate.min(), 2)} sampai {P(rsz.reject_rate.max(), 2)}) dan shift ({P(rsz.reject_rate.iloc[3], 2)} dan {P(rsz.reject_rate.iloc[4], 2)}) hampir sama. Pola ini berasal dari data simulasi dan dihitung dari kunci jawaban."),
         '<h4>Grafik 2.6a. Reject rate per stasiun (6 bulan)</h4>',
         hbars([(cs(r.station), r.reject_rate, BLUE if i == 0 else SOFT, f"{cs(r.station)}: {P(r.reject_rate, 2)}") for i, r in enumerate(st_rate.itertuples())], lambda v: P(v, 2), "Reject rate per stasiun", 0.025),
         '<h4>Tabel 2.6b. Pivot vs total laporan per file</h4>',
         table(["File", "Layout", "Total laporan", "Pivot semua nilai", "Pivot sesudah pemulihan", "Selisih sesudah", "Sama"],
               [[f"<code>{r.source_file}</code>", I(r.layout), I(r.report_total), I(r.pivot_total_raw), I(r.pivot_total_final), I(r.diff_final), OK("Ya") if r.same_after_repair else NO("Tidak")] for r in pvr.itertuples()]),
         '<h4>Tabel 2.6c. Kemiringan reject rate per stasiun</h4>',
         table(["Stasiun", "Kemiringan (poin persen per bulan)", "Bulan pertama", "Bulan terakhir", "Terendah", "Tertinggi"],
               [[cs(r.station), D(r.slope_pp_per_block, 3), P(r.rate_first_block, 2), P(r.rate_last_block, 2), P(r.rate_min_block, 2), P(r.rate_max_block, 2)] for r in slopes.itertuples()]),
         '<h4>Tabel 2.6d. Reject rate menurut ukuran dan shift</h4>',
         table(["Dimensi", "Kelompok", "Output", "Reject", "Reject rate"], [[r.dimension, cs(r.group), I(r.produced), I(r.reject), P(r.reject_rate, 2)] for r in rsz.itertuples()]),
         '</div>')

s27 = mk('<h3 id="sec27">2.7 Dampak <span class="qlist">Q13, Q14</span></h3><div class="card">',
         Q(13, f"Sekitar {D(saved_h, 0)} jam kerja per tahun (estimated, simulated): {I(reports_mo)} laporan per bulan x {I(manual_min)} menit x {I(12)} bulan / {I(60)} = {D(copy_h, 0)} jam copy-paste, dikurangi waktu parser {D(parser_s36, 1)} detik untuk {I(36)} file ({D(parser_h, 4)} jam per tahun). "
              f"Jumlah laporan dan menit per laporan adalah asumsi; dalam rentang skenario di bawah hasilnya {D(isc.hours_saved_per_year.min(), 0)} sampai {D(isc.hours_saved_per_year.max(), 0)} jam.", warn=True),
         Q(14, f"Pembandingnya belum dikerjakan: rekap copy-paste manual pada sampel file tidak dilakukan, jadi tidak ada angka perbandingan. Yang diketahui: dari {I(errs_total)} sel angka atau subtotal salah atau hilang di laporan, {I(ec.value.iloc[3])} tercatat di log anomali dan {I(ec.value.iloc[4])} lolos tanpa tercatat. "
              f"Sebanyak {I(ec.value.iloc[1])} berada di file yang punya subtotal (layout 1 dan 2) dan {I(ec.value.iloc[2])} di file tanpa subtotal; {I(n_recov)} sel dipulihkan tepat lewat subtotal dan {I(ec.value.iloc[5])} sel bersatuan dibersihkan.", warn=True),
         '<h4>Tabel 2.7a. Waktu dan jam dihemat</h4>',
         table(["Ukuran", "Nilai", "Satuan", "Dasar"], [[cs(r.Index), D(r.value, 4) if r.value < 0.01 else D(r.value, 1 if r.value < 10 and r.value % 1 else 0), r.unit, r.basis] for r in imp.itertuples()]),
         '<h4>Tabel 2.7b. Jam dihemat per tahun menurut asumsi</h4>',
         table(["Laporan per bulan", "Menit per laporan", "Jam dihemat per tahun"], [[I(r.reports_per_month), I(r.minutes_per_report), D(r.hours_saved_per_year, 0)] for r in isc.itertuples()]),
         '<h4>Tabel 2.7c. Kesalahan yang tertangkap</h4>',
         table(["Ukuran", "Nilai"], [[cs(r.item), I(r.value) if pd.notna(r.value) else "tidak dilakukan"] for r in ec.itertuples()]),
         '</div>')

vp = vplant.copy()
s28 = mk('<h3 id="sec28">2.8 Validitas <span class="qlist">Q15</span></h3><div class="card">',
         Q(15, f"Ya untuk kejadian yang benar-benar berubah di file: enam layout ({I(vp.detected.iloc[0])} dari {I(vp.planted.iloc[0])} file), perubahan bulan ke-4 ({I(vp.detected.iloc[1])} dari {I(vp.planted.iloc[1])}), subtotal salah ketik ({I(vp.detected.iloc[2])} dari {I(vp.planted.iloc[2])}), sheet ganda ({I(vp.detected.iloc[3])} dari {I(vp.planted.iloc[3])}), "
              f"dan sel kotor ({I(dirty_eff)} dari {I(vp.planted.iloc[4:8].sum())}). Positif palsu: {I(0)} dari {I(n_anom)} anomali tercatat adalah sel yang tidak ditanam. Catatan: pembuat data mencatat {I(n_planted_log)} sel bermasalah, tetapi {I(len(peff[peff.problem == 'blank']))} sel jenis 'blank' tidak benar-benar dikosongkan, "
              f"sehingga yang nyata {I(n_planted_eff)}; kelemahan ini ada pada generator v1, bukan parser.", warn=True),
         '<h4>Tabel 2.8a. Kejadian tertanam vs terdeteksi</h4>',
         table(["Kejadian", "Pemeriksaan", "Ditanam", "Terdeteksi", "Recall", "Catatan"],
               [[cs(r.fact), cs(r.check), I(r.planted), I(r.detected), P(r.recall, 0) if pd.notna(r.recall) else "-", cs(r.note) if pd.notna(r.note) else ""] for r in vplant.itertuples()]),
         '<h4>Tabel 2.8b. Pemeriksaan validitas</h4>',
         table(["Pertanyaan", "Pemeriksaan", "Diuji", "Lulus", "Hasil"], [[r.question, cs(r.check), I(r.n_tested), I(r.n_pass), OK("Lulus")] for r in vchk.itertuples()]),
         '<h4>Tabel 2.8c. Cek silang SQL vs pandas</h4>',
         table(["Pemeriksaan", "SQL", "pandas", "Cocok"], [[cs(r.check), D(r.sql, 6) if abs(r.sql) < 1 else I(r.sql), D(r.pandas, 6) if abs(r.pandas) < 1 else I(r.pandas), OK("Ya")] for r in cx.itertuples()]),
         '</div>')
rp2_body = mk(s21, s22, s23, s24, s25, s26, s27, s28)
qn_all = sorted(int(x) for x in re.findall(r'<span class="qn">Q(\d+)</span>', rp2_body))
assert qn_all == list(range(1, 16)), qn_all
npr = {k_: sum(1 for v in PRIO.values() if v == k_) for k_ in ("Utama", "Pendukung", "Tambahan")}
nw = len(WARN)
wtxt = ", ".join(f"Q{n}" for n in sorted(WARN))
chips = mk('<div class="qchips">', "".join(f'<a class="qc{" w" if n in WARN else ""}" href="#sec{SEC[n]}" title="{esc(QT[n])}">Q{n}</a>' for n in range(1, 16)), '</div>')
rp2 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> semua {len(QT)} pertanyaan terjawab ({npr["Utama"]} Utama, {npr["Pendukung"]} Pendukung, {npr["Tambahan"]} Tambahan). '
         f'{nw} jawaban dengan catatan (kuning): {wtxt}. Klik nomor pertanyaan untuk melompat ke pembahasannya. Pertanyaan utama project dijawab di bagian 7.</p>',
         chips, '<p class="report-note">Q hijau = terjawab, Q kuning = terjawab dengan catatan. Pembahasan dikelompokkan per tabel atau grafik bukti (2.1 sampai 2.8). Catatan kuning pada dasarnya tiga hal: Power Query tidak dijalankan dan waktu manusia tidak diukur, angka dampak memakai asumsi, dan sebagian pembanding tidak dikerjakan (Q14).</p></div>', rp2_body)

# ---------------------------------------------------------------- 3-5. dataset, tools, alur
CODE_REL = "project/code/"
npy = len(list((REPO / CODE_REL).rglob("*.py")))
loc = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in (REPO / CODE_REL).rglob("*.py"))
nsql = len(list((REPO / CODE_REL).rglob("*.sql")))
ntest_files = len(list((REPO / "project" / "tests").glob("test_*.py")))
ncfg = len(list((REPO / "project" / "config" / "templates").glob("*.yaml")))
d_st = ["Water Treatment", "Syrup Mixing", "Blow Molding", "Rinsing", "Filling", "Capping", "Labeling", "Fill & Cap Inspection", "Shrink Wrapping", "Palletizing"]
r_st = ["Water Treatment", "Mixing", "Blow Molding", "Rinsing", "Filling", "Capping", "Labeling", "Cartoning", "Shrink Wrap", "Palletizing"]
assert sorted(r_st) == sorted(st_rate.station), "daftar stasiun realisasi"
rp3 = mk('<div class="card"><p><b>Jawaban singkat:</b> ukuran dan sumber data sesuai rancangan, dengan beberapa perbedaan nyata: metrik yang dibaca dua (produced dan reject, bukan tiga), enam layout berbeda dari usulan T1 sampai T6, '
         'perubahan bulan ke-4 menimpa dua layout (bukan satu), sel kotor tidak mencakup desimal koma dan sel kosong tidak efektif, serta dua nama stasiun berbeda. Lisensi dataset tidak berlaku karena data buatan sendiri.</p></div>',
         table(["Aspek", "Rancangan", "Realisasi", "Verdict"], [
             ["Sumber", "Simulasi buatan sendiri, <code>scripts/generate_reports.py</code>, versi v1, 28 Okt 2026, seed 25260302", f"<code>01_generate_reports.py</code> (pindah ke struktur standar), v1, seed 25260302; hash {I(39)} berkas sama dengan daftar di repo DataCenter", OK("Sesuai")],
             ["Ukuran", "10 stasiun, 3 ukuran, 2 shift, ±150 hari kerja, 6 template, ±36 file", f"10 stasiun, 3 ukuran, 2 shift x 3 slot, 150 hari kerja, {I(prof['layout'])} layout, {I(N_FILES)} file", OK("Sesuai")],
             ["Metrik", "Tiga: input, OK, NG", "Dua: produced dan reject; OK dihitung (produced dikurangi reject)", NO("Berubah")],
             ["Ukuran tabel tidy", "±27.000 baris (10 x 3 x 2 x 150 x 3 metrik)", f"{I(N_CELLS)} baris ({I(dbt['truth_output'])} kunci x 2 metrik; ditambah slot per shift)", PART("Sesuai + penyesuaian")],
             ["Stasiun", ", ".join(d_st), ", ".join(r_st) + ". Syrup Mixing menjadi Mixing, Fill & Cap Inspection menjadi Cartoning, Shrink Wrapping menjadi Shrink Wrap", PART("Sesuai + penyesuaian")],
             ["Layout", "Enam template T1 sampai T6 (tanggal kolom, header bertingkat, 2 tabel per sheet, subtotal mingguan, catatan dalam sel, 1 sheet per bulan)",
              f"Enam layout dengan {I(len(tx))} jenis masalah; urutan dan gabungan masalah berbeda dari usulan (lihat Tabel 2.1b)", PART("Sesuai + penyesuaian")],
             ["Fakta 2: perubahan bulan ke-4", "Satu template menambah kolom Remark dan menggeser blok dua baris", "Layout 1: judul 4 baris dan kolom Catatan/Paraf; layout 3: nama sheet Minggu menjadi Wk; masing-masing 2 baris config", NO("Berubah")],
             ["Fakta 3: subtotal salah ketik", "Dua subtotal", f"{I(rtypo.shape[0])} subtotal di layout 2, keduanya ditemukan", OK("Sesuai")],
             ["Fakta 4: sheet ganda", "Satu sheet bulan disalin", f"{I(at.loc['duplicate_sheet', 'n'])} sheet ganda di layout 1, dibuang parser", OK("Sesuai")],
             ["Fakta 5: sel kotor 2 sampai 3%", "Angka teks, desimal koma, '-', sel kosong, spasi berlebih di nama stasiun",
              f"{I(n_planted_eff - 3)} sel kotor nyata ({P((n_planted_eff - 3) / N_CELLS, 1)} dari nilai): n/a, '-', kali 10, satuan. Tanpa desimal koma; sel kosong ({I(len(peff[peff.problem == 'blank']))}) tidak benar-benar kosong; nama stasiun tidak seragam di layout 5", NO("Berubah")],
             ["Tabel fact_output_tidy", "date, shift, station, model, metric, value, source_file, source_cell", "Ditambah slot, quality, template, source_sheet; <code>model</code> menjadi <code>size</code>", PART("Sesuai + penyesuaian")],
             ["Tabel anomaly_log", "source_file, sheet, cell, issue_type, raw_value, action", "Ditambah template, fix_method, parsed_value", PART("Sesuai + penyesuaian")],
             ["Tabel reconciliation", "source_file, sheet, block, metric, report_total, parsed_total, diff, status", "Ditambah kind, report_cell, hasil sesudah pemulihan (<code>*_final</code>), resolution", PART("Sesuai + penyesuaian")],
             ["Tabel method_benchmark", "method, scenario, build_minutes, run_seconds, result_match, fix_minutes", "Kolom ada, tetapi <code>build_minutes</code> dan <code>fix_minutes</code> kosong (tidak diukur); ditambah ukuran pekerjaan", PART("Sebagian")],
             ["Lisensi", "Tidak memakai dataset publik atau data perusahaan", "Tidak berlaku (data buatan sendiri)", OK("Tidak berlaku")]]))
rp4 = mk('<div class="card"><p><b>Jawaban singkat:</b> semua tools utama dipakai. Perbedaannya: Power Query hanya ditulis (kode M), tidak dijalankan; rumus Excel dihitung dengan LibreOffice, bukan Excel; dashboard belum di-deploy; '
         'dan ditambah LibreOffice, Jupyter, dan matplotlib untuk one-sheet.</p></div>',
         table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
             ["Python (openpyxl, pandas)", "openpyxl membaca isi sel dan merged cell; pandas merapikan dan unpivot", f"Paket parser (<code>parser/</code>) dengan empat jenis pembaca; {I(npy)} skrip dan modul, {I(loc)} baris", OK("Sesuai")],
             ["YAML (config template)", "Satu config per template: sel jangkar, header, blok data, subtotal", f"{I(ncfg)} file config template (6 layout + 2 revisi bulan ke-4), kamus nama <code>lookup.yaml</code>, aturan <code>parser_rules.yaml</code>", PART("Sesuai + penyesuaian")],
             ["pytest", "Tes tiap template dan skenario perubahan layout", f"{I(ntest_files)} berkas tes, {I(n_tests)} tes lulus: pembersihan, rekonsiliasi, template, akurasi, skenario, repo", OK("Sesuai")],
             ["DuckDB + SQL", "Empat tabel, pivot, rekonsiliasi, tren; SQL sebagai metode pembanding", f"<code>parsed.duckdb</code> (tiga tabel + kunci jawaban, bukan empat), {I(nsql)} file SQL; cek silang dengan pandas {I(ok_cx)} dari {I(len(cx))} cocok", PART("Sesuai + penyesuaian")],
             ["Excel (rumus + tabel pemetaan)", "Rumus INDEX/MATCH dan tabel pemetaan sel; juga cek silang", "<code>methods/excel_formula.xlsx</code>: sheet Laporan, Pemetaan, Tidy dengan INDEX/MATCH; dihitung ulang dengan LibreOffice headless, bukan Excel", PART("Sebagian")],
             ["Power Query", "Gabung file dari folder, buang subtotal, unpivot lewat menu", "Kode M ditulis (<code>L1_v1.pq</code>, <code>combine_folder.pq</code>) tetapi tidak dijalankan karena tidak ada Excel; tidak ada <code>power_query.xlsx</code>", PART("Sebagian")],
             ["Streamlit + Plotly", "Dashboard tiga halaman, dipublikasikan lewat link", "<code>streamlit/app.py</code> dengan tiga halaman (Data Produksi, Kualitas Parsing, Perbandingan Metode); diuji lokal dengan <code>AppTest</code>; belum di-deploy", PART("Sebagian")],
             ["GitHub", "Kode, config, laporan contoh, README; tes bisa dijalankan tiap perubahan", "Struktur, README, enam laporan contoh, dan tes siap; di branch <code>project-25-build</code>, belum digabung ke <code>main</code>", PART("Sebagian")],
             ["Markdown", "README dan panduan menambah template", "<code>README.md</code> dan lima dokumen di <code>project/docs/</code> (termasuk <code>add_new_template.md</code>)", OK("Sesuai")],
             ["LibreOffice, Jupyter, matplotlib", "Tidak disebut", "LibreOffice menghitung rumus Excel; <code>analysis.ipynb</code> dieksekusi tanpa error; matplotlib membuat one-sheet", PART("Tambahan")]]))
steps = [("1", "Mendata masalah layout", "<code>02_layout_taxonomy.py</code>, <code>docs/layout_taxonomy.md</code>", OK("Sesuai"), f"{I(len(tx))} jenis masalah pada {I(prof['layout'])} layout."),
         ("2", "Menetapkan skema tidy dan aturan rekonsiliasi", "<code>docs/data_dictionary.md</code>, <code>docs/metrics.md</code>", PART("Sesuai + penyesuaian"), "Dua metrik dan kolom slot; toleransi selisih nol; aturan pemulihan sel ditambahkan."),
         ("3", "Membuat data output yang rapi", "<code>01_generate_reports.py</code>, <code>truth_fact_output_tidy.csv</code>", OK("Sesuai"), "Generator v1 apa adanya."),
         ("4", "Membuat laporan Excel berantakan", "<code>project/data/sim/reports/</code>", PART("Sesuai + penyesuaian"), "Sel kosong tidak efektif; desimal koma tidak ditanam."),
         ("5", "Menulis config per template", "<code>project/config/</code>", PART("Sesuai + penyesuaian"), f"{I(ncfg)} file config (dua revisi bulan ke-4) ditambah kamus nama dan aturan umum."),
         ("6", "Membangun parser", "<code>parser/</code>, <code>03_parse_all.py</code>", OK("Sesuai"), "Berhenti bila template atau label tidak dikenal."),
         ("7", "Rekonsiliasi dan log anomali", "<code>parser/reconcile.py</code>, <code>06_anomalies.py</code>, <code>07_reconciliation_summary.py</code>", PART("Sesuai + tambahan"), "Ditambah pemulihan sel lewat subtotal dan penandaan angka kali 10."),
         ("8", "Tes otomatis dan uji perubahan layout", "<code>project/tests/</code>, <code>08_robustness.py</code>, <code>12_validation.py</code>", PART("Sesuai + penyesuaian"), "Sembilan skenario perubahan layout (dua nyata, tujuh sintetis)."),
         ("9", "Mengerjakan tiga metode pembanding", "<code>09_methods_benchmark.py</code>, <code>methods/</code>", PART("Sebagian"), "Power Query tidak dijalankan; waktu manusia tidak diukur."),
         ("10", "Analisis tabel tidy dan hitung dampak", "<code>10_pivot_trends.py</code>, <code>11_impact.py</code>, <code>13_crosscheck_sql.py</code>", PART("Sebagian"), "Pembanding rekap copy-paste (Q14) tidak dilakukan."),
         ("11", "Membuat dashboard", "<code>streamlit/app.py</code>, <code>14_build_dashboard_data.py</code>", PART("Sebagian"), "Belum di-deploy."),
         ("12", "Menulis README, rekomendasi, dan finalisasi", "<code>README.md</code>, <code>17_build_docs.py</code>, halaman ini", PART("Sebagian"), "Finalisasi menunggu merge ke main dan hub.")]
rp5 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> {len(steps)} langkah dijalankan sesuai urutan. {sum(1 for s in steps if s[3].count("Sebagian") and "Sesuai" not in s[3])} langkah sebagian (metode pembanding, analisis dampak, dashboard, finalisasi); langkah lain sesuai dengan beberapa penyesuaian.</p></div>',
         table(["Langkah", "Rancangan", "Realisasi", "Verdict", "Catatan"], [list(s) for s in steps]),
         '<div class="card"><h4>Penyesuaian dan improvisasi yang tidak ada di rancangan</h4><ul class="tight">',
         f'<li>Parser berhenti, bukan menebak: bila isi sel tidak cocok dengan satu pun template atau label tidak dikenal, hasilnya pesan kesalahan. Pada {I(len(rob))} skenario perubahan layout tidak ada angka salah yang ditulis.</li>',
         f'<li>Pemulihan sel lewat subtotal: sel kosong, "-", "n/a", atau berlebih 10 kali dihitung dari subtotal laporan bila hanya satu sel yang tidak pasti ({I(n_recov)} sel). Selain itu sel ditandai, tidak diisi.</li>',
         f'<li>Hasil dinilai terhadap kunci jawaban dengan status kualitas (ok, fixed, flagged, missing), sehingga akurasi nilai tepercaya ({P(1, 0)}) dan nilai ditandai ({I(n_bad)}) dilaporkan terpisah.</li>',
         f'<li>Kelemahan generator v1 ditemukan saat validasi: jenis sel kosong ({I(len(peff[peff.problem == "blank"]))} sel) tidak efektif. Generator tidak diubah agar data tetap identik dengan yang tercatat di DataCenter.</li></ul></div>',
         '<div class="card"><h4>Perubahan nama dan lokasi file terhadap rancangan</h4>',
         table(["Rancangan", "Realisasi"], [[f"<code>{a}</code>", ", ".join(f"<code>{x}</code>" for x in b.split(", "))] for a, b in [
             ("scripts/generate_reports.py", "project/code/1-data-preparation/python/01_generate_reports.py"),
             ("data/ground_truth/*.csv", "project/data/sim/truth_fact_output_tidy.csv, project/data/sim/ground_truth_dirty_cells.csv"),
             ("data/reports/*.xlsx", "project/data/sim/reports/*.xlsx, project/data/samples/*.xlsx"),
             ("data/planted_facts.json", "project/data/sim/ground_truth.json"),
             ("configs/*.yaml", "project/config/templates/*.yaml, project/config/lookup.yaml, project/config/parser_rules.yaml"),
             ("parser/", "project/code/1-data-preparation/python/parser/"),
             ("sql/", "project/code/1-data-preparation/sql/, project/code/2-analysis/sql/"),
             ("methods/power_query.xlsx", "project/methods/power_query/L1_v1.pq, project/methods/power_query/combine_folder.pq"),
             ("outputs/method_benchmark.csv", "project/results/2-analysis/method_benchmark.csv"),
             ("notebooks/analysis.ipynb", "project/results/3-presentation/analysis.ipynb"),
             ("dashboard/app.py", "project/code/3-presentation/streamlit/app.py"),
             ("outputs/method_onesheet.pdf / .png", "project/results/3-presentation/method_onesheet.pdf, project/results/3-presentation/method_onesheet.png")]]) + '</div>')

# ---------------------------------------------------------------- 6. output
chk_ = lambda rel: (REPO / rel).exists()
outs = [("Dashboard interaktif", "Utama", PART("Sebagian"), "<code>streamlit/app.py</code>, tiga halaman, diuji lokal dengan AppTest. Link publik belum ada"),
        ("One-sheet perbandingan metode", "Utama", OK("Tercapai"), "<code>method_onesheet.pdf</code> dan <code>.png</code>; uji ke pembaca awam (kurang dari 1 menit) belum dilakukan"),
        ("Parser & config template", "Utama", OK("Tercapai"), f"<code>parser/</code>, {I(ncfg)} config template, {I(n_tests)} tes, panduan <code>docs/add_new_template.md</code>"),
        ("Database & query SQL", "Utama", PART("Sebagian"), f"<code>parsed.duckdb</code> dengan tiga tabel hasil ({I(nsql)} file SQL); <code>method_benchmark</code> berupa CSV, bukan tabel database"),
        ("Generator laporan simulasi", "Utama", OK("Tercapai"), "<code>01_generate_reports.py</code> dan <code>ground_truth.json</code>; hasil identik tiap jalan (SHA-256)"),
        ("Workbook metode pembanding", "Utama", PART("Sebagian"), "<code>excel_formula.xlsx</code> ada; versi Power Query hanya kode M, tidak ada workbook"),
        ("Laporan temuan & rekomendasi", "Utama", OK("Tercapai"), "<code>README.md</code> dan halaman ini; angka dampak berlabel estimated dan simulated"),
        ("Repositori GitHub", "Utama", PART("Sebagian"), f"Kode, {I(n_tests)} tes, dan petunjuk menjalankan siap; di branch <code>project-25-build</code>, belum digabung ke <code>main</code>"),
        ("Slide presentasi", "Opsional", NO("Tidak dibuat"), "Opsional, tidak dibuat")]
nU = [o for o in outs if o[1] == "Utama"]
cnt = lambda s: sum(1 for o in nU if s in o[2])
PRIV = ("project/data/sim/ground_truth", "project/data/sim/reports", "project/parsed.duckdb")
docs = [("docs/layout_taxonomy.md", "Enam jenis masalah layout beserta contoh", "project/docs/layout_taxonomy.md"), ("docs/data_dictionary.md", "Kamus data dan aturan rekonsiliasi", "project/docs/data_dictionary.md"),
        ("scripts/generate_reports.py", "Pembuat data rapi dan laporan berantakan", "project/code/1-data-preparation/python/01_generate_reports.py"),
        ("data/ground_truth/*.csv", "Data rapi sebagai kunci jawaban (tidak di-commit)", "project/data/sim/ground_truth"),
        ("data/reports/*.xlsx", "Laporan simulasi (hanya enam contoh di-commit)", "project/data/samples/laporan_G1_2026-03.xlsx"),
        ("data/planted_facts.json", "Catatan fakta yang ditanam", "project/data/sim/ground_truth"), ("configs/*.yaml", "Config per template", "project/config/templates/L1_v1.yaml"),
        ("data/README.md", "Cara membuat ulang data", "project/data/README.md"), ("parser/", "Kode parser, rekonsiliasi, log anomali", "project/code/1-data-preparation/python/parser/pipeline.py"),
        ("tests/", "Tes per template dan skenario", "project/tests/test_scenarios.py"), ("parsed.duckdb", "Database (tidak di-commit)", "project/parsed.duckdb"),
        ("sql/", "Query pivot, rekonsiliasi, metode SQL", "project/code/2-analysis/sql/02_kpi.sql"), ("methods/excel_formula.xlsx", "Metode rumus Excel", "project/methods/excel_formula.xlsx"),
        ("methods/power_query.xlsx", "Metode Power Query", "project/methods/power_query.xlsx"), ("outputs/method_benchmark.csv", "Perbandingan empat metode", "project/results/2-analysis/method_benchmark.csv"),
        ("notebooks/analysis.ipynb", "Analisis Q1 sampai Q15", "project/results/3-presentation/analysis.ipynb"), ("dashboard/app.py", "Dashboard Streamlit", "project/code/3-presentation/streamlit/app.py"),
        ("requirements.txt", "Paket Python", "project/requirements.txt"), ("outputs/method_onesheet.pdf / .png", "One-sheet perbandingan metode", "project/results/3-presentation/method_onesheet.pdf"),
        ("docs/add_new_template.md", "Panduan menambah template", "project/docs/add_new_template.md"), ("README.md", "Laporan temuan", "README.md"), ("index.html", "Pengalihan ke design-and-report/", "index.html"),
        ("slides/presentation.pdf", "Slide", "slides/presentation.pdf")]
stat_doc = lambda rel: PART("Tidak di-commit") if rel in PRIV else (OK("Ada") if chk_(rel) else NO("Belum ada"))
rp6 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> {I(cnt("Tercapai"))} dari {I(len(nU))} output Utama tercapai penuh dan {I(cnt("Sebagian"))} sebagian (dashboard ter-deploy, workbook Power Query, tabel benchmark di database, dan merge ke main belum ada). '
         f'Slide Opsional tidak dibuat.</p></div>',
         table(["Output", "Label", "Status", "Bukti"], [[f"<b>{a}</b>", b, c, d] for a, b, c, d in outs]),
         '<div class="card"><h4>Daftar dokumen pada rancangan vs repositori</h4>',
         table(["Dokumen (rancangan)", "Isi", "Lokasi sekarang", "Status"], [[f"<code>{a}</code>", b, f"<code>{c}</code>", stat_doc(c) if c in PRIV else stat_doc(c)] for a, b, c in docs]),
         '<p>Laporan simulasi lengkap, kunci jawaban, tabel tidy lengkap, dan database tidak di-commit karena bisa dibuat ulang dari skrip (hasil identik). Yang di-commit: enam laporan contoh, config, kode, tes, dokumen, dan CSV hasil. File yang ditandai "Belum ada" memang tidak dibuat atau berganti bentuk (lihat bagian 4 dan 5).</p></div>')

# ---------------------------------------------------------------- 7. kesimpulan
crit = [("1. Kesepuluh pertanyaan Utama terjawab dengan angka dari data", OK("Tercapai"), "Q1, Q3, Q4, Q5, Q6, Q8, Q9, Q11, Q13, Q15 terjawab (bagian 2); beberapa dengan catatan"),
        ("2. Semua nilai hasil parser sama dengan data rapi asli, kecuali sel di log anomali beserta alasannya", OK("Tercapai"),
         f"{I(n_okfix)} dari {I(n_okfix)} nilai ok atau fixed sama persis; {I(n_bad)} nilai ditandai di log; {I(0)} nilai salah lolos"),
        ("3. Rekonsiliasi cocok di semua blok, kecuali dua subtotal salah yang ditanam, dan keduanya tertangkap", PART("Sebagian"),
         f"Dua subtotal salah tertangkap; tetapi {I(n_sub - m_fin)} dari {I(n_sub)} subtotal tidak cocok ({I(n_sub - m_fin - 2)} karena sel yang tidak bisa dipastikan)"),
        ("4. Perubahan layout bulan ke-4 hanya dengan mengubah config, dan semua tes lulus", OK("Tercapai"), f"{I(rob.config_lines_changed.iloc[0])} baris config, {I(0)} baris Python; {I(n_tests)} tes lulus"),
        ("5. Orang awam membaca one-sheet dan menyebut metode yang cocok kurang dari 1 menit", PART("Sebagian"), "One-sheet ada; belum diuji ke pembaca awam"),
        ("6. Checklist standar (pertanyaan bisnis, cleaning, SQL, dashboard ter-deploy, README)", PART("Sebagian"), "Semua ada kecuali dashboard ter-deploy")]
ncr = sum(1 for c in crit if ">Tercapai<" in c[1])
rp7 = mk(
    '<div class="card"><h4>7.1 Hasil analisis: jawaban atas pertanyaan utama</h4>',
    '<p><i>Bagaimana mengubah laporan Excel manual berlayout bebas menjadi tabel tidy tanpa copy-paste, membuktikan bahwa hasilnya benar, dan memilih metode yang paling cocok untuk tiap situasi?</i></p><ul class="tight">',
    f'<li><b>Tanpa copy-paste:</b> satu parser berbasis config membaca {I(N_FILES)} file dengan {I(prof["layout"])} layout menjadi {I(N_CELLS)} nilai dalam {D(parser_s36, 1)} detik. Template dikenali dari isi sel; bila tidak dikenal parser berhenti.</li>',
    f'<li><b>Hasilnya terbukti benar:</b> {I(n_okfix)} dari {I(n_okfix)} nilai tepercaya sama dengan data rapi asli; {I(n_bad)} nilai ({P(n_bad / N_CELLS, 1)}) ditandai di log. Subtotal cocok {P(m_raw / n_sub, 1)} sebelum dan {P(m_fin / n_sub, 1)} sesudah pemulihan sel, dan kedua subtotal salah ketik ditemukan.</li>',
    f'<li><b>Tahan perubahan layout:</b> {I(len(rob))} skenario, tidak ada angka salah yang ditulis; config baru {I(rob.config_lines_changed.min())} sampai {I(rob.config_lines_changed.max())} baris, kode Python tidak diubah.</li>',
    f'<li><b>Metode menurut situasi:</b> rumus Excel untuk end user (satu sampai dua file, sekitar {D(sec_(XL, S1), 1)} detik per file), Power Query untuk tim non-programmer (belum diuji), parser Python untuk banyak layout dan bukti kebenaran, SQL bila data sudah di database. Tidak ada metode yang menang di semua kriteria.</li>',
    f'<li><b>Yang tidak terpecahkan:</b> pada layout tanpa subtotal (3, 4, 6), sel kotor hanya bisa ditandai ({I(n_flag + n_miss)} nilai ditandai di seluruh data), tidak dipulihkan.</li></ul></div>',
    '<div class="card"><h4>7.2 Impact</h4><ul class="tight">',
    f'<li><b>Nilai praktis (estimated, simulated):</b> sekitar {D(saved_h, 0)} jam kerja per tahun bila {I(reports_mo)} laporan per bulan memakan {I(manual_min)} menit copy-paste; parser memprosesnya dalam {D(parser_s6, 1)} detik per bulan.</li>',
    f'<li><b>Nilai analitis:</b> rekonsiliasi menunjukkan hal yang tidak terlihat di copy-paste: {I(errs_total)} sel atau subtotal salah di laporan tertangkap semuanya, termasuk dua subtotal yang diketik salah.</li>',
    '<li><b>Nilai portofolio:</b> tabel tidy dengan alamat sel asal bisa menjadi sumber data Project 3 dan 27; versi anonim laporan kerja memakai pipeline Project 24.</li>',
    '<li><b>Belum terukur:</b> waktu pembuatan dan perbaikan oleh manusia tiap metode, jumlah salah salin pada rekap copy-paste, dan kinerja pada laporan kerja yang sebenarnya.</li></ul></div>')
rp7 += ('<div class="card"><h4>7.3 Success criteria</h4>' + table(["Kriteria (Design Project, bagian 8)", "Status", "Bukti"], [[a, b, c] for a, b, c in crit])
        + f'<p><b>Hasil:</b> {I(ncr)} dari {I(len(crit))} kriteria tercapai, {I(len(crit) - ncr)} sebagian.</p></div>')
rp7 += mk('<div class="card"><h4>7.4 Rekomendasi</h4><ul class="tight">',
          '<li>Pakai parser berbasis config bila laporan banyak dan layoutnya beragam; simpan satu file config per versi layout, dan jangan menebak layout yang tidak dikenal.</li>',
          '<li>Jalankan rekonsiliasi dengan subtotal pada setiap file dan tangani sel yang ditandai secara manual; jangan mengisi angka yang tidak bisa dibuktikan.</li>',
          '<li>Minta pembuat laporan menyertakan subtotal di setiap blok: tanpa subtotal sel kotor hanya bisa ditandai, tidak dipulihkan.</li>',
          '<li>Untuk satu atau dua file di lini produksi, rumus Excel cukup, tetapi cek hasilnya karena perubahan layout bisa menghilangkan data tanpa peringatan.</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.5 Saran perbaikan</h4><ul class="tight">',
          '<li>Jalankan Power Query di Excel yang sebenarnya dan ukur waktu pembuatan serta perbaikan semua metode dengan stopwatch pada beberapa orang.</li>',
          '<li>Lakukan pembanding rekap copy-paste manual pada sampel file untuk menjawab Q14, dan uji one-sheet ke pembaca awam.</li>',
          '<li>Perbaiki generator (sel kosong benar-benar kosong, tambah desimal koma dan spasi di nama stasiun) lalu catat sidik jari baru di DataCenter.</li>',
          '<li>Deploy dashboard ke Streamlit Community Cloud dan uji parser pada satu laporan kerja yang sudah dianonimkan (pipeline Project 24).</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.6 Batasan</h4><ul class="tight">',
          '<li>Semua temuan berasal dari data simulasi yang lebih rapi dari laporan nyata; hasil membuktikan metode, bukan kondisi pabrik. Data simulasi.</li>',
          '<li>Parser hanya seandal config-nya. Layout yang berubah total tetap butuh config baru, dan struktur di luar empat jenis pembaca butuh kode baru.</li>',
          f'<li>Rekonsiliasi hanya pada layout dengan subtotal (layout 1 dan 2); layout lain hanya dicek lewat aturan sel dan kunci jawaban. {I(n_sub - m_fin)} subtotal tetap tidak cocok.</li>',
          f'<li>Generator v1: sel kosong ({I(len(peff[peff.problem == "blank"]))} sel) tidak benar-benar kosong, desimal koma tidak ditanam, dan layout 5 tidak dikotori. Generator sengaja tidak diubah agar sidik jari data tetap sama.</li>',
          '<li>Power Query hanya ditulis, tidak dijalankan; rumus Excel dihitung dengan LibreOffice. Waktu pembuatan dan perbaikan oleh manusia tidak diukur, dan pembanding copy-paste manual (Q14) tidak dilakukan. Menit copy-paste dan jumlah laporan per bulan adalah asumsi.</li>',
          '<li>Dashboard belum di-deploy, uji one-sheet ke pembaca awam belum dilakukan, dan slide (Opsional) tidak dibuat.</li>',
          '<li>Lisensi dataset tidak berlaku (data buatan sendiri).</li></ul></div>')

evq = [("1", "rp1", "Data yang didapat", OK("Didapat"), f"{I(N_FILES)} file, {I(N_CELLS)} nilai tidy, {I(n_anom)} baris anomali, {I(n_sub)} subtotal dicocokkan"),
       ("2", "rp2", "Business question terjawab?", OK(f"{len(QT)} dari {len(QT)}"), f"Semua terjawab ({npr['Utama']} Utama, {npr['Pendukung']} Pendukung, {npr['Tambahan']} Tambahan); {nw} dengan catatan ({wtxt})"),
       ("3", "rp3", "Dataset sesuai?", PART("Sesuai + penyesuaian"), "Ukuran sesuai; dua metrik, dua layout berubah di bulan ke-4, sel kosong tidak efektif"),
       ("4", "rp4", "Tools sesuai?", PART("Sesuai + penyesuaian"), "Power Query tidak dijalankan; Excel via LibreOffice; dashboard belum di-deploy"),
       ("5", "rp5", "Alur sesuai?", PART("Sesuai + penyesuaian"), f"{len(steps)} langkah dijalankan; metode pembanding, dampak, dashboard, finalisasi sebagian"),
       ("6", "rp6", "Output tercapai?", PART(f"{cnt('Tercapai')} penuh, {cnt('Sebagian')} sebagian"), f"{cnt('Tercapai')} dari {len(nU)} output Utama penuh"),
       ("7", "rp7", "Kesimpulan", OK("Tersedia"), f"Hasil analisis, Impact, {len(crit)} kriteria sukses, rekomendasi, saran perbaikan, batasan")]
evq_html = '<div class="scroll"><table class="evq"><tr><th>No</th><th>Pertanyaan evaluasi</th><th>Verdict</th><th>Ringkasan</th></tr>' + "".join(
    f'<tr><td><span class="en">{n}</span></td><td><a href="#{h}">{t}</a></td><td>{v}</td><td>{s}</td></tr>' for n, h, t, v, s in evq) + "</table></div>"
H = lambda i, t, sm, body: f'\n<h2 id="rp{i}">{i}. {t}<small>{sm}</small></h2>\n{body}\n'
report = mk(
    '<div class="pane" id="report" data-tab="report" hidden>\n',
    f'<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4><p>Halaman ini disusun sebagai 7 jawaban atas pertanyaan evaluasi. Tabel dan grafik dibuat otomatis dari hasil skrip Python dan query SQL (DuckDB) pada laporan Excel simulasi. '
    f'Hasil SQL dicek silang dengan pandas ({I(ok_cx)} dari {I(len(cx))} pemeriksaan cocok). Angka pada teks diaudit terhadap file di <code>project/results/</code>: @@AUDIT@@ angka diperiksa tanpa selisih. '
    'Semua angka bersumber dari data simulasi buatan sendiri dan menguji metode, bukan kondisi pabrik. Rancangan lengkap ada di tab <a href="#design">Design Project</a>.</p></div>\n',
    evq_html,
    H(1, "Data yang berhasil didapatkan", "Isi data mentah, tabel di database, dan data hasil analisis", rp1),
    H(2, "Apakah business question terjawab?", f"{len(QT)} pertanyaan pada Design Project, dijawab dengan data", rp2),
    H(3, "Apakah dataset sesuai dengan Design Project?", "Perbandingan rancangan dengan realisasi", rp3),
    H(4, "Apakah tools yang digunakan sesuai?", "Perbandingan rancangan dengan eksekusi", rp4),
    H(5, "Apakah alur pengerjaan sesuai dengan Design Project?", f"{len(steps)} langkah rancangan vs yang dijalankan", rp5),
    H(6, "Apakah project output tercapai?", "Output pada Design Project, bagian 7", rp6),
    H(7, "Kesimpulan", "Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan", rp7),
    '</div>\n')

# ---------------------------------------------------------------- audit angka
STATIC = {str(i) for i in range(0, 32)} | {f"{i:02d}" for i in range(0, 60)} | {"100", "60", "80", "95", "75", "50", "1,5", "2,0", "2026", "25", "20", "9", "7", "8", "10", "13", "14", "330", "600", "1.000", "120", "27.000", "36", "25260302", "496", "39", "28"}
STATIC |= {f"{a}.{b}" for a in range(1, 10) for b in range(1, 10)}
n_tok, bad = audit(report, STATIC)
manual = [("seluruh CSV hasil terdokumentasi", not miss), ("nilai ok atau fixed semua benar, tidak ada salah lolos", n_bad == N_CELLS - n_okfix and int(accv[13]) == 0),
          ("flagged semuanya bernilai 10 kali kunci jawaban", int(accv[10]) == n_flag), ("subtotal cocok sesudah pemulihan 4.164 dari 4.200", m_fin == 4164 and n_sub == 4200),
          ("dua subtotal salah ketik ditemukan", rtypo.shape[0] == 2), ("anomali tercatat sama dengan baris log", n_anom == len(pd.read_csv(result("anomaly_log.csv")))),
          ("semua kejadian nyata terdeteksi, recall 100%", bool((vplant.recall.dropna() == 1).all())), ("semua uji validasi lulus", bool((vchk.result == "lulus").all())),
          ("cek silang SQL vs pandas cocok", bool(cx.match.all())), ("config lama berhenti dengan aman pada semua skenario", bool(rob.old_stopped_safely.all())),
          ("tidak ada baris Python diubah pada skenario perubahan layout", bool((rob.python_lines_changed == 0).all())), ("catatan hanya Q7, Q8, Q9, Q10, Q11, Q13, Q14, Q15", WARN == {7, 8, 9, 10, 11, 13, 14, 15}),
          ("jumlah pertanyaan 15 (10 Utama, 4 Pendukung, 1 Tambahan)", len(QT) == 15 and npr == {"Utama": 10, "Pendukung": 4, "Tambahan": 1}), ("langkah rancangan = 12", len(steps) == 12),
          ("jumlah pertanyaan unik pada bagian 2 = 15", qn_all == list(range(1, 16))), ("pivot layout 2 sama persis, layout 1 tidak", bool(pvr2.same_after_repair.all() and not pvr1.same_after_repair.any())),
          ("daftar stasiun realisasi sesuai CSV", sorted(r_st) == sorted(st_rate.station))]
assert all(v for _, v in manual), [k_ for k_, v in manual if not v]
if bad:
    print("TOKEN TIDAK TERDAFTAR:", bad)
    sys.exit(1)
report = report.replace("@@AUDIT@@", I(n_tok) + f" (ditambah {I(len(manual))} klaim manual)")

# ---------------------------------------------------------------- rakit halaman
v1 = (HERE / "page_v1.html").read_text(encoding="utf-8")
a = v1.index('<div class="pane" id="report"')
b = v1.index("</main>")
design_pane = v1[v1.index('<div class="pane" id="design"'):a]
nav_old = re.search(r'<nav aria-label="Project navigation">.*?</nav>', v1, re.S).group(0)
btn = lambda t: re.search(rf'<button type="button" class="tab[^"]*" data-t="{t}".*?</button>', nav_old, re.S).group(0)
design_links = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_old, re.S).group(0)
report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in
               enumerate(["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + "</div>")
nav_new = f'<nav aria-label="Project navigation">{btn("design")}{btn("report")}{design_links}{report_links}</nav>'
css = (HERE / "report.css").read_text(encoding="utf-8")
html = v1[:a] + report + v1[b:]
html = html.replace(nav_old, nav_new)
i = html.rindex("</style>")
html = html[:i] + css + html[i:]
out = REPO / "design-and-report" / "index.html"
out.write_text(html, encoding="utf-8")
assert design_pane == html[html.index('<div class="pane" id="design"'):html.index('<div class="pane" id="report"')], "pane Design berubah"
print(f"index.html {len(html) / 1024:.0f} KB; {n_tok} angka diaudit; {len(manual)} klaim manual; pane Design identik; {n_tests} tes lulus")
