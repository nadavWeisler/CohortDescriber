"""Check for missing value rate in a specified column of the DataFrame."""

from __future__ import annotations
import polars as pl

from .registry import register_check, CheckResult


def check_missing_rate(df: pl.DataFrame, spec: dict) -> CheckResult:
    """
    Check for missing value rate in a specified column of the DataFrame.
    Args:
        df: The DataFrame to check.
        spec: The specification of the check to run.
    Returns:
        A tuple of (check_name, passed: bool, details: dict)
    """
    col = spec["column"]
    max_rate = float(spec["max"])
    null_rate = df.select(pl.col(col).is_null().mean()).item()
    passed = null_rate <= max_rate
    return (
        f"missing_rate_max:{col}",
        passed,
        {"column": col, "null_rate": float(null_rate), "max": max_rate},
    )


register_check("missing_rate", check_missing_rate)
