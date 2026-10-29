-- Metode SQL untuk layout 1 (tanggal sebagai kolom, blok PRODUKSI dan REJECT).
-- Tabel cell_dump(r, c, v) berisi isi setiap sel laporan sebagai teks. Parameter {first_value_col} dan {year} diisi sebelum dijalankan.
-- name: method_L1
WITH marker AS (
    SELECT r AS marker_row, v AS block FROM cell_dump WHERE c = 1 AND v IN ('PRODUKSI', 'REJECT')
), total AS (
    SELECT m.marker_row, MIN(t.r) AS total_row FROM marker m JOIN cell_dump t ON t.c = 1 AND t.r > m.marker_row AND t.v LIKE 'TOTAL%' GROUP BY m.marker_row
), hdr AS (
    SELECT m.marker_row, m.block, h.c, h.v AS date_text FROM marker m JOIN cell_dump h ON h.r = m.marker_row + 1 AND h.c >= {first_value_col} AND h.v IS NOT NULL
), keys AS (
    SELECT m.marker_row, k.r,
           MAX(CASE WHEN k.c = 1 THEN k.v END) AS station, MAX(CASE WHEN k.c = 2 THEN k.v END) AS size,
           MAX(CASE WHEN k.c = 3 THEN k.v END) AS shift, MAX(CASE WHEN k.c = 4 THEN k.v END) AS slot
    FROM marker m JOIN total t USING (marker_row) JOIN cell_dump k ON k.r > m.marker_row + 1 AND k.r < t.total_row AND k.c <= 4
    GROUP BY m.marker_row, k.r
)
SELECT make_date({year}, CAST(substr(h.date_text, 4, 2) AS INTEGER), CAST(substr(h.date_text, 1, 2) AS INTEGER)) AS date,
       k.shift, CAST(k.slot AS INTEGER) AS slot, k.station, k.size,
       CASE h.block WHEN 'PRODUKSI' THEN 'produced' ELSE 'reject' END AS metric,
       TRY_CAST(REPLACE(REPLACE(x.v, ' btl', ''), '.', '') AS INTEGER) AS value
FROM keys k JOIN hdr h ON h.marker_row = k.marker_row JOIN cell_dump x ON x.r = k.r AND x.c = h.c
