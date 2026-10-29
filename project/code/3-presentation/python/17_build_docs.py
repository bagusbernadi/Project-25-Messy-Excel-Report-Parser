"""Tahap 3 / langkah 17: buat README.md (root repo) dan docs/*.md; semua angka dibaca dari CSV hasil."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

R = lambda n: pd.read_csv(C.result(n))
f = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
n = lambda v: f"{int(round(v)):,}".replace(",", ".")
pc = lambda v, d=1: f(v * 100, d) + "%"
REPO = C.ROOT.parent

prof = R("data_profile.csv").set_index("item")["value"]
tax, acc = R("layout_taxonomy.csv"), R("accuracy_summary.csv").set_index("item")["value"]
abl, rs, anom_t, td = R("accuracy_by_layout.csv"), R("reconciliation_summary.csv"), R("anomaly_by_type.csv"), R("template_difficulty.csv")
rob, cfgc, bench, sit = R("robustness_scenarios.csv"), R("config_changes.csv"), R("method_benchmark.csv"), R("method_situations.csv")
imp, errs, vp, vc = R("impact_time.csv").set_index("item")["value"], R("errors_caught.csv").set_index("item")["value"], R("validation_planted.csv"), R("validation_checks.csv")
cx = R("crosscheck_sql.csv")
gt = json.loads(C.GROUND_TRUTH.read_text(encoding="utf-8"))
s1 = bench[bench.scenario.str.startswith("S1")].set_index("method")
s3 = bench[bench.scenario.str.startswith("S3")].set_index("method").loc["Python (parser)"]
s4 = bench[bench.scenario.str.startswith("S4")].set_index("method")
pe = R('planted_cells_effective.csv')
n_dirty_eff = int(pe[pe.problem.isin(['text_na', 'dash', 'x10', 'unit_text']) & pe.effective].shape[0])
n_blank = int((pe.problem == 'blank').sum())
reconsum = rs.groupby("kind")[["subtotals", "match_raw", "match_final"]].sum()
tot_sub, raw_ok, fin_ok = int(rs.subtotals.sum()), int(rs.match_raw.sum()), int(rs.match_final.sum())

md = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 25: Messy Excel Report Parser

**Status: selesai di branch `project-25-build` (menunggu review sebelum digabung ke `main`).**

Halaman rancangan dan Report: https://bagusbernadi.github.io/project-25-messy-excel-report-parser/

| | |
|---|---|
| Kategori | Manufaktur (pabrik minuman kemasan botol) |
| Tingkat | Menengah–lanjut |
| Data | Simulasi: {n(prof['file laporan'])} laporan Excel berantakan (6 layout x 6 bulan) dibuat dari data rapi; kunci jawaban diketahui |
| Tools | Python (openpyxl, pandas, pytest), YAML, DuckDB + SQL, rumus Excel (dihitung LibreOffice), Power Query (kode M, belum dijalankan), Streamlit + Plotly |

## 1. Problem

Bagaimana mengubah laporan Excel manual berlayout bebas menjadi tabel tidy tanpa copy-paste, membuktikan bahwa hasilnya benar, dan memilih metode yang paling cocok untuk tiap situasi? Dipecah menjadi 15 pertanyaan (10 Utama); jawabannya ada di tab Report pada halaman project.

## 2. Data

- Data simulasi dengan seed tetap (`project/code/1-data-preparation/python/01_generate_reports.py`, v1): data rapi {n(gt['tidy_rows'])} baris (150 hari x 2 shift x 3 slot x 10 stasiun x 3 ukuran) dituang ke {n(gt['n_files'])} file Excel, 6 template layout.
- Fakta yang ditanam: 6 layout, perubahan layout pada layout 1 dan 3 di bulan ke-4, 2 subtotal salah ketik, 1 sheet ganda, dan sel angka kotor. Dari {n(gt['n_problem_cells'])} sel yang dicatat sebagai bermasalah, {n(n_blank)} berjenis 'blank' ternyata tidak benar-benar dikosongkan oleh pembuat data (nilai tetap utuh), sehingga yang nyata adalah {n(n_dirty_eff)} sel angka kotor (salah, hilang, atau berformat teks), 2 subtotal salah, dan 1 sheet ganda.
- Laporan hasil simulasi tidak di-commit (dibuat ulang dalam sekitar satu menit); 6 laporan contoh ada di `project/data/samples/`. Detail kolom tabel hasil: `project/docs/data_dictionary.md`.

## 3. Analysis

- Parser berbasis config: {len(list(C.TEMPLATES_DIR.glob('*.yaml')))} file config YAML untuk 6 layout (termasuk 2 revisi bulan ke-4), 4 jenis pembaca, kamus nama di `project/config/lookup.yaml`. Template dikenali dari isi sel; bila tidak ada yang cocok parser berhenti, tidak menebak.
- Hasil: {n(acc['sel nilai pada kunci jawaban'])} nilai dalam tabel tidy. {n(acc['sel ok atau fixed yang sama persis'])} dari {n(acc['sel berstatus ok atau fixed'])} nilai berstatus ok atau fixed sama persis dengan data rapi asli ({n(acc['sel salah yang lolos tanpa tanda (ok atau fixed tetapi beda dari kunci)'])} salah lolos); {n(acc['sel bermasalah di log (flagged + missing)'])} nilai ditandai (flagged atau missing) di log anomali. Persen sama persis seluruhnya: {pc(acc['persen sama persis'])}.
- Rekonsiliasi: {n(tot_sub)} subtotal laporan (layout 1 dan 2). Sebelum pemulihan {n(raw_ok)} cocok ({pc(raw_ok / tot_sub)}); sesudah pemulihan {n(fin_ok)} cocok ({pc(fin_ok / tot_sub)}). Sisanya adalah sel yang tidak bisa dipastikan dan 2 subtotal salah ketik yang ditemukan.
- Anomali di log: {n(anom_t.n.sum())} baris; jenis terbanyak {anom_t.issue_type.iloc[0]} ({n(anom_t.n.iloc[0])}). {n(errs.iloc[6])} sel dipulihkan tepat lewat subtotal.
- Perubahan layout: bulan ke-4 layout 1 dan 3 hanya butuh {n(cfgc.lines_changed_excluding_id_description.iloc[0])} baris config, tanpa mengubah kode Python; dengan config lama parser berhenti. Template baru dari nol rata-rata {n(cfgc.lines_in_new_file.iloc[2])} baris config.
- Empat metode pada file yang sama: rumus Excel {f(s1.loc['Rumus Excel'].run_seconds, 2)} detik, SQL {f(s1.loc['SQL (DuckDB)'].run_seconds, 2)} detik, parser Python {f(s1.loc['Python (parser)'].run_seconds, 2)} detik per file; Power Query belum dijalankan. Untuk 36 file parser butuh {f(s3.run_seconds, 1)} detik.
- Pemeriksaan: SQL vs pandas {int(cx.match.sum())} dari {len(cx)} cocok; validasi {int((vc.result == 'lulus').sum())} dari {len(vc)} lulus; semua kejadian yang ditanam dan benar-benar berubah terdeteksi.

## 4. Recommendation

"""
for r in sit.itertuples():
    md += f"- **{r.recommended_method}**: {r.situation[0].lower() + r.situation[1:]}. {r.reason}. Dasar: {r.basis}.\n"
