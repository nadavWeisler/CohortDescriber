"""Registry for row-level checks."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Any
import polars as pl

if TYPE_CHECKING:
    from cohort_describer.duckdb import DuckDBDB

CheckResult = tuple[str, bool, dict[str, Any]]
CheckValidator = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class CheckContext:
    """Context available to checks that need database access."""

    db: DuckDBDB | None = None
    raw_table: str | None = None


CheckFn = Callable[[pl.DataFrame, dict, CheckContext], CheckResult]


@dataclass(frozen=True)
class CheckRegistration:
    """Registered check definition."""

    fn: CheckFn
    required_keys: tuple[str, ...]
    validator: CheckValidator | None = None


CHECKS: dict[str, CheckRegistration] = {}


def register_check(
    name: str,
    fn: CheckFn,
    *,
    required_keys: tuple[str, ...] = (),
    validator: CheckValidator | None = None,
) -> None:
    """Register a new check."""
    if name in CHECKS:
        raise KeyError(f"Check '{name}' already registered")
    CHECKS[name] = CheckRegistration(
        fn=fn,
        required_keys=required_keys,
        validator=validator,
    )


def validate_check_spec(spec: dict[str, Any]) -> None:
    """Validate a check config entry."""
    if not isinstance(spec, dict):
        raise ValueError(f"Check spec must be a dict, got {type(spec).__name__}")

    check_type = spec.get("type")
    if not isinstance(check_type, str) or not check_type:
        raise ValueError(f"Check spec must include a non-empty 'type': {spec!r}")

    registration = CHECKS.get(check_type)
    if registration is None:
        raise ValueError(f"Unknown check type: {check_type}. Known: {sorted(CHECKS)}")

    missing = [key for key in registration.required_keys if key not in spec]
    if missing:
        raise ValueError(f"Check '{check_type}' missing required keys: {missing}")

    if registration.validator is not None:
        registration.validator(spec)


def run_check(
    df: pl.DataFrame, spec: dict, context: CheckContext | None = None
) -> CheckResult:
    """Run a registered check."""
    validate_check_spec(spec)
    return CHECKS[spec["type"]].fn(df, spec, context or CheckContext())
