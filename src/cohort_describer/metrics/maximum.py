"""Module defining a maximum metric."""

from __future__ import annotations

import polars as pl

from .registry import register_metric, MetricExpr


def _validate_max_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")


def max_metric(spec: dict) -> MetricExpr:
    """Calculate the maximum of a specified column."""
    return spec["name"], pl.col(spec["column"]).max()


register_metric(
    "max",
    max_metric,
    required_keys=("column",),
    validator=_validate_max_metric,
)
