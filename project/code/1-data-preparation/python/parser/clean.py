"""Pembersihan nilai sel angka dan deteksi sel mencurigakan (outlier robust)."""
import re
import statistics
from collections import defaultdict

_NUM = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+)\s*([A-Za-z]+)?")


def clean_value(raw, rules, expected_text=False):
    """Isi sel -> (nilai int atau None, jenis masalah atau None, cara perbaikan atau None)."""
    nr = rules["numbers"]
    if raw is None:
        return None, "blank", None
    if isinstance(raw, bool):
        return None, "unreadable", None
    if isinstance(raw, int):
        return raw, None, None
    if isinstance(raw, float):
        return (int(raw), None, None) if raw.is_integer() else (None, "unreadable", None)
    s = str(raw).strip()
    low = s.lower()
    if low in nr["missing_tokens"]:
        return None, ("blank" if low == "" else "dash" if low in nr["dash_tokens"] else "text_na"), None
    m = _NUM.fullmatch(s)
    if m and (m.group(2) is None or m.group(2).lower() in nr["units"]):
        v = int(m.group(1).replace(nr["thousands_sep"], ""))
        if expected_text:
            return v, None, None
        return v, ("unit_text" if m.group(2) else "text_number"), "strip_unit"
    return None, "unreadable", None


def outlier_stats(recs):
    """Median dan MAD per (stasiun, ukuran, metrik) dari seluruh nilai numerik."""
    g = defaultdict(list)
    for r in recs:
        if r["value"] is not None:
            g[(r["station"], r["size"], r["metric"])].append(r["value"])
    out = {}
    for k, v in g.items():
        med = statistics.median(v)
        out[k] = (med, statistics.median(abs(x - med) for x in v))
    return out


def flag_outliers(recs, stats, rules):
    ro = rules["outlier"]
    floor = {"produced": ro["min_scale_produced"], "reject": ro["min_scale_reject"]}
    for r in recs:
        r["z"] = 0.0
        if r["value"] is None:
            continue
        med, mad = stats[(r["station"], r["size"], r["metric"])]
        r["z"] = abs(r["value"] - med) / max(1.4826 * mad, floor[r["metric"]])
        r["suspect"] = r["z"] > ro["robust_z"]
