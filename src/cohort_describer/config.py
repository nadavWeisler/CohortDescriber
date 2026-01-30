"""Module to load configuration from a YAML file."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

@dataclass(frozen=True)
class Config:
    """Configuration for cohort description."""
    table_prefix: str
    id_col: str
    metrics: list[dict[str, Any]]
    ingest: dict[str, Any]
    checks: list[dict[str, Any]]

def load_config(path: str = "config/describer.yml") -> Config:
    """Load configuration from a YAML file."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    for k in ("table_prefix", "id_col", "metrics"):
        if k not in data:
            raise ValueError(f"Missing config key: {k}")

    return Config(
        table_prefix=data["table_prefix"],
        id_col=data["id_col"],
        metrics=data["metrics"],
        ingest=data.get("ingest", {}) or {},
        checks=data.get("checks", []) or [],
    )
