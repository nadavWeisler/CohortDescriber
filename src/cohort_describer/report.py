"""Generate reports from cohort description runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import polars as pl

from cohort_describer.duckdb import DuckDBDB
from cohort_describer.utils import quote_identifier


def _md_table(df: pl.DataFrame, max_rows: int = 50) -> str:
    """Render a Polars DataFrame as a simple Markdown table."""
    if df.height == 0:
        return "_(no rows)_\n"

    df2 = df.head(max_rows)
    cols = df2.columns
    rows = df2.rows()

    str_rows = [[("" if v is None else str(v)) for v in r] for r in rows]

    widths = [len(c) for c in cols]
    for r in str_rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(vals: list[str]) -> str:
        return "| " + " | ".join(
            vals[i].ljust(widths[i]) for i in range(len(cols))
        ) + " |"

    header = fmt_row(cols)
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(cols))) + " |"
    body = "\n".join(fmt_row(r) for r in str_rows)

    more = ""
    if df.height > max_rows:
        more = f"\n\n_(showing first {max_rows} of {df.height} rows)_\n"

    return header + "\n" + sep + "\n" + body + more + "\n"


def _column_summary(df: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for col, dtype in df.schema.items():
        series = df[col]
        rows.append(
            {
                "column": col,
                "dtype": str(dtype),
                "null_count": int(series.null_count()),
                "null_rate": float(series.is_null().mean() or 0.0),
                "n_unique": int(series.n_unique()),
            }
        )
    return pl.DataFrame(rows).sort("column") if rows else pl.DataFrame()


def _prepare_failed_checks(failed: pl.DataFrame) -> pl.DataFrame:
    if failed.height == 0:
        return failed

    def _format_json_details(value: str) -> str:
        try:
            return json.dumps(json.loads(value), ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return value

    return failed.with_columns(
        pl.col("details_json")
        .map_elements(_format_json_details, return_dtype=pl.Utf8)
        .alias("details")
    ).drop("details_json")


def _prepare_trends(trends: pl.DataFrame) -> pl.DataFrame:
    if trends.height == 0:
        return trends
    previous = trends.group_by("metric").agg(
        pl.col("value")
        .sort_by("created_at", descending=True)
        .slice(1, 1)
        .first()
        .alias("previous_value")
    )
    current = trends.group_by("metric").agg(
        pl.col("value")
        .sort_by("created_at", descending=True)
        .first()
        .alias("current_value"),
        pl.col("created_at").max().alias("latest_run_at"),
    )
    return (
        current.join(previous, on="metric", how="left")
        .with_columns(
            (pl.col("current_value") - pl.col("previous_value")).alias("delta")
        )
        .sort("metric")
    )


def _collect_report_data(
    db: DuckDBDB, raw_table: str, run_id: str
) -> dict[str, pl.DataFrame | str | int]:
    raw_table_name = quote_identifier(raw_table)
    raw_df = db.read_df(f"SELECT * FROM {raw_table_name} WHERE run_id = ?", [run_id])
    metrics = db.read_df(
        'SELECT metric, value, n FROM "dataset_metrics" WHERE run_id = ? ORDER BY metric',
        [run_id],
    )
    grouped = db.read_df(
        'SELECT group_name, group_value, metric, value, n FROM "dataset_metric_groups" '
        "WHERE run_id = ? ORDER BY group_name, group_value, metric",
        [run_id],
    )
    failed = db.read_df(
        'SELECT check_name, details_json FROM "checks" WHERE run_id = ? AND passed = 0 ORDER BY check_name',
        [run_id],
    )
    checks_summary = db.read_df(
        'SELECT '
        "SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) AS passed, "
        "SUM(CASE WHEN passed = 0 THEN 1 ELSE 0 END) AS failed "
        'FROM "checks" WHERE run_id = ?',
        [run_id],
    ).fill_null(0)
    trends_raw = db.read_df(
        'SELECT m.metric, m.value, r.created_at '
        'FROM "dataset_metrics" m '
        'JOIN "dataset_runs" r ON r.run_id = m.run_id '
        "WHERE m.metric IN (SELECT metric FROM \"dataset_metrics\" WHERE run_id = ?) "
        "ORDER BY r.created_at DESC",
        [run_id],
    )
    latest_run = db.read_df(
        'SELECT dataset_name, created_at, source FROM "dataset_runs" WHERE run_id = ?',
        [run_id],
    )

    return {
        "run_id": run_id,
        "row_count": raw_df.height,
        "raw_table": raw_table,
        "run_meta": latest_run,
        "metrics": metrics,
        "grouped_metrics": grouped,
        "failed_checks": _prepare_failed_checks(failed),
        "checks_summary": checks_summary,
        "column_summary": (
            _column_summary(raw_df.drop("run_id"))
            if "run_id" in raw_df.columns
            else _column_summary(raw_df)
        ),
        "metric_trends": _prepare_trends(trends_raw),
    }


def _write_markdown(path: Path, report_data: dict[str, pl.DataFrame | str | int]) -> None:
    md = [
        "# Dataset Report\n\n",
        f"**run_id:** `{report_data['run_id']}`  \n",
        f"**raw table:** `{report_data['raw_table']}`  \n",
        f"**rows in run:** `{report_data['row_count']}`  \n\n",
    ]

    run_meta = report_data["run_meta"]
    if isinstance(run_meta, pl.DataFrame) and run_meta.height > 0:
        md.append("## Run metadata\n\n")
        md.append(_md_table(run_meta))

    md.append("## Checks summary\n\n")
    md.append(_md_table(report_data["checks_summary"]))

    md.append("## Top issues\n\n")
    md.append(_md_table(report_data["failed_checks"]))

    md.append("## Dataset metrics\n\n")
    md.append(_md_table(report_data["metrics"]))

    md.append("## Cohort slices\n\n")
    md.append(_md_table(report_data["grouped_metrics"]))

    md.append("## Metric trends\n\n")
    md.append(_md_table(report_data["metric_trends"]))

    md.append("## Per-column summary\n\n")
    md.append(_md_table(report_data["column_summary"]))

    path.write_text("".join(md), encoding="utf-8")


def _write_json(path: Path, report_data: dict[str, pl.DataFrame | str | int]) -> None:
    payload = {
        key: value.to_dicts() if isinstance(value, pl.DataFrame) else value
        for key, value in report_data.items()
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _write_csv(base_path: Path, report_data: dict[str, pl.DataFrame | str | int]) -> None:
    for key in (
        "metrics",
        "grouped_metrics",
        "failed_checks",
        "checks_summary",
        "metric_trends",
        "column_summary",
    ):
        value = report_data[key]
        if isinstance(value, pl.DataFrame):
            value.write_csv(base_path.with_name(f"{base_path.name}_{key}.csv"))


def generate_report(
    db: DuckDBDB,
    raw_table: str,
    out_base: str = "report",
    run_id: str | None = None,
    formats: Iterable[str] = ("md",),
) -> dict[str, pl.DataFrame | str | int]:
    """Generate report artifacts for a given run_id (defaults to latest run)."""
    if run_id is None:
        latest = db.read_df(
            'SELECT run_id FROM "dataset_runs" ORDER BY created_at DESC LIMIT 1'
        )
        if latest.height == 0:
            Path(f"{out_base}.md").write_text(
                "# Dataset Report\n\n_No runs found in dataset_runs._\n",
                encoding="utf-8",
            )
            return {"run_id": "", "row_count": 0, "raw_table": raw_table}
        run_id = latest["run_id"][0]

    report_data = _collect_report_data(db, raw_table=raw_table, run_id=run_id)
    base_path = Path(out_base)
    normalized_formats = {fmt.lower().lstrip(".") for fmt in formats}

    if "md" in normalized_formats:
        _write_markdown(base_path.with_suffix(".md"), report_data)
    if "json" in normalized_formats:
        _write_json(base_path.with_suffix(".json"), report_data)
    if "csv" in normalized_formats:
        _write_csv(base_path, report_data)

    return report_data
