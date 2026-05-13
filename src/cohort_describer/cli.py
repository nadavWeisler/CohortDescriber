"""CLI entrypoint for Cohort Describer."""

from __future__ import annotations

from typing import Annotated

import typer

from cohort_describer.pipeline import (
    checks_step,
    init_db,
    ingest_step,
    metrics_step,
    report_step,
    run_all,
)

app = typer.Typer(add_completion=False, help="Run cohort description workflows.")


def _parse_formats(value: str) -> list[str]:
    formats = [part.strip().lower() for part in value.split(",") if part.strip()]
    if not formats:
        raise typer.BadParameter("At least one output format is required")
    return formats


@app.command("init")
def init_command(
    db_path: Annotated[str, typer.Option("--db-path")] = "cohort.duckdb",
    schema_path: Annotated[str, typer.Option("--schema-path")] = "sql/schema.sql",
) -> None:
    """Initialize the DuckDB schema."""
    db = init_db(db_path=db_path, schema_path=schema_path)
    db.close()
    typer.echo(f"Initialized database at {db_path}")


@app.command("ingest")
def ingest_command(
    input_path: Annotated[str, typer.Argument(help="Input CSV or Parquet path")],
    config_path: Annotated[str, typer.Option("--config-path")] = "config/describer.yml",
    db_path: Annotated[str, typer.Option("--db-path")] = "cohort.duckdb",
    schema_path: Annotated[str, typer.Option("--schema-path")] = "sql/schema.sql",
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    dataset_name: Annotated[str | None, typer.Option("--dataset-name")] = None,
    source: Annotated[str, typer.Option("--source")] = "local",
) -> None:
    """Ingest a dataset into DuckDB."""
    resolved_run_id, raw_table, row_count = ingest_step(
        input_path,
        config_path=config_path,
        db_path=db_path,
        schema_path=schema_path,
        run_id=run_id,
        dataset_name=dataset_name,
        source=source,
    )
    typer.echo(f"OK: run_id={resolved_run_id}, rows={row_count}, raw_table={raw_table}")


@app.command("metrics")
def metrics_command(
    run_id: Annotated[str, typer.Argument(help="Run ID to compute metrics for")] = "r1",
    config_path: Annotated[str, typer.Option("--config-path")] = "config/describer.yml",
    db_path: Annotated[str, typer.Option("--db-path")] = "cohort.duckdb",
    schema_path: Annotated[str, typer.Option("--schema-path")] = "sql/schema.sql",
) -> None:
    """Compute configured metrics."""
    rows = metrics_step(
        config_path=config_path,
        db_path=db_path,
        schema_path=schema_path,
        run_id=run_id,
    )
    typer.echo(f"metric rows written: {rows}")


@app.command("checks")
def checks_command(
    run_id: Annotated[str, typer.Argument(help="Run ID to execute checks for")] = "r1",
    config_path: Annotated[str, typer.Option("--config-path")] = "config/describer.yml",
    db_path: Annotated[str, typer.Option("--db-path")] = "cohort.duckdb",
    schema_path: Annotated[str, typer.Option("--schema-path")] = "sql/schema.sql",
) -> None:
    """Run configured checks."""
    rows = checks_step(
        config_path=config_path,
        db_path=db_path,
        schema_path=schema_path,
        run_id=run_id,
    )
    typer.echo(f"checks written: {rows}")


@app.command("report")
def report_command(
    run_id: Annotated[str, typer.Argument(help="Run ID to build a report for")] = "r1",
    config_path: Annotated[str, typer.Option("--config-path")] = "config/describer.yml",
    db_path: Annotated[str, typer.Option("--db-path")] = "cohort.duckdb",
    schema_path: Annotated[str, typer.Option("--schema-path")] = "sql/schema.sql",
    output_base: Annotated[str, typer.Option("--output-base")] = "report",
    formats: Annotated[str, typer.Option("--formats")] = "md",
) -> None:
    """Generate report outputs."""
    report_step(
        config_path=config_path,
        db_path=db_path,
        schema_path=schema_path,
        run_id=run_id,
        out_base=output_base,
        formats=_parse_formats(formats),
    )
    typer.echo(f"Wrote report artifacts with base path {output_base}")


@app.command("all")
def all_command(
    input_path: Annotated[str, typer.Argument(help="Input CSV or Parquet path")],
    config_path: Annotated[str, typer.Option("--config-path")] = "config/describer.yml",
    db_path: Annotated[str, typer.Option("--db-path")] = "cohort.duckdb",
    schema_path: Annotated[str, typer.Option("--schema-path")] = "sql/schema.sql",
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    dataset_name: Annotated[str | None, typer.Option("--dataset-name")] = None,
    source: Annotated[str, typer.Option("--source")] = "local",
    output_base: Annotated[str, typer.Option("--output-base")] = "report",
    formats: Annotated[str, typer.Option("--formats")] = "md",
) -> None:
    """Run the full ingest → metrics → checks → report pipeline."""
    resolved_run_id, raw_table, row_count = run_all(
        input_path,
        config_path=config_path,
        db_path=db_path,
        schema_path=schema_path,
        run_id=run_id,
        dataset_name=dataset_name,
        source=source,
        out_base=output_base,
        formats=_parse_formats(formats),
    )
    typer.echo(f"OK: run_id={resolved_run_id}, rows={row_count}, raw_table={raw_table}")


def main() -> None:
    """Console entrypoint."""
    app()


if __name__ == "__main__":
    main()
