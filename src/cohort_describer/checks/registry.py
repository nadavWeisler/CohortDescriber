"""Registry for row-level checks."""

from __future__ import annotations
from typing import Callable, Any
import polars as pl

CheckResult = tuple[str, bool, dict[str, Any]]
CheckFn = Callable[[pl.DataFrame, dict], CheckResult]

CHECKS: dict[str, CheckFn] = {}


def register_check(name: str, fn: CheckFn) -> None:
    """Register a new check."""
    if name in CHECKS:
        raise KeyError(f"Check '{name}' already registered")
    CHECKS[name] = fn


def run_check(df: pl.DataFrame, spec: dict) -> CheckResult:
    """Run a registered check."""
    t = spec["type"]
    fn = CHECKS.get(t)
    if fn is None:
        raise ValueError(f"Unknown check type: {t}. Known: {sorted(CHECKS)}")
    return fn(df, spec)
