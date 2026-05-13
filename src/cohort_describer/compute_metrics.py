"""Compute and store metrics in DuckDB."""

from __future__ import annotations

import polars as pl

from cohort_describer.duckdb import DuckDBDB
from cohort_describer.metrics import metric_expr
from cohort_describer.utils import quote_identifier


def _validate_metric_columns(df: pl.DataFrame, cfg) -> None:
    missing = sorted(
        {
            spec["column"]
            for spec in (cfg.metrics or [])
            if "column" in spec and spec["column"] not in df.columns
        }
    )
    if missing:
        raise ValueError(f"Metrics reference missing columns: {missing}")


def compute_metrics_df(df: pl.DataFrame, cfg) -> pl.DataFrame:
    """Compute metrics as specified in the config and return as a DataFrame."""
    _validate_metric_columns(df, cfg)
    agg_pairs = [metric_expr(m) for m in (cfg.metrics or [])]
    metric_names = [name for name, _ in agg_pairs]
    agg_exprs = [expr.alias(name) for name, expr in agg_pairs]

    n = df.height
    one = df.select(agg_exprs)

    return (
        one.unpivot(on=metric_names, variable_name="metric", value_name="value")
        .with_columns(
            pl.lit(n).alias("n"),
            pl.col("value").cast(pl.Float64, strict=False).alias("value"),
        )
        .select(["metric", "value", "n"])
    )


def compute_grouped_metrics_df(df: pl.DataFrame, cfg) -> pl.DataFrame:
    """Compute grouped metrics for configured cohort slice columns."""
    group_cols = cfg.group_by or []
    if not group_cols:
        return pl.DataFrame(
            schema={
                "group_name": pl.Utf8,
                "group_value": pl.Utf8,
                "metric": pl.Utf8,
                "value": pl.Float64,
                "n": pl.Int64,
            }
        )

    missing = [col for col in group_cols if col not in df.columns]
    if missing:
        raise ValueError(f"group_by references missing columns: {missing}")

    frames: list[pl.DataFrame] = []
    for group_col in group_cols:
        for metric_name, expr in [metric_expr(spec) for spec in cfg.metrics]:
            grouped = (
                df.group_by(group_col)
                .agg(
                    expr.alias("value"),
                    pl.len().alias("n"),
                )
                .with_columns(
                    pl.lit(group_col).alias("group_name"),
                    pl.col(group_col)
                    .cast(pl.Utf8, strict=False)
                    .fill_null("(null)")
                    .alias("group_value"),
                    pl.lit(metric_name).alias("metric"),
                    pl.col("value").cast(pl.Float64, strict=False).alias("value"),
                )
                .select(["group_name", "group_value", "metric", "value", "n"])
            )
            frames.append(grouped)

    return pl.concat(frames, how="vertical") if frames else pl.DataFrame()


def compute_metrics_to_db(db: DuckDBDB, run_id: str, raw_table: str, cfg) -> int:
    """Compute metrics and store results in DuckDB."""
    df = db.read_df(f"SELECT * FROM {quote_identifier(raw_table)}")
    out = compute_metrics_df(df, cfg).with_columns(pl.lit(run_id).alias("run_id"))

    db.execute('DELETE FROM "dataset_metrics" WHERE run_id = ?', [run_id])
    db.write_df(
        out.select(["run_id", "metric", "value", "n"]),
        "dataset_metrics",
        mode="append",
    )

    grouped = compute_grouped_metrics_df(df, cfg)
    db.execute('DELETE FROM "dataset_metric_groups" WHERE run_id = ?', [run_id])
    if grouped.height > 0:
        db.write_df(
            grouped.with_columns(pl.lit(run_id).alias("run_id")).select(
                ["run_id", "group_name", "group_value", "metric", "value", "n"]
            ),
            "dataset_metric_groups",
            mode="append",
        )

    return out.height
