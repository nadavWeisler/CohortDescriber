"""Module defining a distinct-count metric."""

from __future__ import annotations

import polars as pl

from .registry import register_metric, MetricExpr


def _validate_n_unique_metric(spec: dict) -> None:
    if not isinstance(spec["column"], str) or not spec["column"]:
        raise ValueError(f"Metric '{spec['name']}' must include a non-empty 'column'")


def n_unique_metric(spec: dict) -> MetricExpr:
    """Count distinct values in a column."""
    return spec["name"], pl.col(spec["column"]).n_unique()


register_metric(
    "n_unique",
    n_unique_metric,
    required_keys=("column",),
    validator=_validate_n_unique_metric,
)
