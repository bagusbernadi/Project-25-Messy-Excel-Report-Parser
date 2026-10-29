"""Dashboard Project 25 (3 halaman): Data Produksi, Kualitas Parsing, Perbandingan Metode. Membaca CSV ringkas di results/3-presentation/.

Jalankan:  streamlit run project/code/3-presentation/streamlit/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RES = Path(__file__).resolve().parents[3] / "results" / "3-presentation"
BLUE, ORANGE, GREY = "#1A73E8", "#E8710A", "#9AA0A6"
st.set_page_config(page_title="Project 25: Messy Excel Report Parser", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(RES / name)


def idn(n, d=0):
    return f"{n:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


page = st.sidebar.radio("Halaman", ["Data Produksi", "Kualitas Parsing", "Perbandingan Metode"])
st.sidebar.caption("Data simulasi (laporan Excel buatan). Hasil menguji metode, bukan kondisi pabrik.")
st.title("Project 25: Messy Excel Report Parser")

if page == "Data Produksi":
    d = load("dash_pivot.csv")
    st.caption("Pivot dari tabel tidy hasil parsing. Sel yang hilang atau mencurigakan tidak dihitung ulang; jumlahnya ditampilkan di bawah.")
    c1, c2, c3 = st.columns(3)
    stations = c1.multiselect("Stasiun", sorted(d.station.unique()), default=sorted(d.station.unique()))
    sizes = c2.multiselect("Ukuran", sorted(d["size"].unique()), default=sorted(d["size"].unique()))
    shifts = c3.multiselect("Shift", sorted(d["shift"].unique()), default=sorted(d["shift"].unique()))
    x = d[d.station.isin(stations) & d["size"].isin(sizes) & d["shift"].isin(shifts)]
    k1, k2, k3, k4 = st.columns(4)
    prod, rej = x["produced"].sum(), x["reject"].sum()
    k1.metric("Output (botol)", idn(prod))
    k2.metric("Reject (botol)", idn(rej))
    k3.metric("Reject rate", idn(rej / prod * 100, 2) + "%" if prod else "-")
    k4.metric("Sel belum pasti", idn(x.open_cells.sum()))
    by = x.groupby("station").agg(produced=("produced", "sum"), reject=("reject", "sum")).reset_index()
    by["reject_rate"] = by.reject / by.produced * 100
    st.plotly_chart(px.bar(by.sort_values("reject_rate", ascending=False), x="station", y="reject_rate", labels={"reject_rate": "reject rate (%)", "station": ""}, color_discrete_sequence=[BLUE]), width="stretch")
    mo = x.groupby("block_month").agg(produced=("produced", "sum"), reject=("reject", "sum")).reset_index()
    st.plotly_chart(px.bar(mo, x="block_month", y="produced", labels={"produced": "output (botol)", "block_month": "laporan bulan"}, color_discrete_sequence=[BLUE]), width="stretch")
    st.dataframe(by.rename(columns={"produced": "output", "reject": "reject"}), width="stretch", hide_index=True)

elif page == "Kualitas Parsing":
    fs, rs, tp, an, op = load("dash_files.csv"), load("dash_recon_summary.csv"), load("dash_anomaly_type.csv"), load("dash_anomaly.csv"), load("dash_recon_open.csv")
    tot = fs[["ok", "fixed", "flagged", "missing"]].sum()
    c = st.columns(4)
    c[0].metric("Sel berstatus ok", idn(tot["ok"]))
    c[1].metric("Dipulihkan (fixed)", idn(tot["fixed"]))
    c[2].metric("Mencurigakan (flagged)", idn(tot["flagged"]))
    c[3].metric("Hilang (missing)", idn(tot["missing"]))
    st.subheader("Rekonsiliasi subtotal")
    rs = rs.assign(layout=rs.layout.astype(str) + " " + rs.kind)
    m = rs.melt(id_vars="layout", value_vars=["match_rate_raw", "match_rate_final"], var_name="tahap", value_name="rate")
    m["tahap"] = m.tahap.map({"match_rate_raw": "sebelum pemulihan", "match_rate_final": "sesudah pemulihan"})
    st.plotly_chart(px.bar(m, x="layout", y="rate", color="tahap", barmode="group", labels={"rate": "subtotal yang cocok", "layout": "layout dan jenis subtotal"}, color_discrete_sequence=[GREY, BLUE]), width="stretch")
    st.subheader("Anomali sel menurut jenis")
    st.plotly_chart(px.bar(tp, x="issue_type", y="n", color_discrete_sequence=[ORANGE], labels={"n": "jumlah", "issue_type": ""}), width="stretch")
    st.subheader("Log anomali (setiap baris bisa dilacak ke file, sheet, dan sel)")
    f1, f2 = st.columns(2)
    it = f1.multiselect("Jenis", sorted(an.issue_type.dropna().unique()), default=sorted(an.issue_type.dropna().unique()))
    ac = f2.multiselect("Tindakan", sorted(an.action.unique()), default=sorted(an.action.unique()))
    st.dataframe(an[an.issue_type.isin(it) & an.action.isin(ac)], width="stretch", hide_index=True)
    st.subheader("Subtotal yang belum cocok setelah pemulihan")
    st.dataframe(op[op.status_final != "cocok"], width="stretch", hide_index=True)

else:
    b, sit, mat = load("dash_benchmark.csv"), load("dash_situations.csv"), load("dash_matrix.csv")
    st.subheader("Metode mana untuk situasi mana")
    st.dataframe(sit, width="stretch", hide_index=True)
    st.subheader("Benchmark (waktu proses adalah waktu mesin, bukan waktu pengerjaan manusia)")
    sc = st.selectbox("Skenario", list(b.scenario.unique()))
    x = b[b.scenario == sc]
    st.dataframe(x[["method", "n_files", "run_seconds", "result_match", "result_match_before_fix", "fix_size", "fix_unit", "status", "note"]], width="stretch", hide_index=True)
    t = x.dropna(subset=["run_seconds"])
    if len(t):
        st.plotly_chart(px.bar(t, x="method", y="run_seconds", labels={"run_seconds": "detik", "method": ""}, color_discrete_sequence=[BLUE]), width="stretch")
    st.subheader("Perbandingan kriteria")
    st.dataframe(mat, width="stretch", hide_index=True)
    st.subheader("Estimasi jam copy-paste yang dihemat per tahun (estimated, simulated)")
    im = load("dash_impact.csv")
    st.plotly_chart(px.bar(im, x="reports_per_month", y="hours_saved_per_year", color="minutes_per_report", barmode="group", labels={"reports_per_month": "laporan per bulan", "hours_saved_per_year": "jam per tahun", "minutes_per_report": "menit per laporan"}), width="stretch")
    st.caption("Waktu pembuatan dan perbaikan oleh manusia tidak diukur dengan stopwatch; kolom ukuran perubahan (parameter, baris config) dipakai sebagai gantinya.")
