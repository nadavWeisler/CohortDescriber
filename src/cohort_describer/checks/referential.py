"""Check that values exist in a reference table."""

from __future__ import annotations

import polars as pl

from cohort_describer.utils import quote_identifier

from .registry import register_check, CheckContext, CheckResult


def _validate_referential_check(spec: dict) -> None:
    for key in ("column", "ref_table", "ref_column"):
        if not isinstance(spec[key], str) or not spec[key]:
            raise ValueError(f"referential check requires a non-empty '{key}'")


def check_referential(
    df: pl.DataFrame, spec: dict, context: CheckContext
) -> CheckResult:
    """Check whether source values are present in a reference table column."""
    if context.db is None:
        raise ValueError("referential check requires database context")

    column = spec["column"]
    ref_table = quote_identifier(spec["ref_table"])
    ref_column = quote_identifier(spec["ref_column"])

    ref_df = context.db.read_df(f"SELECT DISTINCT {ref_column} AS ref_value FROM {ref_table}")
    ref_values = set(ref_df["ref_value"].to_list()) if ref_df.height else set()

    invalid_rows = df.filter(pl.col(column).is_not_null() & ~pl.col(column).is_in(ref_values))
    invalid_count = invalid_rows.height
    examples = invalid_rows.select(column).head(5)[column].to_list() if invalid_count else []
    return (
        f"referential:{column}->{spec['ref_table']}.{spec['ref_column']}",
        invalid_count == 0,
        {
            "column": column,
            "ref_table": spec["ref_table"],
            "ref_column": spec["ref_column"],
            "invalid_count": invalid_count,
            "invalid_examples": examples,
        },
    )


register_check(
    "referential",
    check_referential,
    required_keys=("column", "ref_table", "ref_column"),
    validator=_validate_referential_check,
)
