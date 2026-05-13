"""Module defining a mean metric for cohort description."""

from __future__ import annotations
import polars as pl

from .registry import register_metric, MetricExpr


def _validate_mean_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")


def mean_metric(spec: dict) -> MetricExpr:
    """Calculate the mean of a specified column."""
    col = spec["column"]
    return spec["name"], pl.col(col).mean()


register_metric(
    "mean",
    mean_metric,
    required_keys=("column",),
    validator=_validate_mean_metric,
)