md += f"""
## 5. Impact

Rumus: jam dihemat per tahun = laporan per bulan x menit copy-paste per laporan x 12 / 60. Dengan {n(imp['Laporan per bulan'])} laporan per bulan dan {n(imp['Menit copy-paste dan pengecekan per laporan'])} menit per laporan (asumsi): sekitar {n(imp['Jam dihemat per tahun'])} jam kerja per tahun (**estimated, simulated**). Waktu proses parser untuk laporan satu bulan sekitar {f(imp['Waktu parser untuk laporan satu bulan (6 file)'], 1)} detik.

## Batasan

- Semua temuan berasal dari data simulasi yang lebih rapi dari laporan nyata; hasil membuktikan metode, bukan kondisi pabrik.
- Parser hanya seandal config-nya: layout yang berubah total tetap butuh config baru, dan struktur yang belum punya jenis pembaca butuh kode baru.
- Rekonsiliasi hanya bisa dilakukan pada layout yang punya subtotal (layout 1 dan 2); layout lain hanya dicek dengan aturan sel dan tes kunci jawaban.
- Waktu pembuatan dan perbaikan oleh manusia tidak diukur dengan stopwatch; yang dicatat adalah ukuran pekerjaan dan waktu mesin. Menit copy-paste dan jumlah laporan per bulan adalah asumsi.
- Metode Power Query hanya ditulis (kode M), belum dijalankan karena tidak ada Excel di lingkungan pengerjaan; rumus Excel dihitung dengan LibreOffice, bukan Excel.
- Pembanding rekap copy-paste manual (Q14) tidak dilakukan.
- Dashboard belum di-deploy ke Streamlit Community Cloud; slide presentasi (Opsional) tidak dibuat.

## Cara menjalankan

Lihat `project/docs/how_to_use.md`. Singkatnya, dari root repo: `pip install -r project/requirements.txt`, lalu jalankan skrip berurutan di `project/code/` (tahap 1, 2, 3), dan `python -m pytest project/tests`.

## Struktur repository

```
index.html                       pengalihan ke design-and-report/
design-and-report/               halaman project (Design dan Report); src/ berisi generator Report
project/code/common.py           pengaturan bersama
project/code/1-data-preparation/ generator laporan, taksonomi layout, parser (python/parser), database
project/code/2-analysis/         akurasi, anomali, rekonsiliasi, perubahan layout, empat metode, dampak, validasi
project/code/3-presentation/     dashboard Streamlit, one-sheet, notebook, README
project/config/                  config template (templates/*.yaml), lookup.yaml, parser_rules.yaml
project/methods/                 workbook rumus Excel dan kode Power Query
project/results/                 CSV hasil per tahap
project/data/                    README, laporan contoh (samples/); data simulasi dibuat ulang oleh skrip
project/docs/                    taksonomi layout, kamus data, metrik, cara pakai, panduan menambah template
project/tests/                   pytest
```
"""
(REPO / "README.md").write_text(md, encoding="utf-8")

