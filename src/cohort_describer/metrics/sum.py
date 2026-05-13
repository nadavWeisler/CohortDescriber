"""Module defining a sum metric."""

from __future__ import annotations

import polars as pl

from .registry import register_metric, MetricExpr


def _validate_sum_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")


def sum_metric(spec: dict) -> MetricExpr:
    """Calculate the sum of a specified column."""
    return spec["name"], pl.col(spec["column"]).sum()


register_metric(
    "sum",
    sum_metric,
    required_keys=("column",),
    validator=_validate_sum_metric,
)
