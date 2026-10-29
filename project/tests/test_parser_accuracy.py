import json

import pandas as pd

from parser import parse_files
import common as C

KEY = ["date", "shift", "slot", "station", "size", "metric"]


def test_all_cells_present_and_unique(parsed, truth):
    f = parsed["fact"]
    assert len(f) == len(truth) == 54000
    assert not f.duplicated(KEY).any()
    f = f.assign(date=f.date.astype(str))
    assert len(truth.merge(f[KEY], on=KEY, how="inner")) == 54000


def test_trusted_cells_equal_truth(parsed, truth):
    f = parsed["fact"].assign(date=lambda x: x.date.astype(str))
    m = f.merge(truth, on=KEY)
    t = m[m.quality.isin(["ok", "fixed"])]
    assert len(t) > 53000
    assert (t.value == t.truth).all()


def test_untrusted_cells_have_no_silent_values(parsed):
    f = parsed["fact"]
    assert f[f.quality == "missing"].value.isna().all()
    assert f[f.quality != "missing"].value.notna().all()


def test_subtotal_typos_flagged(parsed):
    a = parsed["anomaly"]
    t = a[a.issue_type == "subtotal_mismatch"]
    assert sorted(t.source_file) == ["laporan_G2_2026-04.xlsx", "laporan_G2_2026-07.xlsx"]
    assert set(t.cell) == {"H503", "F367"}


def test_duplicate_sheet_dropped(parsed):
    a = parsed["anomaly"]
    d = a[a.issue_type == "duplicate_sheet"]
    assert len(d) == 1 and d.iloc[0].source_file == "laporan_G1_2026-05.xlsx" and d.iloc[0].action == "dropped"
    f = parsed["fact"]
    assert "Sheet1 (2)" not in set(f.source_sheet)


def test_every_planted_effective_dirty_cell_is_logged(parsed, sim):
    d = pd.read_csv(C.DIRTY_CSV)
    d = d[d.problem.isin(["text_na", "dash", "unit_text", "x10"]) & ~((d.problem == "x10") & (d.original == 0))]
    a = parsed["anomaly"]
    logged = set(a.source_file + "|" + a.sheet + "|" + a.cell.fillna(""))
    assert (d.file + "|" + d.sheet + "|" + d.cell).isin(logged).all()


def test_no_anomaly_outside_planted(parsed, sim):
    d = pd.read_csv(C.DIRTY_CSV)
    a = parsed["anomaly"]
    planted = set(d.file + "|" + d.sheet + "|" + d.cell.fillna(""))
    assert (a.source_file + "|" + a.sheet + "|" + a.cell.fillna("")).isin(planted).all()


def test_parse_is_deterministic(sim, templates, lookup, rules, parsed):
    again = parse_files(sorted(sim.glob("*.xlsx")), templates, lookup, rules)
    pd.testing.assert_frame_equal(parsed["fact"], again["fact"])
    pd.testing.assert_frame_equal(parsed["anomaly"], again["anomaly"])


def test_ground_truth_version(sim):
    g = json.loads(C.GROUND_TRUTH.read_text(encoding="utf-8"))
    assert g["seed"] == 25260302 and g["version"] == "v1" and g["n_files"] == 36 and g["tidy_rows"] == 27000