# ---- docs
layout_note = {x["layout"]: x["layout_note"] for x in reversed(gt["files"])}
lt = "# Taksonomi masalah layout\n\nHasil `02_layout_taxonomy.py` (memeriksa 36 laporan apa adanya, tanpa parser). Angka = jumlah file yang terkena, dari 36.\n\n"
lt += "| Masalah | Total file | " + " | ".join(f"Layout {i}" for i in range(1, 7)) + " |\n|---|---|" + "---|" * 6 + "\n"
for r in tax.itertuples():
    lt += f"| {r.description} | {r.files} | " + " | ".join(str(getattr(r, f"layout{i}")) for i in range(1, 7)) + " |\n"
lt += "\n## Enam layout\n\n" + "".join(f"- **Layout {i}**: {layout_note[i]}\n" for i in range(1, 7))
(C.DOCS_DIR).mkdir(exist_ok=True)
(C.DOCS_DIR / "layout_taxonomy.md").write_text(lt, encoding="utf-8")

dd = f"""# Kamus data

Tabel disimpan di `project/parsed.duckdb` (dibuat ulang oleh `04_build_db.py`; tidak di-commit).

## fact_output_tidy ({n(acc['sel nilai pada kunci jawaban'])} baris)
Satu baris = satu nilai: satu metrik untuk satu tanggal, shift, slot, stasiun, dan ukuran.

| Kolom | Arti |
|---|---|
| date, shift, slot, station, size | Kunci: tanggal, Shift 1 atau 2, slot 1-3 dalam shift, stasiun, ukuran botol |
| metric | `produced` (output kotor) atau `reject` (afkir); `ok` = produced - reject (kolom `ok_qty` di view `v_fact_wide`) |
| value | Jumlah botol; kosong bila sel laporan hilang |
| quality | `ok` (terbaca langsung), `fixed` (dibersihkan atau dipulihkan lewat subtotal), `flagged` (mencurigakan, nilai dipertahankan), `missing` (tidak ada nilai) |
| template | Config yang dipakai (mis. `L1_v2`) |
| source_file, source_sheet, source_cell | Alamat sel asal di laporan |

## anomaly_log
Satu baris = satu sel atau satu sheet bermasalah: `source_file, sheet, cell, template, issue_type, raw_value, action, fix_method, parsed_value`.
- `issue_type`: `text_na`, `dash`, `blank`, `unit_text`, `outlier`, `x10` (angka kali 10 yang dipulihkan lewat subtotal), `subtotal_mismatch`, `duplicate_sheet`, `unexpected_sheet`.
- `action`: `fixed` (nilai dipulihkan atau dibersihkan), `flagged` (perlu dicek manusia), `dropped` (sheet ganda dibuang).

## reconciliation
Satu baris = satu subtotal di laporan dibanding jumlah hasil parsing: `source_file, sheet, block, metric, kind, report_cell, report_total, parsed_total, diff, status, parsed_total_final, diff_final, status_final, resolution`.
`parsed_total` dan `status` dihitung sebelum pemulihan; `*_final` sesudahnya. `kind`: `subtotal` atau `row_total` (total produksi per baris di layout 2).

## method_benchmark
Satu baris = satu metode pada satu skenario: `method, scenario, n_files, build_size, build_unit, run_seconds, result_match, result_match_before_fix, fix_size, fix_unit, build_minutes, fix_minutes, status, note`.
`build_minutes` dan `fix_minutes` kosong karena waktu manusia tidak diukur; `build_size` dan `fix_size` (rumus, baris, parameter) dipakai sebagai gantinya.

## Aturan rekonsiliasi
1. Subtotal cocok bila jumlah nilai hasil parsing sama persis dengan angka laporan (toleransi 0).
2. Satu sel bermasalah dalam satu subtotal: nilainya dihitung dari subtotal dikurangi sel lain.
3. Tidak ada sel bermasalah tetapi selisih tepat 9/10 dari satu sel yang berukuran 10 kali wajar: sel itu dibagi 10.
4. Selain itu selisih dicatat sebagai `subtotal_mismatch` atau sel `flagged`; tidak ada angka yang ditebak.
"""
(C.DOCS_DIR / "data_dictionary.md").write_text(dd, encoding="utf-8")

