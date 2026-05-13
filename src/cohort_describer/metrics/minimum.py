"""Module defining a minimum metric."""

from __future__ import annotations

import polars as pl

from .registry import register_metric, MetricExpr


def _validate_min_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")


def min_metric(spec: dict) -> MetricExpr:
    """Calculate the minimum of a specified column."""
    return spec["name"], pl.col(spec["column"]).min()


register_metric(
    "min",
    min_metric,
    required_keys=("column",),
    validator=_validate_min_metric,
)
