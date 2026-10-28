[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 25: Messy Excel Report Parser

**Status: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Parser, analisis, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

**Tujuan:** membangun parser yang mengubah laporan Excel manual berlayout bebas menjadi satu tabel tidy yang terbukti cocok dengan angka laporan aslinya, lalu membandingkan empat metode pengerjaan agar tim bisa memilih cara yang paling hemat waktu dan paling tahan terhadap perubahan layout.

| | |
|---|---|
| Kategori | Manufaktur (pabrik minuman kemasan botol) |
| Tingkat | Menengah–lanjut |
| Data | Simulasi: laporan Excel berantakan yang dibuat dari data rapi (generator disertakan) |
| Tools | Python (openpyxl, pandas, pytest), YAML, DuckDB + SQL, Excel (rumus + Power Query), Streamlit + Plotly |

## 1. Problem

**Pertanyaan utama:** Bagaimana mengubah laporan Excel manual berlayout bebas menjadi tabel tidy tanpa copy-paste, membuktikan bahwa hasilnya benar, dan memilih metode yang paling cocok untuk tiap situasi?

Rancangan memecahnya menjadi 15 pertanyaan (10 Utama, 4 Pendukung, 1 Tambahan) dalam 7 tema: layout, akurasi, ketahanan, metode, pemakaian hasil, dampak, dan validitas. Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- Sumber: data simulasi buatan sendiri, dibuat oleh `scripts/generate_reports.py` (Versi: v1; Tanggal dibuat: 28 Okt 2026; Seed: 25260302). Tidak memakai dataset publik atau data perusahaan.
- Konteks: pabrik minuman kemasan botol, 10 stasiun (Water Treatment sampai Palletizing), 3 ukuran botol (330 ml, 600 ml, 1,5 L), 2 shift.
- Ukuran (perkiraan): 6 template layout × 6 bulan = ±36 file Excel; tabel tidy ±27.000 baris.
- Rencana tabel: `fact_output_tidy`, `anomaly_log`, `reconciliation`, `method_benchmark`.
- Fakta yang sengaja ditanam: 6 jenis masalah layout, perubahan layout di bulan ke-4, 2 subtotal salah ketik, 1 sheet ganda, dan 2–3% sel kotor.

## 3. Analysis

Belum dikerjakan. Rencana langkah (12 langkah, tahap A sampai D) ada di bagian 6 halaman rancangan. Hasil parser dicocokkan dengan subtotal laporan (rekonsiliasi) dan dengan data rapi asli (ground truth), lalu dicek silang dengan Excel.

## 4. Recommendation

Belum dikerjakan. Output yang direncanakan: matriks rekomendasi metode per situasi (rumus Excel untuk end user, Power Query untuk tim non-programmer, Python untuk banyak file, SQL untuk data yang sudah di database).

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated` dan `simulated`):

```
Jam dihemat per tahun = laporan per bulan × menit copy-paste per laporan × 12 ÷ 60
```

## Batasan yang sudah diketahui

- Parser hanya seandal config-nya. Layout yang berubah total tetap butuh config baru.
- Rekonsiliasi hanya bisa dilakukan pada blok yang punya subtotal.
- Waktu pembuatan tiap metode dicatat sendiri oleh satu orang, sehingga bias. Bias ini ditulis terbuka.
- Data simulasi lebih rapi dari laporan nyata.

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `configs/`, `parser/`, `tests/`, `data/`, `scripts/`, `sql/`, `methods/`, `notebooks/`, `dashboard/`, dan `outputs/` ditambahkan saat pengerjaan dimulai.
