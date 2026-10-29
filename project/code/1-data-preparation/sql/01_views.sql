-- name: v_fact_wide
CREATE OR REPLACE VIEW v_fact_wide AS
SELECT date, shift, slot, station, size, template, source_file,
       MAX(CASE WHEN metric = 'produced' THEN value END) AS produced,
       MAX(CASE WHEN metric = 'reject' THEN value END) AS reject,
       MAX(CASE WHEN metric = 'produced' THEN value END) - MAX(CASE WHEN metric = 'reject' THEN value END) AS ok_qty,
       MAX(CASE WHEN quality IN ('flagged', 'missing') THEN 1 ELSE 0 END) = 1 AS has_open_issue
FROM fact_output_tidy
GROUP BY date, shift, slot, station, size, template, source_file;

-- name: v_fact_trusted
CREATE OR REPLACE VIEW v_fact_trusted AS
SELECT * FROM fact_output_tidy WHERE quality IN ('ok', 'fixed');
