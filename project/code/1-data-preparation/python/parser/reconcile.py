"""Rekonsiliasi: cocokkan jumlah hasil parsing dengan subtotal laporan, lalu pulihkan sel yang bisa dipastikan.

Aturan pemulihan (urut):
1. Satu sel bermasalah (kosong, tidak terbaca, atau mencurigakan) dalam satu subtotal: nilainya = subtotal - jumlah sel lain.
2. Tidak ada sel bermasalah tetapi selisih tepat 9/10 dari satu sel yang berukuran 10 kali wajar (tanda angka berlebih nol): sel itu dibagi 10.
3. Selain itu selisih dicatat; tidak ada angka yang ditebak.
"""
from .clean import clean_value


def _bad(m):
    return m["value"] is None or m["suspect"]


def reconcile(recs, cons, rules):
    """Mengubah recs di tempat (value, suspect, fixed_by, issue) dan mengisi cons (parsed_raw, parsed_final, status, resolution)."""
    for i, c in enumerate(cons):
        c["id"] = i
        c["report_total"] = clean_value(c["report_raw"], rules)[0]
        c["parsed_raw"] = sum(recs[j]["value"] for j in c["members"] if recs[j]["value"] is not None)
        c["n_bad_raw"] = sum(1 for j in c["members"] if _bad(recs[j]))
    changed = True
    while changed:
        changed = False
        for c in cons:
            if c["report_total"] is None:
                continue
            mem = [recs[j] for j in c["members"]]
            bad = [m for m in mem if _bad(m)]
            good = sum(m["value"] for m in mem if not _bad(m))
            if len(bad) == 1:
                b, v = bad[0], c["report_total"] - good
                if v < 0:
                    continue
                if b["value"] == v:                           # dugaan outlier ternyata benar (subtotal membenarkan)
                    b["suspect"], b["cleared"] = False, True
                    changed = True
                elif b["value"] is None or b["suspect"]:
                    b["value"], b["suspect"], b["fixed_by"] = v, False, c["id"]
                    changed = True
            elif not bad:
                diff = sum(m["value"] for m in mem) - c["report_total"]
                cand = [m for m in mem if diff > 0 and 9 * m["value"] == 10 * diff and m["z"] > 3]
                if len(cand) == 1:
                    cand[0].update(value=cand[0]["value"] // 10, issue="x10", fixed_by=c["id"])
                    changed = True
    for c in cons:
        mem = [recs[j] for j in c["members"]]
        c["parsed_final"] = sum(m["value"] for m in mem if m["value"] is not None)
        n_bad = sum(1 for m in mem if _bad(m))
        rt = c["report_total"]
        c["diff_raw"] = None if rt is None else c["parsed_raw"] - rt
        c["diff_final"] = None if rt is None or n_bad else c["parsed_final"] - rt
        c["status_raw"] = "tidak terbaca" if rt is None else "cocok" if c["diff_raw"] == 0 and not c["n_bad_raw"] else "selisih"
        if c["status_raw"] == "cocok":
            c["resolution"] = "cocok"
        elif any(m.get("fixed_by") == c["id"] for m in mem):
            c["resolution"] = "dipulihkan dari subtotal ini"
        elif c["diff_final"] == 0:
            c["resolution"] = "dipulihkan lewat subtotal lain"
        elif n_bad:
            c["resolution"] = "selisih: sel bermasalah belum bisa dipastikan"
        else:
            c["resolution"] = "selisih: subtotal dicurigai"
        c["status_final"] = "cocok" if c["diff_final"] == 0 else "selisih"
    return cons
