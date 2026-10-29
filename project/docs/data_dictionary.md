# Kamus data

Tabel disimpan di `project/parsed.duckdb` (dibuat ulang oleh `04_build_db.py`; tidak di-commit).

## fact_output_tidy (54.000 baris)
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
