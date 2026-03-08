"""Run the full dataset describer pipeline end to end."""

from cohort_describer.duckdb import DuckDBDB
from cohort_describer.config import load_config
from cohort_describer.ingest import ingest, IngestSpec
from cohort_describer.compute_metrics import compute_metrics_to_db
from cohort_describer.compute_checks import run_checks_to_db
from cohort_describer.report import generate_report
from cohort_describer.run_id import make_run_id

cfg = load_config("config/describer.yml")
db = DuckDBDB("cohort.duckdb")
db.execute_file("sql/schema.sql")

INPUT_PATH = "data/customers_test.csv"
run_id = make_run_id("customers")

raw_table, n = ingest(
    db,
    INPUT_PATH,
    cfg,
    IngestSpec(run_id=run_id, dataset_name=INPUT_PATH, source="local"),
)

compute_metrics_to_db(db, run_id, raw_table, cfg)
run_checks_to_db(db, run_id, raw_table, cfg)
generate_report(db, out_path="report.md", run_id=run_id, table=raw_table)

print(f"OK: run_id={run_id}, rows={n}, raw_table={raw_table}")
