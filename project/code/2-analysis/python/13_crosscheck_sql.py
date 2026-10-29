"""Tahap 2 / langkah 13: cek silang hasil SQL (DuckDB) dengan pandas untuk angka kunci."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C, fact_vs_truth, load_fact  # noqa: E402

con = duckdb.connect(str(C.DB_PATH), read_only=True)
Q = C.load_sql(C.SQL_ANALYSIS / "02_kpi.sql")
f = load_fact()
m = fact_vs_truth()
a = pd.read_csv(C.RES_PREP / "anomaly_log.csv")
r = pd.read_csv(C.RES_PREP / "reconciliation.csv")
rows = []


def chk(name, sql_v, pd_v):
    rows.append({"check": name, "sql": float(sql_v), "pandas": float(pd_v), "diff": float(sql_v) - float(pd_v), "match": abs(float(sql_v) - float(pd_v)) < 1e-9})


qc = con.execute(Q["quality_counts"]).df().set_index("quality").n
for qn in ("ok", "fixed", "flagged", "missing"):
    chk(f"sel berstatus {qn}", qc[qn], (f.quality == qn).sum())
acc = con.execute(Q["accuracy_vs_truth"]).df().iloc[0]
chk("sel pada kunci jawaban", acc.cells, len(m))
chk("sel sama persis dengan kunci jawaban", acc.exact, m.exact.sum())
rs = con.execute(Q["recon_status"]).df().set_index("status").n
chk("subtotal cocok sebelum pemulihan", rs.get("cocok", 0), (r.status == "cocok").sum())
chk("subtotal selisih sebelum pemulihan", rs.get("selisih", 0), (r.status == "selisih").sum())
rf = con.execute(Q["recon_status_final"]).df().set_index("status").n
chk("subtotal cocok sesudah pemulihan", rf.get("cocok", 0), (r.status_final == "cocok").sum())
an = con.execute(Q["anomaly_by_type"]).df().set_index("issue_type").n
for t in a.issue_type.unique():
    chk(f"anomali {t}", an[t], (a.issue_type == t).sum())
sr = con.execute(Q["station_rate"]).df().set_index("station")
tr = f[f.quality.isin(["ok", "fixed"])].pivot_table(index="station", columns="metric", values="value", aggfunc="sum")
chk("reject rate tertinggi (stasiun tepercaya)", sr.reject_rate.iloc[0], (tr.reject / tr["produced"]).max())
chk("produksi total tepercaya", sr.produced.sum(), tr["produced"].sum())
pv = con.execute(Q["pivot_station_block"]).df()
chk("produksi total di pivot (semua nilai)", pv.produced_pivot.sum(), f[f.metric == "produced"].value.sum())
x = pd.DataFrame(rows)
x.to_csv(C.RES_ANALYSIS / "crosscheck_sql.csv", index=False)
print(x.to_string(index=False)); assert x.match.all()
