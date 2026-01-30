from cohort_describer.duckdb import DuckDBDB
from cohort_describer.config import load_config
from cohort_describer.compute_metrics import compute_metrics_to_db

cfg = load_config("config/describer.yml")
db = DuckDBDB("cohort.duckdb")

run_id = "r1"

rows = compute_metrics_to_db(db, run_id=run_id, cfg=cfg)
print("metric rows written:", rows)
print(db.read_df(f"SELECT * FROM dataset_metrics WHERE run_id='{run_id}' ORDER BY metric"))