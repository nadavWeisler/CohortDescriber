"""Check that values are drawn from an allowed set."""

from __future__ import annotations

import polars as pl

from .registry import register_check, CheckContext, CheckResult


def _validate_accepted_values_check(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError("accepted_values check requires a non-empty 'column'")
    values = spec["values"]
    if not isinstance(values, list) or not values:
        raise ValueError("accepted_values check requires a non-empty list in 'values'")


def check_accepted_values(
    df: pl.DataFrame, spec: dict, _context: CheckContext
) -> CheckResult:
    """Check whether non-null values in a column are contained in an allowed set."""
    column = spec["column"]
    values = spec["values"]
    allow_null = bool(spec.get("allow_null", True))

    expr = ~pl.col(column).is_in(values)
    if allow_null:
        expr = expr & pl.col(column).is_not_null()

    invalid_rows = df.filter(expr)
    invalid_count = invalid_rows.height
    sample = invalid_rows.select(column).head(5)[column].to_list() if invalid_count else []
    return (
        f"accepted_values:{column}",
        invalid_count == 0,
        {
            "column": column,
            "allowed_values": values,
            "invalid_count": invalid_count,
            "invalid_examples": sample,
        },
    )


register_check(
    "accepted_values",
    check_accepted_values,
    required_keys=("column", "values"),
    validator=_validate_accepted_values_check,
)
