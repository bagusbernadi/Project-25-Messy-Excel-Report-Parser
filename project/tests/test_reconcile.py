from parser.reconcile import reconcile


def mk(values, suspect=(), z=None):
    recs = []
    for i, v in enumerate(values):
        recs.append({"value": v, "suspect": i in suspect, "fixed_by": None, "issue": None, "cleared": False, "z": (z or {}).get(i, 0.0)})
    return recs


def con(total, n, kind="subtotal"):
    return {"kind": kind, "report_raw": total, "members": list(range(n)), "file": "f", "sheet": "s", "block": "b", "metric": "produced", "report_cell": "A1"}


def test_single_missing_is_recovered(rules):
    recs = mk([10, None, 30])
    c = reconcile(recs, [con(60, 3)], rules)[0]
    assert recs[1]["value"] == 20 and recs[1]["fixed_by"] == 0
    assert c["status_raw"] == "selisih" and c["status_final"] == "cocok" and c["resolution"] == "dipulihkan dari subtotal ini"


def test_two_missing_not_guessed(rules):
    recs = mk([10, None, None])
    c = reconcile(recs, [con(60, 3)], rules)[0]
    assert recs[1]["value"] is None and recs[2]["value"] is None
    assert c["status_final"] == "selisih" and c["resolution"].startswith("selisih: sel bermasalah")


def test_suspect_outlier_is_corrected(rules):
    recs = mk([10, 500, 30], suspect={1}, z={1: 9.0})
    reconcile(recs, [con(60, 3)], rules)
    assert recs[1]["value"] == 20 and not recs[1]["suspect"]


def test_false_outlier_is_cleared(rules):
    recs = mk([10, 20, 30], suspect={1})
    reconcile(recs, [con(60, 3)], rules)
    assert recs[1]["value"] == 20 and not recs[1]["suspect"] and recs[1]["cleared"]


def test_x10_signature_without_flag(rules):
    recs = mk([10, 200, 30], z={1: 5.0})              # sel kedua seharusnya 20: selisih 180 dan 9 x 200 = 10 x 180
    reconcile(recs, [con(60, 3)], rules)
    assert recs[1]["value"] == 20 and recs[1]["issue"] == "x10"


def test_wrong_subtotal_is_suspect_not_guessed(rules):
    recs = mk([10, 20, 30])
    c = reconcile(recs, [con(150, 3)], rules)[0]
    assert [r["value"] for r in recs] == [10, 20, 30]
    assert c["resolution"] == "selisih: subtotal dicurigai"


def test_recovery_never_negative(rules):
    recs = mk([40, None, 30])
    reconcile(recs, [con(60, 3)], rules)
    assert recs[1]["value"] is None


def test_second_constraint_can_recover_after_first(rules):
    recs = mk([10, None, 30, None])
    cons = [con(40, 3, "row_total"), con(100, 4)]
    cons[0]["members"] = [0, 1, 2]
    c = reconcile(recs, cons, rules)
    assert recs[1]["value"] == 0                      # 40 - 10 - 30 dari total baris
    assert recs[3]["value"] == 60                     # 100 - (10 + 0 + 30) dari subtotal, setelah sel kedua terisi
