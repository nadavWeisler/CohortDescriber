"""Registry for metrics."""

from __future__ import annotations
from typing import Callable, Any
import polars as pl

MetricExpr = tuple[str, pl.Expr]          # (metric_name, aggregation_expr)
MetricFn = Callable[[dict[str, Any]], MetricExpr]

METRICS: dict[str, MetricFn] = {}

def register_metric(name: str, fn: MetricFn) -> None:
    """Register a new metric."""
    if name in METRICS:
        raise KeyError(f"Metric '{name}' already registered")
    METRICS[name] = fn

def metric_expr(spec: dict[str, Any]) -> MetricExpr:
    """Get the metric expression for a registered metric."""
    t = spec["type"]
    fn = METRICS.get(t)
    if fn is None:
        raise ValueError(f"Unknown metric type: {t}. Known: {sorted(METRICS)}")
    return fn(spec)