mt = f"""# Definisi ukuran

- **Sama persis dengan kunci jawaban**: nilai hasil parsing = nilai pada data rapi asli, untuk kunci (tanggal, shift, slot, stasiun, ukuran, metrik) yang sama. Dihitung atas {n(acc['sel nilai pada kunci jawaban'])} sel.
- **Sel tepercaya**: berstatus `ok` atau `fixed`. Tujuan: semua sel tepercaya sama persis dengan kunci jawaban.
- **Sel ditandai**: `flagged` atau `missing`, tercatat di log anomali.
- **Match rate rekonsiliasi**: subtotal yang cocok dibagi seluruh subtotal; dilaporkan sebelum dan sesudah pemulihan.
- **Kejadian yang ditanam terdeteksi**: sel yang benar-benar berubah di file (dicek dengan membaca sel) dan tercatat di log anomali pada file, sheet, dan sel yang sama.
- **Hasil metode (result_match)**: sel kunci jawaban pada file yang diproses yang nilainya sama persis dengan keluaran metode.
- **Jam dihemat per tahun** = laporan per bulan x menit copy-paste per laporan x 12 / 60 (estimated, simulated).
"""
(C.DOCS_DIR / "metrics.md").write_text(mt, encoding="utf-8")

hu = """# Cara memakai

Dari root repo:

```
pip install -r project/requirements.txt
python project/code/1-data-preparation/python/01_generate_reports.py   # membuat 36 laporan simulasi (sekitar 1 menit)
python project/code/1-data-preparation/python/02_layout_taxonomy.py
python project/code/1-data-preparation/python/03_parse_all.py          # parse: fact, anomaly_log, reconciliation
python project/code/1-data-preparation/python/04_build_db.py           # parsed.duckdb
for f in project/code/2-analysis/python/0[5-9]_*.py project/code/2-analysis/python/1[0-3]_*.py; do python $f; done
python project/code/3-presentation/python/14_build_dashboard_data.py
python project/code/3-presentation/python/15_build_onesheet.py
python project/code/3-presentation/python/16_build_notebook.py
python project/code/3-presentation/python/17_build_docs.py
streamlit run project/code/3-presentation/streamlit/app.py
python -m pytest project/tests -q
```

Memparse satu laporan sendiri:

```python
import sys; sys.path[:0] = ["project/code", "project/code/1-data-preparation/python"]
import common as C
from parser import load_lookup, load_rules, load_templates, parse_files
out = parse_files(["laporan_saya.xlsx"], load_templates(C.TEMPLATES_DIR), load_lookup(C.LOOKUP), load_rules(C.RULES))
out["fact"], out["anomaly"], out["reconciliation"]
```

Bila layout laporan belum punya config, parser berhenti dengan `UnknownTemplate`. Cara menambah template: `add_new_template.md`.
"""
(C.DOCS_DIR / "how_to_use.md").write_text(hu, encoding="utf-8")

