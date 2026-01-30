from cohort_describer.duckdb import DuckDBDB
from cohort_describer.config import load_config
from cohort_describer.report import generate_report

cfg = load_config("config/describer.yml")
db = DuckDBDB("cohort.duckdb")

run_id = "r1"  # or None for latest
generate_report(db, table=cfg.table, out_path="report.md", run_id=run_id)

print("Wrote report.md")