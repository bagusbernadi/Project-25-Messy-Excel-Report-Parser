"""Tahap 1 / langkah 4: muat tabel hasil parsing ke DuckDB (parsed.duckdb) dan buat view."""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

C.DB_PATH.unlink(missing_ok=True)
con = duckdb.connect(str(C.DB_PATH))
con.execute(f"CREATE TABLE fact_output_tidy AS SELECT CAST(date AS DATE) AS date, shift, CAST(slot AS INTEGER) AS slot, station, size, metric, CAST(value AS INTEGER) AS value, quality, template, source_file, source_sheet, source_cell FROM read_csv_auto('{C.PARSED_DIR / 'fact_output_tidy.csv'}')")
con.execute(f"CREATE TABLE anomaly_log AS SELECT * FROM read_csv_auto('{C.RES_PREP / 'anomaly_log.csv'}', all_varchar=true)")
con.execute(f"CREATE TABLE reconciliation AS SELECT * FROM read_csv_auto('{C.RES_PREP / 'reconciliation.csv'}')")
con.execute(f"CREATE TABLE truth_output AS SELECT CAST(date AS DATE) AS date, shift, CAST(slot AS INTEGER) AS slot, station, size, qty_produced, qty_reject FROM read_csv_auto('{C.TRUTH_CSV}')")
for name, q in C.load_sql(C.SQL_PREP / "01_views.sql").items():
    con.execute(q)
for t in ("fact_output_tidy", "anomaly_log", "reconciliation", "truth_output"):
    print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
con.close()
