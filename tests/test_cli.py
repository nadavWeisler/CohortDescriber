"""End-to-end CLI smoke tests."""

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from cohort_describer.cli import app
from cohort_describer.duckdb import DuckDBDB

RUNNER = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_all_generates_database_and_report_artifacts(tmp_path: Path):
    input_path = tmp_path / "customers.csv"
    config_path = tmp_path / "describer.yml"
    db_path = tmp_path / "cohort.duckdb"
    output_base = tmp_path / "report"

    pl.DataFrame(
        {
            "id": ["a", "a", "b", "c"],
            "marketing_sector": ["retail", "finance", "gaming", "retail"],
            "value": [10.0, 5.0, 8.0, 2.0],
        }
    ).write_csv(input_path)

    config_path.write_text(
        """
table_prefix: raw_input
id_col: id
group_by:
  - marketing_sector
ingest:
  dtypes:
    value: float
metrics:
  - name: n
    type: count
  - name: distinct_ids
    type: n_unique
    column: id
  - name: total_value
    type: sum
    column: value
checks:
  - type: unique
    cols: [id]
  - type: accepted_values
    column: marketing_sector
    values: [retail, finance]
  - type: row_count
    min: 3
""".strip(),
        encoding="utf-8",
    )

    result = RUNNER.invoke(
        app,
        [
            "all",
            str(input_path),
            "--config-path",
            str(config_path),
            "--db-path",
            str(db_path),
            "--schema-path",
            str(REPO_ROOT / "sql" / "schema.sql"),
            "--run-id",
            "r1",
            "--output-base",
            str(output_base),
            "--formats",
            "md,json,csv",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report_metrics.csv").exists()
    assert (tmp_path / "report_grouped_metrics.csv").exists()
    assert (tmp_path / "report_failed_checks.csv").exists()

    report_md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "## Cohort slices" in report_md
    assert "## Metric trends" in report_md
    assert "## Per-column summary" in report_md

    db = DuckDBDB(str(db_path))
    try:
        metrics = db.read_df('SELECT * FROM "dataset_metrics" WHERE run_id = ?', ["r1"])
        grouped = db.read_df('SELECT * FROM "dataset_metric_groups" WHERE run_id = ?', ["r1"])
        checks = db.read_df('SELECT * FROM "checks" WHERE run_id = ?', ["r1"])
    finally:
        db.close()

    assert metrics.height == 3
    assert grouped.height > 0
    assert checks.height == 3
