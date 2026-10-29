# Menambah template baru

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
