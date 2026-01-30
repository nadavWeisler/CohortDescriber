"""Compute and store checks results in DuckDB."""

from __future__ import annotations
import json
import polars as pl

from cohort_describer.checks import run_check
from cohort_describer.duckdb import DuckDBDB


def run_checks_to_db(db: DuckDBDB, run_id: str, raw_table: str, cfg) -> int:
    """Run checks and store results in DuckDB."""

    df = db.read_df(f"SELECT * FROM {raw_table}")

    rows: list[dict] = []
    for spec in cfg.checks or []:
        name, passed, details = run_check(df, spec)
        rows.append(
            {
                "run_id": run_id,
                "check_name": name,
                "passed": 1 if passed else 0,
                "details_json": json.dumps(
                    details, separators=(",", ":"), ensure_ascii=False
                ),
            }
        )

    out = pl.DataFrame(rows)
    db.execute(f"DELETE FROM checks WHERE run_id='{run_id}'")
    if out.height > 0:
        db.write_df(out, "checks", mode="append")
    return out.height
