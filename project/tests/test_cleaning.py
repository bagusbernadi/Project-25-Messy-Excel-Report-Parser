from datetime import date, datetime

import pytest

from parser import UnknownLabel
from parser.cells import parse_date
from parser.clean import clean_value


def test_clean_numbers(rules):
    cv = lambda x, **k: clean_value(x, rules, **k)  # noqa: E731
    assert cv(3200) == (3200, None, None)
    assert cv(12.0) == (12, None, None)
    assert cv("123 btl") == (123, "unit_text", "strip_unit")
    assert cv("3.200 btl") == (3200, "unit_text", "strip_unit")
    assert cv("3.200 btl", expected_text=True) == (3200, None, None)
    assert cv("12 pcs", expected_text=True) == (12, None, None)
    assert cv("n/a") == (None, "text_na", None)
    assert cv("-") == (None, "dash", None)
    assert cv(None) == (None, "blank", None)
    assert cv("  ")[1] == "blank"
    assert cv("abc")[1] == "unreadable"


def test_dash_is_missing_not_zero(rules):
    assert clean_value("-", rules)[0] is None


def test_parse_date_formats(lookup):
    mo = lookup.months
    assert parse_date("02-Mar-26", ["%d-%b-%y"], mo) == date(2026, 3, 2)
    assert parse_date("2026/03/02", ["%Y/%m/%d"], mo) == date(2026, 3, 2)
    assert parse_date("02.03.2026", ["%d.%m.%Y"], mo) == date(2026, 3, 2)
    assert parse_date(datetime(2026, 3, 2), [], mo) == date(2026, 3, 2)
    assert parse_date("Catatan: angka dalam botol", ["%d/%m/%Y"], mo) is None


def test_lookup_variants(lookup):
    assert lookup.station("WTP") == "Water Treatment"
    assert lookup.size("0,6 L") == "600 ml"
    assert lookup.shift("II") == "Shift 2"
    assert lookup.slot_from_time("Shift 2", "18:00-21:00") == 2


def test_unknown_label_stops(lookup):
    with pytest.raises(UnknownLabel):
        lookup.station("Mesin Baru")
