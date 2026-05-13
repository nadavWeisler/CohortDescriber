"""Compute and store checks results in DuckDB."""

from __future__ import annotations

import json

import polars as pl

from cohort_describer.checks import CheckContext, run_check
from cohort_describer.duckdb import DuckDBDB
from cohort_describer.utils import quote_identifier


def _validate_check_columns(df: pl.DataFrame, cfg) -> None:
    missing = sorted(
        {
            col
            for spec in (cfg.checks or [])
            for key in ("column",)
            if key in spec
            for col in [spec[key]]
            if col not in df.columns
        }
        | {
            col
            for spec in (cfg.checks or [])
            if "cols" in spec
            for col in spec["cols"]
            if col not in df.columns
        }
    )
    if missing:
        raise ValueError(f"Checks reference missing columns: {missing}")


def run_checks_to_db(db: DuckDBDB, run_id: str, raw_table: str, cfg) -> int:
    """Run checks and store results in DuckDB."""
    df = db.read_df(f"SELECT * FROM {quote_identifier(raw_table)}")
    _validate_check_columns(df, cfg)

    rows: list[dict] = []
    context = CheckContext(db=db, raw_table=raw_table)
    for spec in cfg.checks or []:
        name, passed, details = run_check(df, spec, context)
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

    out = (
        pl.DataFrame(rows)
        if rows
        else pl.DataFrame(
            schema={
                "run_id": pl.Utf8,
                "check_name": pl.Utf8,
                "passed": pl.Int64,
                "details_json": pl.Utf8,
            }
        )
    )
    db.execute('DELETE FROM "checks" WHERE run_id = ?', [run_id])
    if out.height > 0:
        db.write_df(out, "checks", mode="append")
    return out.height
