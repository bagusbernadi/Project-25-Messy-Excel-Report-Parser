# Data simulasi

- Versi data: v1
- Tanggal dibuat: 28 Okt 2026
- Seed: 25260302
- Jenis: simulasi murni (tidak ada data kerja). Lisensi dataset: tidak berlaku (data buatan sendiri).
- Data tidak disimpan di repo (kecuali `samples/`). Dibuat ulang (hasil identik) dari folder repo:

```
pip install -r project/requirements.txt
python project/code/1-data-preparation/python/01_generate_reports.py
```

- Hasil di `project/data/sim/`: 36 file Excel di `reports/` (6 layout x 6 blok bulan), `truth_fact_output_tidy.csv` (27.000 baris), `ground_truth_dirty_cells.csv`, `ground_truth.json`.
- `project/data/parsed/` berisi hasil parser (`fact_output_tidy.csv`, 54.000 baris), dibuat oleh `03_parse_all.py`.
- `project/data/samples/`: 6 file Excel contoh (satu per layout, bulan Mar) yang di-commit.
- Uji determinisme: dijalankan 2x, SHA-256 semua berkas identik, dan identik dengan daftar di repo DataCenter, `simulasi/fingerprints/project-25.sha256` (39 berkas).
- Catatan generator v1: jenis masalah `blank` (240 sel) tidak benar-benar mengosongkan sel (`openpyxl cell(r, c, None)` tidak menimpa nilai). Sel tersebut tetap terisi dan terbaca benar. Yang efektif: 975 baris anomali yang dicatat parser, 972 sel bermasalah efektif (lihat `results/2-analysis/planted_cells_effective.csv`).
