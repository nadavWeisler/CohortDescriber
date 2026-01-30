"""Compute and store metrics in DuckDB."""
from __future__ import annotations
import polars as pl

from cohort_describer.duckdb import DuckDBDB
from cohort_describer.metrics import metric_expr

def compute_metrics_df(df: pl.DataFrame, cfg) -> pl.DataFrame:
    """Compute metrics as specified in the config and return as a DataFrame."""
    agg_pairs = [metric_expr(m) for m in (cfg.metrics or [])]
    metric_names = [name for name, _ in agg_pairs]
    agg_exprs = [expr.alias(name) for name, expr in agg_pairs]

    n = df.height
    one = df.select(agg_exprs)

    out = one.unpivot(on=metric_names, variable_name="metric", value_name="value").with_columns(
        pl.lit(n).alias("n"),
        pl.col("value").cast(pl.Float64, strict=False).alias("value"),
    ).select(["metric", "value", "n"])
    return out

def compute_metrics_to_db(db: DuckDBDB, run_id: str, raw_table: str, cfg) -> int:
    """Compute metrics and store results in DuckDB."""
    df = db.read_df(f"SELECT * FROM {raw_table}")
    out = compute_metrics_df(df, cfg).with_columns(pl.lit(run_id).alias("run_id"))

    db.execute(f"DELETE FROM dataset_metrics WHERE run_id='{run_id}'")
    db.write_df(out.select(["run_id", "metric", "value", "n"]), "dataset_metrics", mode="append")
    return out.height
