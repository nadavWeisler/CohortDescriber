"""Ingest data into DuckDB for cohort describer."""

from cohort_describer.duckdb import DuckDBDB
from cohort_describer.config import load_config
from cohort_describer.ingest import ingest, IngestSpec

cfg = load_config("config/describer.yml")
db = DuckDBDB("cohort.duckdb")
db.execute_file("sql/schema.sql")

run_id = "r1"
input_path = "data/customers_test.csv"  # or your file

raw_table, n = ingest(
    db=db,
    input_path=input_path,
    cfg=cfg,
    spec=IngestSpec(run_id=run_id, dataset_name=input_path, source="local"),
)

print("ingested rows:", (raw_table, n))
print(db.read_df(f"SELECT run_id, COUNT(*) AS n FROM {raw_table} GROUP BY run_id"))
print(db.read_df("SELECT * FROM dataset_runs ORDER BY created_at DESC LIMIT 5"))