"""Reusable pipeline helpers for scripts and CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from cohort_describer.compute_checks import run_checks_to_db
from cohort_describer.compute_metrics import compute_metrics_to_db
from cohort_describer.config import Config, load_config
from cohort_describer.duckdb import DuckDBDB
from cohort_describer.ingest import IngestSpec, ingest
from cohort_describer.report import generate_report
from cohort_describer.run_id import make_run_id
from cohort_describer.utils import raw_table_name, validate_safe_token


def init_db(db_path: str = "cohort.duckdb", schema_path: str = "sql/schema.sql") -> DuckDBDB:
    """Open the database and ensure the schema exists."""
    db = DuckDBDB(db_path)
    db.execute_file(schema_path)
    return db


def load_pipeline_config(config_path: str = "config/describer.yml") -> Config:
    """Load the validated pipeline config."""
    return load_config(config_path)


def resolve_run_id(run_id: str | None, prefix: str = "run") -> str:
    """Resolve or generate a safe run ID."""
    resolved = run_id or make_run_id(prefix)
    return validate_safe_token(resolved, "run_id")


def ingest_step(
    input_path: str,
    *,
    config_path: str = "config/describer.yml",
    db_path: str = "cohort.duckdb",
    schema_path: str = "sql/schema.sql",
    run_id: str | None = None,
    dataset_name: str | None = None,
    source: str = "local",
) -> tuple[str, str, int]:
    """Run ingest and return the resolved run ID, table, and row count."""
    cfg = load_pipeline_config(config_path)
    db = init_db(db_path, schema_path)
    resolved_run_id = resolve_run_id(run_id, Path(input_path).stem.replace("-", "_"))
    try:
        raw_table, row_count = ingest(
            db,
            input_path,
            cfg,
            IngestSpec(
                run_id=resolved_run_id,
                dataset_name=dataset_name or input_path,
                source=source,
            ),
        )
    finally:
        db.close()
    return resolved_run_id, raw_table, row_count


def metrics_step(
    *,
    config_path: str = "config/describer.yml",
    db_path: str = "cohort.duckdb",
    schema_path: str = "sql/schema.sql",
    run_id: str = "r1",
) -> int:
    """Run metrics for a known run ID."""
    cfg = load_pipeline_config(config_path)
    db = init_db(db_path, schema_path)
    try:
        return compute_metrics_to_db(db, run_id, raw_table_name(cfg.table_prefix, run_id), cfg)
    finally:
        db.close()


def checks_step(
    *,
    config_path: str = "config/describer.yml",
    db_path: str = "cohort.duckdb",
    schema_path: str = "sql/schema.sql",
    run_id: str = "r1",
) -> int:
    """Run checks for a known run ID."""
    cfg = load_pipeline_config(config_path)
    db = init_db(db_path, schema_path)
    try:
        return run_checks_to_db(db, run_id, raw_table_name(cfg.table_prefix, run_id), cfg)
    finally:
        db.close()


def report_step(
    *,
    config_path: str = "config/describer.yml",
    db_path: str = "cohort.duckdb",
    schema_path: str = "sql/schema.sql",
    run_id: str = "r1",
    out_base: str = "report",
    formats: Iterable[str] = ("md",),
):
    """Generate report artifacts for a known run ID."""
    cfg = load_pipeline_config(config_path)
    db = init_db(db_path, schema_path)
    try:
        return generate_report(
            db,
            raw_table=raw_table_name(cfg.table_prefix, run_id),
            out_base=out_base,
            run_id=run_id,
            formats=formats,
        )
    finally:
        db.close()


def run_all(
    input_path: str,
    *,
    config_path: str = "config/describer.yml",
    db_path: str = "cohort.duckdb",
    schema_path: str = "sql/schema.sql",
    run_id: str | None = None,
    dataset_name: str | None = None,
    source: str = "local",
    out_base: str = "report",
    formats: Iterable[str] = ("md",),
) -> tuple[str, str, int]:
    """Run ingest, metrics, checks, and reporting end to end."""
    cfg = load_pipeline_config(config_path)
    db = init_db(db_path, schema_path)
    resolved_run_id = resolve_run_id(run_id, Path(input_path).stem.replace("-", "_"))

    try:
        raw_table, row_count = ingest(
            db,
            input_path,
            cfg,
            IngestSpec(
                run_id=resolved_run_id,
                dataset_name=dataset_name or input_path,
                source=source,
            ),
        )
        compute_metrics_to_db(db, resolved_run_id, raw_table, cfg)
        run_checks_to_db(db, resolved_run_id, raw_table, cfg)
        generate_report(
            db,
            raw_table=raw_table,
            out_base=out_base,
            run_id=resolved_run_id,
            formats=formats,
        )
    finally:
        db.close()

    return resolved_run_id, raw_table, row_count
