# Cara memakai

Dari root repo:

```
pip install -r project/requirements.txt
python project/code/1-data-preparation/python/01_generate_reports.py   # membuat 36 laporan simulasi (sekitar 1 menit)
python project/code/1-data-preparation/python/02_layout_taxonomy.py
python project/code/1-data-preparation/python/03_parse_all.py          # parse: fact, anomaly_log, reconciliation
python project/code/1-data-preparation/python/04_build_db.py           # parsed.duckdb
for f in project/code/2-analysis/python/0[5-9]_*.py project/code/2-analysis/python/1[0-3]_*.py; do python $f; done
python project/code/3-presentation/python/14_build_dashboard_data.py
python project/code/3-presentation/python/15_build_onesheet.py
python project/code/3-presentation/python/16_build_notebook.py
python project/code/3-presentation/python/17_build_docs.py
streamlit run project/code/3-presentation/streamlit/app.py
python -m pytest project/tests -q
```

Memparse satu laporan sendiri:

```python
import sys; sys.path[:0] = ["project/code", "project/code/1-data-preparation/python"]
import common as C
from parser import load_lookup, load_rules, load_templates, parse_files
out = parse_files(["laporan_saya.xlsx"], load_templates(C.TEMPLATES_DIR), load_lookup(C.LOOKUP), load_rules(C.RULES))
out["fact"], out["anomaly"], out["reconciliation"]
```

Bila layout laporan belum punya config, parser berhenti dengan `UnknownTemplate`. Cara menambah template: `add_new_template.md`.
