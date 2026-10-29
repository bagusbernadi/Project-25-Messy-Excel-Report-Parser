"""Tahap 2 / langkah 10 (Q11, Q12): pivot dari tabel tidy (SQL) vs kunci jawaban dan total laporan; pola setelah 6 bulan digabung."""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C  # noqa: E402

con = duckdb.connect(str(C.DB_PATH), read_only=True)
Q = C.load_sql(C.SQL_ANALYSIS / "02_kpi.sql")
# nama stasiun -> kelompok file; blok bulan = bulan pada nama file
piv, tru = con.execute(Q["pivot_station_block"]).df(), con.execute(Q["truth_station_block"]).df()
m = piv.merge(tru, on=["station", "block_month"], validate="one_to_one")
m["produced_diff"] = m.produced_pivot - m.produced_truth
m["produced_diff_pct"] = m.produced_diff / m.produced_truth
m["reject_diff"] = m.reject_pivot - m.reject_truth
m["reject_rate_pivot"] = m.reject_pivot / m.produced_pivot
m["reject_rate_truth"] = m.reject_truth / m.produced_truth
m["reject_rate_diff_pp"] = (m.reject_rate_pivot - m.reject_rate_truth) * 100
m.to_csv(C.RES_ANALYSIS / "pivot_vs_truth.csv", index=False)

rt = con.execute(Q["report_totals_vs_pivot"]).df()
rt["layout"] = rt.source_file.str.extract(r"_G(\d)_")[0].astype(int)
rt["diff_raw"] = rt.pivot_total_raw - rt.report_total
rt["diff_final"] = rt.pivot_total_final - rt.report_total
rt["same_after_repair"] = rt.diff_final == 0
rt.to_csv(C.RES_ANALYSIS / "pivot_vs_report_totals.csv", index=False)

rate = con.execute(Q["station_rate"]).df()
rate.to_csv(C.RES_ANALYSIS / "station_reject_rate.csv", index=False)
# tren: kemiringan reject rate (poin persentase per laporan bulanan) per stasiun; nilai kunci jawaban dipakai agar tidak terpengaruh sel hilang
slopes = []
for st, g in m.sort_values("block_month").groupby("station"):
    x = np.arange(len(g))
    slopes.append({"station": st, "slope_pp_per_block": float(np.polyfit(x, g.reject_rate_truth.to_numpy() * 100, 1)[0]), "rate_first_block": g.reject_rate_truth.iloc[0], "rate_last_block": g.reject_rate_truth.iloc[-1],
                   "rate_min_block": g.reject_rate_truth.min(), "rate_max_block": g.reject_rate_truth.max()})
sl = pd.DataFrame(slopes).sort_values("station")
sl.to_csv(C.RES_ANALYSIS / "trend_slopes.csv", index=False)
tr = pd.read_csv(C.TRUTH_CSV)
sz = tr.groupby("size").agg(produced=("qty_produced", "sum"), reject=("qty_reject", "sum")).reset_index()
sz["reject_rate"] = sz.reject / sz.produced
sh = tr.groupby("shift").agg(produced=("qty_produced", "sum"), reject=("qty_reject", "sum")).reset_index()
sh["reject_rate"] = sh.reject / sh.produced
pd.concat([sz.rename(columns={"size": "group"}).assign(dimension="ukuran"), sh.rename(columns={"shift": "group"}).assign(dimension="shift")])[["dimension", "group", "produced", "reject", "reject_rate"]].to_csv(C.RES_ANALYSIS / "rate_by_size_shift.csv", index=False)
print(m[["station", "block_month", "produced_diff_pct", "reject_rate_diff_pp", "missing_cells", "flagged_cells"]].head(8).to_string(index=False))
print(rt.groupby("layout")[["report_total", "diff_raw", "diff_final"]].sum()); print(rate.to_string(index=False)); print(sl.to_string(index=False)); print(sz, sh)
