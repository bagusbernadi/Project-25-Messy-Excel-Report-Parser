"""Pembungkus worksheet (merged cell diisi ke seluruh area, baris tersembunyi) dan pembaca tanggal."""
import re
from datetime import date, datetime

_TOK = {"%d": r"(?P<d>\d{1,2})", "%m": r"(?P<m>\d{1,2})", "%Y": r"(?P<Y>\d{4})", "%y": r"(?P<y>\d{2})", "%b": r"(?P<b>[A-Za-z]{3})"}


class Grid:
    def __init__(self, ws):
        self.ws = ws
        self.max_row, self.max_col = ws.max_row, ws.max_column
        self.merged = {}
        for rng in ws.merged_cells.ranges:
            v = ws.cell(rng.min_row, rng.min_col).value
            for r in range(rng.min_row, rng.max_row + 1):
                for c in range(rng.min_col, rng.max_col + 1):
                    self.merged[(r, c)] = v
        self.hidden = {r for r, d in ws.row_dimensions.items() if d.hidden}

    def v(self, r, c, fill=False):
        if fill and (r, c) in self.merged:
            return self.merged[(r, c)]
        return self.ws.cell(r, c).value


def parse_date(v, formats, months):
    """Nilai sel -> date, atau None bila bukan tanggal. Format memakai token %d %m %Y %y %b."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if v is None:
        return None
    s = str(v).strip()
    for f in formats:
        rx = "".join(_TOK.get(p, re.escape(p)) for p in re.split(r"(%[dmYyb])", f))
        m = re.fullmatch(rx, s)
        if not m:
            continue
        g = m.groupdict()
        year = int(g["Y"]) if g.get("Y") else 2000 + int(g["y"])
        mon = int(g["m"]) if g.get("m") else months.get(g["b"].casefold())
        if mon is None:
            continue
        return date(year, mon, int(g["d"]))
    return None
