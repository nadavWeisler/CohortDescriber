"""Module defining a count metric for cohort description."""

from __future__ import annotations
import polars as pl

from .registry import register_metric, MetricExpr


def count_metric(spec: dict) -> MetricExpr:
    """Count the number of rows in the cohort."""
    return spec["name"], pl.len()


register_metric("count", count_metric)
