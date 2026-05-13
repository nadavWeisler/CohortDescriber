"""Check row-count thresholds."""

from __future__ import annotations

import polars as pl

from .registry import register_check, CheckContext, CheckResult


def _validate_row_count_check(spec: dict) -> None:
    if "min" not in spec and "max" not in spec:
        raise ValueError("row_count check requires at least one of 'min' or 'max'")
    if "min" in spec:
        try:
            int(spec["min"])
        except (TypeError, ValueError) as exc:
            raise ValueError("row_count check requires integer-like 'min'") from exc
    if "max" in spec:
        try:
            int(spec["max"])
        except (TypeError, ValueError) as exc:
            raise ValueError("row_count check requires integer-like 'max'") from exc


def check_row_count(df: pl.DataFrame, spec: dict, context: CheckContext) -> CheckResult:
    """Check that row count falls within configured thresholds."""
    del context
    n_rows = df.height
    min_rows = int(spec["min"]) if "min" in spec else None
    max_rows = int(spec["max"]) if "max" in spec else None
    passed = (min_rows is None or n_rows >= min_rows) and (
        max_rows is None or n_rows <= max_rows
    )
    return (
        "row_count",
        passed,
        {"n_rows": n_rows, "min": min_rows, "max": max_rows},
    )


register_check(
    "row_count",
    check_row_count,
    validator=_validate_row_count_check,
)