an = """# Menambah template baru

Parser tidak menebak layout. Setiap layout laporan punya satu file config di `project/config/templates/`. Bila bentuk laporan masuk salah satu dari empat jenis pembaca, kode Python tidak perlu diubah.

## 1. Pilih jenis pembaca (`reader`)
| reader | Bentuk laporan | Contoh |
|---|---|---|
| `date_columns` | tanggal sebagai kolom, blok bernama (PRODUKSI, REJECT), baris TOTAL | `L1_v1.yaml` |
| `date_shift_groups` | blok berulang per tanggal dan shift, slot melebar, baris Subtotal | `L2_v1.yaml` |
| `wide_groups` | header dua tingkat (grup digabung + Prod/Rej), satu baris per kombinasi kunci | `L3_v1.yaml`, `L6_v1.yaml` |
| `flat` | tabel rata, satu atau beberapa blok berdampingan, angka boleh teks | `L4_v1.yaml`, `L5_v1.yaml` |

## 2. Salin config terdekat dan ubah
Contoh `flat` (layout 4):

```yaml
id: L4_v1
layout: 4
reader: flat
detect:                      # cara parser mengenali file ini; harus cocok dengan tepat satu config
  sheet_regex: '^Output$'
  cells:
    - {cell: A1, equals: Shift 1}
    - {cell: H1, equals: Shift 2}
sheets: {include: '^Output$'}
header_row: 2
first_data_row: 3
blocks:
  - {start_col: A, shift_cell: A1}
  - {start_col: H, shift_cell: H1}
columns: [date, slot, station, size, produced, reject]   # urutan kolom dari start_col; pakai _ untuk kolom yang diabaikan
date_formats: ['%d/%m/%Y']
```

## 3. Daftarkan nama baru
Nama stasiun, ukuran, atau shift yang belum dikenal membuat parser berhenti dengan `UnknownLabel`. Tambahkan variasi penulisan di `project/config/lookup.yaml`.

## 4. Uji
```
python project/code/1-data-preparation/python/03_parse_all.py
python -m pytest project/tests -q
```
Periksa `results/1-data-preparation/anomaly_log.csv` dan `reconciliation.csv`. Bila ada kunci jawaban, bandingkan seperti `05_accuracy.py`.

## Layout yang berubah di tengah jalan
Salin config lama menjadi `<layout>_v2.yaml`, ubah hanya baris yang berbeda (biasanya `detect` dan satu parameter letak). Contoh nyata: `L1_v1.yaml` ke `L1_v2.yaml` mengubah 2 baris (A3 berisi 'Revisi form' dan `first_value_col: G`).
"""
(C.DOCS_DIR / "add_new_template.md").write_text(an, encoding="utf-8")
print("README.md dan docs ditulis")
