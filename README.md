[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 25: Messy Excel Report Parser

**Status: selesai di branch `project-25-build` (menunggu review sebelum digabung ke `main`).**

Halaman rancangan dan Report: https://bagusbernadi.github.io/project-25-messy-excel-report-parser/

| | |
|---|---|
| Kategori | Manufaktur (pabrik minuman kemasan botol) |
| Tingkat | Menengah–lanjut |
| Data | Simulasi: 36 laporan Excel berantakan (6 layout x 6 bulan) dibuat dari data rapi; kunci jawaban diketahui |
| Tools | Python (openpyxl, pandas, pytest), YAML, DuckDB + SQL, rumus Excel (dihitung LibreOffice), Power Query (kode M, belum dijalankan), Streamlit + Plotly |

## 1. Problem

Bagaimana mengubah laporan Excel manual berlayout bebas menjadi tabel tidy tanpa copy-paste, membuktikan bahwa hasilnya benar, dan memilih metode yang paling cocok untuk tiap situasi? Dipecah menjadi 15 pertanyaan (10 Utama); jawabannya ada di tab Report pada halaman project.

## 2. Data

- Data simulasi dengan seed tetap (`project/code/1-data-preparation/python/01_generate_reports.py`, v1): data rapi 27.000 baris (150 hari x 2 shift x 3 slot x 10 stasiun x 3 ukuran) dituang ke 36 file Excel, 6 template layout.
- Fakta yang ditanam: 6 layout, perubahan layout pada layout 1 dan 3 di bulan ke-4, 2 subtotal salah ketik, 1 sheet ganda, dan sel angka kotor. Dari 1.215 sel yang dicatat sebagai bermasalah, 240 berjenis 'blank' ternyata tidak benar-benar dikosongkan oleh pembuat data (nilai tetap utuh), sehingga yang nyata adalah 972 sel angka kotor (salah, hilang, atau berformat teks), 2 subtotal salah, dan 1 sheet ganda.
- Laporan hasil simulasi tidak di-commit (dibuat ulang dalam sekitar satu menit); 6 laporan contoh ada di `project/data/samples/`. Detail kolom tabel hasil: `project/docs/data_dictionary.md`.

## 3. Analysis

- Parser berbasis config: 8 file config YAML untuk 6 layout (termasuk 2 revisi bulan ke-4), 4 jenis pembaca, kamus nama di `project/config/lookup.yaml`. Template dikenali dari isi sel; bila tidak ada yang cocok parser berhenti, tidak menebak.
- Hasil: 54.000 nilai dalam tabel tidy. 53.520 dari 53.520 nilai berstatus ok atau fixed sama persis dengan data rapi asli (0 salah lolos); 480 nilai ditandai (flagged atau missing) di log anomali. Persen sama persis seluruhnya: 99,1%.
- Rekonsiliasi: 4.200 subtotal laporan (layout 1 dan 2). Sebelum pemulihan 3.753 cocok (89,4%); sesudah pemulihan 4.164 cocok (99,1%). Sisanya adalah sel yang tidak bisa dipastikan dan 2 subtotal salah ketik yang ditemukan.
- Anomali di log: 975 baris; jenis terbanyak dash (246). 252 sel dipulihkan tepat lewat subtotal.
- Perubahan layout: bulan ke-4 layout 1 dan 3 hanya butuh 2 baris config, tanpa mengubah kode Python; dengan config lama parser berhenti. Template baru dari nol rata-rata 18 baris config.
- Empat metode pada file yang sama: rumus Excel 0,94 detik, SQL 0,95 detik, parser Python 0,07 detik per file; Power Query belum dijalankan. Untuk 36 file parser butuh 3,0 detik.
- Pemeriksaan: SQL vs pandas 18 dari 18 cocok; validasi 7 dari 7 lulus; semua kejadian yang ditanam dan benar-benar berubah terdeteksi.

## 4. Recommendation

- **Rumus Excel**: end user di lini produksi, satu atau dua file, tanpa programmer. Tanpa instalasi; perubahan layout cukup mengubah satu sel parameter; waktu proses sekitar satu detik per file. Dasar: diukur.
- **Power Query**: tim non-programmer yang rutin mengolah banyak file satu layout. Refresh dari folder tanpa menulis kode; perubahan layout lewat parameter. Belum diuji karena Excel tidak tersedia. Dasar: penilaian (belum dijalankan).
- **Python (parser)**: banyak file dengan banyak layout dan perlu bukti kebenaran. Pilih template otomatis, rekonsiliasi dengan subtotal, pemulihan dan penandaan sel; berhenti bila layout tak dikenal. Dasar: diukur.
- **SQL (DuckDB)**: data sudah berupa tabel di database. Sekali tabel sel termuat, query bisa diulang dan diaudit; tidak membaca .xlsx langsung. Dasar: diukur.

## 5. Impact

Rumus: jam dihemat per tahun = laporan per bulan x menit copy-paste per laporan x 12 / 60. Dengan 6 laporan per bulan dan 30 menit per laporan (asumsi): sekitar 36 jam kerja per tahun (**estimated, simulated**). Waktu proses parser untuk laporan satu bulan sekitar 0,5 detik.

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
