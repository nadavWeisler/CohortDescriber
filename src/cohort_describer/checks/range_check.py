"""Check for values within a specified range in a column of the DataFrame."""

from __future__ import annotations
import polars as pl

from .registry import register_check, CheckResult


def check_range(df: pl.DataFrame, spec: dict) -> CheckResult:
    """Check that all values in a specified column are within a given range."""

    col = spec["column"]
    lo = spec.get("min", None)
    hi = spec.get("max", None)

    expr = pl.lit(True)
    if lo is not None:
        expr = expr & (pl.col(col) >= lo)
    if hi is not None:
        expr = expr & (pl.col(col) <= hi)

    out_of_range = df.select((~expr).mean()).item()
    passed = out_of_range == 0.0
    return (
        f"range:{col}",
        passed,
        {
            "column": col,
            "min": lo,
            "max": hi,
            "out_of_range_rate": float(out_of_range),
        },
    )


register_check("range", check_range)
