"""Load and validate pipeline configuration from YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cohort_describer.checks import validate_check_spec
from cohort_describer.metrics import validate_metric_spec
from cohort_describer.utils import validate_safe_token

_ALLOWED_DTYPES = {"int", "float", "str", "date", "datetime", "bool"}


@dataclass(frozen=True)
class Config:
    """Configuration for cohort description."""

    table_prefix: str
    id_col: str
    metrics: list[dict[str, Any]]
    ingest: dict[str, Any]
    checks: list[dict[str, Any]]
    group_by: list[str]


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _validate_ingest(ingest: Any) -> dict[str, Any]:
    if ingest in (None, {}):
        return {}
    if not isinstance(ingest, dict):
        raise ValueError("ingest must be a mapping when provided")

    mapping = ingest.get("mapping", {}) or {}
    if not isinstance(mapping, dict):
        raise ValueError("ingest.mapping must be a mapping")
    for src, dst in mapping.items():
        _require_non_empty_string(src, "ingest.mapping keys")
        _require_non_empty_string(dst, "ingest.mapping values")

    date_columns = ingest.get("date_columns", []) or []
    if not isinstance(date_columns, list) or not all(
        isinstance(col, str) and col for col in date_columns
    ):
        raise ValueError("ingest.date_columns must be a list of non-empty strings")

    dtypes = ingest.get("dtypes", {}) or {}
    if not isinstance(dtypes, dict):
        raise ValueError("ingest.dtypes must be a mapping")
    for col, dtype in dtypes.items():
        _require_non_empty_string(col, "ingest.dtypes keys")
        dtype_name = _require_non_empty_string(dtype, f"ingest.dtypes[{col}]")
        if dtype_name.lower() not in _ALLOWED_DTYPES:
            raise ValueError(
                f"Unsupported ingest dtype {dtype_name!r} for column {col!r}; "
                f"allowed: {sorted(_ALLOWED_DTYPES)}"
            )

    return {
        "mapping": mapping,
        "date_columns": date_columns,
        "dtypes": dtypes,
    }


def _validate_group_by(group_by: Any) -> list[str]:
    if group_by in (None, []):
        return []
    if not isinstance(group_by, list) or not all(
        isinstance(col, str) and col for col in group_by
    ):
        raise ValueError("group_by must be a list of non-empty strings")
    return group_by


def load_config(path: str = "config/describer.yml") -> Config:
    """Load configuration from a YAML file."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Configuration file must define a YAML mapping")

    for key in ("table_prefix", "id_col", "metrics"):
        if key not in data:
            raise ValueError(f"Missing config key: {key}")

    table_prefix = validate_safe_token(
        _require_non_empty_string(data["table_prefix"], "table_prefix"),
        "table_prefix",
    )
    id_col = _require_non_empty_string(data["id_col"], "id_col")

    metrics = data["metrics"]
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("metrics must be a non-empty list")
    for spec in metrics:
        validate_metric_spec(spec)

    checks = data.get("checks", []) or []
    if not isinstance(checks, list):
        raise ValueError("checks must be a list when provided")
    for spec in checks:
        validate_check_spec(spec)

    return Config(
        table_prefix=table_prefix,
        id_col=id_col,
        metrics=metrics,
        ingest=_validate_ingest(data.get("ingest", {})),
        checks=checks,
        group_by=_validate_group_by(data.get("group_by", [])),
    )
