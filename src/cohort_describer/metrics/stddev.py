"""Module defining a standard deviation metric."""

from __future__ import annotations

import polars as pl

from .registry import register_metric, MetricExpr


def _validate_std_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")


def std_metric(spec: dict) -> MetricExpr:
    """Calculate the standard deviation of a specified column."""
    return spec["name"], pl.col(spec["column"]).std()


register_metric(
    "stddev",
    std_metric,
    required_keys=("column",),
    validator=_validate_std_metric,
)
