"""Pengaturan bersama semua skrip Project 25. Semua jalur relatif terhadap folder project/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # folder project/
DATA = ROOT / "data"
SIM_DIR = DATA / "sim"                                 # laporan simulasi + kunci jawaban (tidak di-commit; dibuat ulang oleh generator)
REPORTS_DIR = SIM_DIR / "reports"
TRUTH_CSV = SIM_DIR / "truth_fact_output_tidy.csv"
DIRTY_CSV = SIM_DIR / "ground_truth_dirty_cells.csv"
GROUND_TRUTH = SIM_DIR / "ground_truth.json"
PARSED_DIR = DATA / "parsed"                           # tabel tidy hasil parsing (tidak di-commit; dibuat ulang)
SAMPLES_DIR = DATA / "samples"                         # 6 laporan contoh (bulan pertama tiap layout), di-commit
DB_PATH = ROOT / "parsed.duckdb"
CODE = ROOT / "code"
SQL_PREP = CODE / "1-data-preparation" / "sql"
SQL_ANALYSIS = CODE / "2-analysis" / "sql"
CONFIG_DIR = ROOT / "config"
TEMPLATES_DIR = CONFIG_DIR / "templates"
LOOKUP = CONFIG_DIR / "lookup.yaml"
RULES = CONFIG_DIR / "parser_rules.yaml"
METHODS_DIR = ROOT / "methods"
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANALYSIS = ROOT / "results" / "2-analysis"
RES_PRESENT = ROOT / "results" / "3-presentation"
DOCS_DIR = ROOT / "docs"
for _d in (SIM_DIR, PARSED_DIR, RES_PREP, RES_ANALYSIS, RES_PRESENT, METHODS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SEED = 25260302
DATA_VERSION = "v1"
DATA_DATE = "2026-10-28"
ANALYSIS_DATE = "2026-10-29"
N_FILES = 36
METRICS = ["produced", "reject"]

# asumsi dampak waktu (estimated, tidak diukur dengan stopwatch)
REPORTS_PER_MONTH = 6          # asumsi: 6 laporan bulanan (satu per kelompok stasiun)
COPYPASTE_MIN_PER_REPORT = 30  # asumsi: menit copy-paste dan pengecekan per laporan
MONTHS_PER_YEAR = 12


def load_sql(path):
    """Baca file .sql berisi blok '-- name: nama' menjadi dict nama -> query."""
    out, name, buf = {}, None, []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name:"):
            if name:
                out[name] = "\n".join(buf).strip().rstrip(";")
            name, buf = line.split(":", 1)[1].strip(), []
        elif name is not None:
            buf.append(line)
    if name:
        out[name] = "\n".join(buf).strip().rstrip(";")
    return out


def result(name):
    """Cari CSV hasil di folder hasil per tahap."""
    for d in (RES_PREP, RES_ANALYSIS, RES_PRESENT):
        p = d / name
        if p.exists():
            return p
    raise FileNotFoundError(name)


def chdir_root():
    os.chdir(ROOT)
