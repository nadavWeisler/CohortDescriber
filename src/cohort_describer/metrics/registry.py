"""Registry for metrics."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any
import polars as pl

MetricExpr = tuple[str, pl.Expr]          # (metric_name, aggregation_expr)
MetricFn = Callable[[dict[str, Any]], MetricExpr]
MetricValidator = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class MetricRegistration:
    """Registered metric definition."""

    fn: MetricFn
    required_keys: tuple[str, ...]
    validator: MetricValidator | None = None


METRICS: dict[str, MetricRegistration] = {}


def register_metric(
    name: str,
    fn: MetricFn,
    *,
    required_keys: tuple[str, ...] = (),
    validator: MetricValidator | None = None,
) -> None:
    """Register a new metric."""
    if name in METRICS:
        raise KeyError(f"Metric '{name}' already registered")
    METRICS[name] = MetricRegistration(
        fn=fn,
        required_keys=required_keys,
        validator=validator,
    )


def validate_metric_spec(spec: dict[str, Any]) -> None:
    """Validate a metric config entry."""
    if not isinstance(spec, dict):
        raise ValueError(f"Metric spec must be a dict, got {type(spec).__name__}")

    name = spec.get("name")
    metric_type = spec.get("type")
    if not isinstance(name, str) or not name:
        raise ValueError(f"Metric spec must include a non-empty 'name': {spec!r}")
    if not isinstance(metric_type, str) or not metric_type:
        raise ValueError(f"Metric '{name}' must include a non-empty 'type'")

    registration = METRICS.get(metric_type)
    if registration is None:
        raise ValueError(f"Unknown metric type: {metric_type}. Known: {sorted(METRICS)}")

    missing = [key for key in registration.required_keys if key not in spec]
    if missing:
        raise ValueError(f"Metric '{name}' missing required keys: {missing}")

    if registration.validator is not None:
        registration.validator(spec)


def metric_expr(spec: dict[str, Any]) -> MetricExpr:
    """Get the metric expression for a registered metric."""
    validate_metric_spec(spec)
    return METRICS[spec["type"]].fn(spec)
