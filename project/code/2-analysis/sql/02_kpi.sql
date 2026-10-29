-- name: pivot_station_block
-- Output dan reject per stasiun per laporan bulanan (blok 25 hari kerja) dari tabel tidy; nilai hilang dihitung sebagai kosong.
SELECT f.station, regexp_extract(f.source_file, '_(\d{4}-\d{2})\.', 1) AS block_month,
       SUM(CASE WHEN f.metric = 'produced' THEN f.value END) AS produced_pivot,
       SUM(CASE WHEN f.metric = 'reject' THEN f.value END) AS reject_pivot,
       SUM(CASE WHEN f.value IS NULL THEN 1 ELSE 0 END) AS missing_cells,
       SUM(CASE WHEN f.quality = 'flagged' THEN 1 ELSE 0 END) AS flagged_cells,
       COUNT(*) AS cells
FROM fact_output_tidy f
GROUP BY 1, 2
ORDER BY 1, 2;

-- name: truth_station_block
SELECT t.station, regexp_extract(f.source_file, '_(\d{4}-\d{2})\.', 1) AS block_month,
       SUM(CASE WHEN f.metric = 'produced' THEN t.truth END) AS produced_truth, SUM(CASE WHEN f.metric = 'reject' THEN t.truth END) AS reject_truth
FROM fact_output_tidy f
JOIN (SELECT date, shift, slot, station, size, 'produced' AS metric, qty_produced AS truth FROM truth_output
      UNION ALL SELECT date, shift, slot, station, size, 'reject', qty_reject FROM truth_output) t
  ON f.date = t.date AND f.shift = t.shift AND f.slot = t.slot AND f.station = t.station AND f.size = t.size AND f.metric = t.metric
GROUP BY 1, 2
ORDER BY 1, 2;

-- name: report_totals_vs_pivot
-- Total produksi yang tertulis di laporan (layout 1: baris TOTAL PRODUKSI per tanggal; layout 2: kolom total produksi per shift) vs jumlah nilai hasil parsing.
SELECT source_file, SUM(report_total) AS report_total, SUM(parsed_total) AS pivot_total_raw, SUM(parsed_total_final) AS pivot_total_final, COUNT(*) AS n_subtotals
FROM reconciliation
WHERE metric = 'produced' AND (block LIKE '%|PRODUKSI' OR block LIKE '%|total produksi')
GROUP BY 1
ORDER BY 1;

-- name: station_rate
SELECT station, SUM(CASE WHEN metric = 'produced' THEN value END) AS produced, SUM(CASE WHEN metric = 'reject' THEN value END) AS reject,
       SUM(CASE WHEN metric = 'reject' THEN value END) * 1.0 / SUM(CASE WHEN metric = 'produced' THEN value END) AS reject_rate
FROM v_fact_trusted
GROUP BY 1
ORDER BY reject_rate DESC;

-- name: quality_counts
SELECT quality, COUNT(*) AS n FROM fact_output_tidy GROUP BY 1 ORDER BY 1;

-- name: accuracy_vs_truth
SELECT COUNT(*) AS cells, SUM(CASE WHEN f.value = t.truth THEN 1 ELSE 0 END) AS exact
FROM fact_output_tidy f
JOIN (SELECT date, shift, slot, station, size, 'produced' AS metric, qty_produced AS truth FROM truth_output
      UNION ALL SELECT date, shift, slot, station, size, 'reject', qty_reject FROM truth_output) t
  ON f.date = t.date AND f.shift = t.shift AND f.slot = t.slot AND f.station = t.station AND f.size = t.size AND f.metric = t.metric;

-- name: recon_status
SELECT status, COUNT(*) AS n FROM reconciliation GROUP BY 1 ORDER BY 1;

-- name: recon_status_final
SELECT status_final AS status, COUNT(*) AS n FROM reconciliation GROUP BY 1 ORDER BY 1;

-- name: anomaly_by_type
SELECT issue_type, COUNT(*) AS n FROM anomaly_log GROUP BY 1 ORDER BY n DESC, issue_type;
