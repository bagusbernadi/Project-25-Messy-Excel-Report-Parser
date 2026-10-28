# Data simulasi

- Versi data: v1
- Tanggal dibuat: 28 Okt 2026
- Seed: 25260302
- Data tidak disimpan di repo. Dibuat ulang (hasil identik) dengan:

```
pip install numpy pandas openpyxl Faker reportlab Pillow   # sesuai impor skrip
python scripts/generate_reports.py
```

- Hasil di `data/sim/`: 36 file Excel laporan (6 layout x 6 blok bulan), `truth_fact_output_tidy.csv` (27.000 baris), `ground_truth_dirty_cells.csv`, `ground_truth.json`.
- Uji determinisme: dijalankan 2x, SHA-256 semua berkas identik. Daftar hash ada di repo DataCenter, `simulasi/fingerprints/project-25.sha256`.
