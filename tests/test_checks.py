"""Tests for check execution."""

from pathlib import Path

import polars as pl

from cohort_describer.checks import CheckContext, run_check
from cohort_describer.duckdb import DuckDBDB


def test_checks_support_new_builtins():
    df = pl.DataFrame(
        {
            "id": ["a", "a", "b"],
            "segment": ["retail", "finance", "invalid"],
        }
    )

    unique_name, unique_passed, unique_details = run_check(
        df, {"type": "unique", "cols": ["id"]}, CheckContext()
    )
    assert unique_name == "unique:id"
    assert not unique_passed
    assert unique_details["duplicate_groups"] == 1

    accepted_name, accepted_passed, accepted_details = run_check(
        df,
        {
            "type": "accepted_values",
            "column": "segment",
            "values": ["retail", "finance"],
        },
        CheckContext(),
    )
    assert accepted_name == "accepted_values:segment"
    assert not accepted_passed
    assert accepted_details["invalid_count"] == 1

    row_count_name, row_count_passed, row_count_details = run_check(
        df, {"type": "row_count", "min": 2, "max": 3}, CheckContext()
    )
    assert row_count_name == "row_count"
    assert row_count_passed
    assert row_count_details["n_rows"] == 3


def test_referential_check_uses_reference_table(tmp_path: Path):
    db_path = tmp_path / "test.duckdb"
    db = DuckDBDB(str(db_path))
    try:
        db.write_df(pl.DataFrame({"allowed": ["retail", "finance"]}), "allowed_segments", mode="replace")
        df = pl.DataFrame({"segment": ["retail", "invalid"]})

        name, passed, details = run_check(
            df,
            {
                "type": "referential",
                "column": "segment",
                "ref_table": "allowed_segments",
                "ref_column": "allowed",
            },
            CheckContext(db=db, raw_table="raw_input__r1"),
        )
    finally:
        db.close()

    assert name == "referential:segment->allowed_segments.allowed"
    assert not passed
    assert details["invalid_count"] == 1
