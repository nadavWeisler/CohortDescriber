"""Module defining a quantile metric for cohort description."""

from __future__ import annotations
import polars as pl

from .registry import register_metric, MetricExpr


def _validate_quantile_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")
    q = float(spec["q"])
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"Metric '{spec['name']}' q must be between 0 and 1")


def quantile_metric(spec: dict) -> MetricExpr:
    """Calculate the quantile of a specified column."""
    col = spec["column"]
    q = float(spec["q"])
    return spec["name"], pl.col(col).quantile(q)


register_metric(
    "quantile",
    quantile_metric,
    required_keys=("column", "q"),
    validator=_validate_quantile_metric,
)
