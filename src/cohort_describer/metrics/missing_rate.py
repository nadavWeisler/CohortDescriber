"""Module defining a missing rate metric for cohort description."""

from __future__ import annotations
import polars as pl

from .registry import register_metric, MetricExpr


def _validate_missing_rate_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")


def missing_rate_metric(spec: dict) -> MetricExpr:
    """Calculate the missing rate of a specified column."""
    col = spec["column"]
    return spec["name"], pl.col(col).is_null().mean()


register_metric(
    "missing_rate",
    missing_rate_metric,
    required_keys=("column",),
    validator=_validate_missing_rate_metric,
)
