import pytest

from scenarios import run_all


@pytest.fixture(scope="module")
def res(sim):
    return run_all().set_index("id")


def test_real_layout_change_needs_config_only(res):
    for i in ("R1", "R2"):
        r = res.loc[i]
        assert r.old_config.startswith("berhenti") and r.old_stopped_safely
        assert r.new_trusted > 1700 and r.new_trusted_exact == r.new_trusted
        assert r.config_lines_changed == 2 and r.python_lines_changed == 0


def test_synthetic_changes_are_stopped_then_fixed(res):
    for i in ("S1", "S2", "S3", "S4"):
        r = res.loc[i]
        assert r.old_config.startswith("berhenti: UnknownTemplate")
        assert r.new_trusted_exact == r.new_trusted > 800
        assert 1 <= r.config_lines_changed <= 4


def test_extra_sheet_is_ignored_and_logged(res):
    r = res.loc["S5"]
    assert r.new_trusted_exact == r.new_trusted > 800 and r.config_lines_changed == 0


def test_unknown_label_needs_one_lookup_line(res):
    r = res.loc["S6"]
    assert r.old_config.startswith("berhenti: UnknownLabel")
    assert r.lookup_lines_changed == 1 and r.new_trusted_exact == r.new_trusted > 1700


def test_non_report_is_refused(res):
    assert res.loc["S7"].old_config.startswith("berhenti: UnknownTemplate")
    assert res.loc["S7"].new_config.startswith("berhenti")
