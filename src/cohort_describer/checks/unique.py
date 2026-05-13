"""Check for uniqueness of one or more columns."""

from __future__ import annotations

import polars as pl

from .registry import register_check, CheckContext, CheckResult


def _validate_unique_check(spec: dict) -> None:
    cols = spec["cols"]
    if not isinstance(cols, list) or not cols or not all(isinstance(c, str) and c for c in cols):
        raise ValueError("unique check requires a non-empty list[str] in 'cols'")


def check_unique(df: pl.DataFrame, spec: dict, _context: CheckContext) -> CheckResult:
    """Check that a combination of columns is unique."""
    cols = spec["cols"]
    duplicates = df.group_by(cols).len().filter(pl.col("len") > 1)
    duplicate_groups = duplicates.height
    duplicate_rows = int(duplicates["len"].sum() - duplicate_groups) if duplicate_groups else 0
    return (
        f"unique:{','.join(cols)}",
        duplicate_groups == 0,
        {
            "cols": cols,
            "duplicate_groups": duplicate_groups,
            "duplicate_rows": duplicate_rows,
        },
    )


register_check(
    "unique",
    check_unique,
    required_keys=("cols",),
    validator=_validate_unique_check,
)
