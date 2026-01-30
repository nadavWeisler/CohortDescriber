from cohort_describer.duckdb import DuckDBDB
from cohort_describer.config import load_config
from cohort_describer.checks import run_checks_to_db

cfg = load_config("config/describer.yml")
db = DuckDBDB("cohort.duckdb")

run_id = "r1"

n = run_checks_to_db(db, run_id=run_id, cfg=cfg)
print("checks written:", n)
print(db.read_df(f"SELECT * FROM checks WHERE run_id='{run_id}' ORDER BY check_name"))
