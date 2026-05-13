"""Ingest data into DuckDB for cohort describer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import polars as pl

from cohort_describer.duckdb import DuckDBDB
from cohort_describer.utils import raw_table_name, validate_safe_token


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


def _validate_columns_exist(df: pl.DataFrame, cols: list[str], field_name: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValueError(f"{field_name} references missing columns: {missing}")


def ingest(db: DuckDBDB, input_path: str, cfg, spec: IngestSpec) -> tuple[str, int]:
    """Ingest data from a file into DuckDB according to the config and spec."""
    validate_safe_token(spec.run_id, "run_id")

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = _read_any(str(path))

    ingest_cfg = cfg.ingest or {}
    mapping = ingest_cfg.get("mapping", {}) or {}
    dtypes = ingest_cfg.get("dtypes", {}) or {}
    date_cols = ingest_cfg.get("date_columns", []) or []

    if mapping:
        _validate_columns_exist(df, list(mapping.keys()), "ingest.mapping")
        df = df.rename(mapping)

    required_columns = [cfg.id_col, *date_cols, *dtypes.keys(), *(cfg.group_by or [])]
    _validate_columns_exist(
        df,
        list(dict.fromkeys(required_columns)),
        "config after applying ingest.mapping",
    )

    if cfg.id_col not in df.columns:
        raise ValueError(
            f"Missing id_col '{cfg.id_col}' after mapping. Columns: {df.columns}"
        )

    for c in date_cols:
        try:
            df = df.with_columns(pl.col(c).cast(pl.Date, strict=False))
        except Exception as exc:  # pragma: no cover - polars error type varies
            raise ValueError(f"Failed to cast date column {c!r}: {exc}") from exc

    for col, typ in dtypes.items():
        pl_type = _POLARS_DTYPES.get(str(typ).lower())
        if pl_type is None:
            raise ValueError(f"Unknown dtype in config: {typ} (col={col})")
        try:
            df = df.with_columns(pl.col(col).cast(pl_type, strict=False))
        except Exception as exc:  # pragma: no cover - polars error type varies
            raise ValueError(
                f"Failed to cast column {col!r} to dtype {typ!r}: {exc}"
            ) from exc

    df = df.with_columns(pl.lit(spec.run_id).alias("run_id"))

    raw_table = raw_table_name(cfg.table_prefix, spec.run_id)
    db.write_df(df, raw_table, mode="replace")

    db.execute('DELETE FROM "dataset_runs" WHERE run_id = ?', [spec.run_id])
    db.write_df(
        pl.DataFrame(
            [
                {
                    "run_id": spec.run_id,
                    "dataset_name": spec.dataset_name or raw_table,
                    "created_at": datetime.now(),
                    "source": spec.source,
                }
            ]
        ),
        "dataset_runs",
        mode="append",
    )

    return raw_table, df.height
