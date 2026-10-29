"""Tahap 2 / langkah 12 (Q15, Q6): semua kejadian yang sengaja ditanam terdeteksi? Plus pemeriksaan kecocokan template, kunci unik, dan determinisme."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_lib import C, KEY, load_fact, load_truth_long  # noqa: E402
from methods_lib import load_lookup, load_rules, load_templates, parse_files  # noqa: E402

gt = json.loads(C.GROUND_TRUTH.read_text(encoding="utf-8"))
fact = load_fact()
a = pd.read_csv(C.RES_PREP / "anomaly_log.csv")
planted = pd.read_csv(C.RES_ANALYSIS / "planted_cells_effective.csv")
fl = pd.read_csv(C.RES_PREP / "file_summary.csv")
rows = []

# fakta 1: enam template dikenali, satu per layout
fl["layout_from_name"] = fl.source_file.str.extract(r"_G(\d)_")[0].astype(int)
ok1 = int((fl.layout == fl.layout_from_name).sum())
rows.append((1, "Enam layout dikenali", "file yang cocok dengan layout aslinya", 36, ok1, "template dipilih otomatis dari isi sel, bukan dari nama file"))
# fakta 2: perubahan layout bulan ke-4 (layout 1 dan 3)
ch = fl[fl.layout.isin([1, 3])].copy()
ch["month"] = ch.source_file.str.extract(r"_(\d{4}-\d{2})")[0]
ch["expect"] = [f"L{l}_v2" if m >= "2026-06" else f"L{l}_v1" for l, m in zip(ch.layout, ch.month)]
rows.append((2, "Perubahan layout bulan ke-4", "file layout 1 dan 3 memakai config yang benar", len(ch), int((ch.template == ch.expect).sum()), "bulan 1-3: config v1; bulan 4-6: config v2"))
# fakta 3: subtotal salah ketik
typ = planted[planted.problem == "subtotal_typo"]
found = int(typ.caught.sum())
rows.append((3, "Subtotal salah ketik", "subtotal salah yang tercatat sebagai subtotal_mismatch", len(typ), found, "keduanya di layout 2"))
# fakta 4: sheet ganda
dup = planted[planted.problem == "duplicate_sheet"]
dd = a[(a.issue_type == "duplicate_sheet") & (a.action == "dropped")]
rows.append((4, "Sheet ganda", "sheet ganda yang dibuang", len(dup), len(dd), "dikenali dari nama salinan dan kemiripan isi"))
# fakta 5: sel kotor, per jenis
for kind, label in (("text_na", "teks 'n/a'"), ("dash", "tanda '-'"), ("x10", "angka kali 10"), ("unit_text", "angka dengan satuan"), ("blank", "sel kosong")):
    k = planted[planted.problem == kind]
    rows.append((5, f"Sel kotor: {label}", "sel yang benar-benar berubah di file dan tercatat", int(k.effective.sum()), int((k.effective & k.caught).sum()),
                 "tidak ada yang berubah: pembuat data tidak benar-benar mengosongkan sel" if kind == "blank" else ""))
val = pd.DataFrame(rows, columns=["fact_id", "fact", "check", "planted", "detected", "note"])
val["recall"] = val.detected / val.planted.where(val.planted > 0)
val.to_csv(C.RES_ANALYSIS / "validation_planted.csv", index=False)

# false positive: catatan anomali yang tidak ada di daftar sel yang ditanam
k_all = set(planted.file + "|" + planted.sheet + "|" + planted.cell.fillna(""))
fp = a[~(a.source_file + "|" + a.sheet + "|" + a.cell.fillna("")).isin(k_all)]

t = load_truth_long()
chk = []
n = len(fact)
chk.append(("Q4", "Jumlah sel hasil parsing = jumlah sel kunci jawaban", len(t), n))
dupe = int(fact.duplicated(KEY).sum())
chk.append(("Q4", "Tidak ada kunci ganda (tanggal, shift, slot, stasiun, ukuran, metrik)", n, n - dupe))
miss = len(t.merge(fact[KEY], on=KEY, how="left", indicator=True).query("_merge == 'left_only'"))
chk.append(("Q4", "Setiap sel kunci jawaban ada di hasil parsing", len(t), len(t) - miss))
chk.append(("Q15", "Anomali tercatat yang bukan sel yang ditanam (positif palsu)", len(a), len(a) - len(fp)))
tpl = load_templates(C.TEMPLATES_DIR)
import openpyxl  # noqa: E402
from parser.config import matches  # noqa: E402
amb = sum(1 for p in sorted(C.REPORTS_DIR.glob("*.xlsx")) if sum(matches(openpyxl.load_workbook(p), c) for c in tpl) != 1)
chk.append(("Q6", "Setiap file cocok dengan tepat satu template", 36, 36 - amb))
files = sorted(C.REPORTS_DIR.glob("*.xlsx"))
h = lambda o: hashlib.sha256(o["fact"].astype(str).to_csv(index=False).encode()).hexdigest()  # noqa: E731
r1, r2 = (parse_files(files, tpl, load_lookup(C.LOOKUP), load_rules(C.RULES)) for _ in range(2))
chk.append(("Q6", "Parsing dua kali menghasilkan tabel tidy identik (SHA-256)", 1, int(h(r1) == h(r2))))
bad = int((fact[fact.quality.isin(["ok", "fixed"])].merge(t, on=KEY).eval("value != truth")).sum())
chk.append(("Q4", "Sel berstatus ok atau fixed yang berbeda dari kunci jawaban", int(fact.quality.isin(["ok", "fixed"]).sum()), int(fact.quality.isin(["ok", "fixed"]).sum()) - bad))
vc = pd.DataFrame(chk, columns=["question", "check", "n_tested", "n_pass"])
vc["result"] = ["lulus" if r.n_tested == r.n_pass else "gagal" for r in vc.itertuples()]
vc.to_csv(C.RES_ANALYSIS / "validation_checks.csv", index=False)
print(val.to_string(index=False)); print(vc.to_string(index=False)); print(len(fp), "positif palsu")
assert (vc.result == "lulus").all()
