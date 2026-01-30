"""Check for duplicate rows based on specified columns."""

from __future__ import annotations
import polars as pl

from .registry import register_check, CheckResult


def check_duplicates(df: pl.DataFrame, spec: dict) -> CheckResult:
    """
    Check for duplicate rows based on specified columns.

    Args:
        df (pl.DataFrame): The DataFrame to check for duplicates.
        spec (dict): The specification of the check to run.

    Returns:
        CheckResult: A tuple containing the check name, a boolean indicating if the check passed, and a dictionary with details.
    """
    cols = spec["cols"]
    n_rows = df.height
    n_unique = df.select(pl.struct(cols).n_unique()).item()
    n_dupes = n_rows - n_unique
    return (
        f"duplicates:{','.join(cols)}",
        n_dupes == 0,
        {"n_rows": n_rows, "n_unique": n_unique, "n_dupes": n_dupes, "cols": cols},
    )


register_check("duplicates", check_duplicates)
