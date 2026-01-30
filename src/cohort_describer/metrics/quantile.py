"""Module defining a quantile metric for cohort description."""

from __future__ import annotations
import polars as pl

from .registry import register_metric, MetricExpr


def quantile_metric(spec: dict) -> MetricExpr:
    """Calculate the quantile of a specified column."""
    col = spec["column"]
    q = float(spec["q"])
    return spec["name"], pl.col(col).quantile(q)


register_metric("quantile", quantile_metric)
