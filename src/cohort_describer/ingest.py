""" "Ingest data into DuckDB for cohort describer."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import polars as pl

from cohort_describer.duckdb import DuckDBDB
from cohort_describer.utils import raw_table_name


@dataclass(frozen=True)
class IngestSpec:
    """Specification for a data ingestion run."""

    run_id: str
    dataset_name: str = ""
    source: str = ""


_POLARS_DTYPES = {
    "int": pl.Int64,
    "float": pl.Float64,
    "str": pl.Utf8,
    "date": pl.Date,
    "datetime": pl.Datetime,
    "bool": pl.Boolean,
}


def _read_any(path: str) -> pl.DataFrame:
    """Read a CSV or Parquet file into a Polars DataFrame."""
    p = path.lower()
    if p.endswith(".parquet"):
        return pl.read_parquet(path)
    return pl.read_csv(path, try_parse_dates=True)


def ingest(db: DuckDBDB, input_path: str, cfg, spec: IngestSpec) -> tuple[str, int]:
    """Ingest data from a file into DuckDB according to the config and spec."""

    df = _read_any(input_path)

    ingest_cfg = cfg.ingest or {}
    mapping = ingest_cfg.get("mapping", {}) or {}
    dtypes = ingest_cfg.get("dtypes", {}) or {}
    date_cols = ingest_cfg.get("date_columns", []) or []

    if mapping:
        rename_map = {src: dst for src, dst in mapping.items() if src in df.columns}
        if rename_map:
            df = df.rename(rename_map)

    if cfg.id_col not in df.columns:
        raise ValueError(
            f"Missing id_col '{cfg.id_col}' after mapping. Columns: {df.columns}"
        )

    for c in date_cols:
        if c in df.columns:
            df = df.with_columns(pl.col(c).cast(pl.Date, strict=False))

    for col, typ in dtypes.items():
        if col in df.columns:
            pl_type = _POLARS_DTYPES.get(str(typ).lower())
            if pl_type is None:
                raise ValueError(f"Unknown dtype in config: {typ} (col={col})")
            df = df.with_columns(pl.col(col).cast(pl_type, strict=False))

    df = df.with_columns(pl.lit(spec.run_id).alias("run_id"))

    raw_table = raw_table_name(cfg.table_prefix, spec.run_id)

    db.write_df(df, raw_table, mode="replace")

    db.execute(f"DELETE FROM dataset_runs WHERE run_id='{spec.run_id}'")
    db.execute(
        "INSERT INTO dataset_runs(run_id, dataset_name, created_at, source) "
        f"VALUES ('{spec.run_id}', '{spec.dataset_name or raw_table}', '{datetime.now().isoformat(timespec='seconds')}', '{spec.source}')"
    )

    return raw_table, df.height
