"""Minimal DuckDB helper for this project."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence
import duckdb
import polars as pl

from cohort_describer.utils import quote_identifier


class DuckDBDB:
    """
    Minimal DuckDB helper for this project.

    - execute(sql): run SQL (no return)
    - execute_file(path): run a .sql file
    - write_df(df, table, mode): append or replace from a Polars DataFrame
    - read_df(sql): run query and return Polars DataFrame
    """

    def __init__(self, path: str = "cohort.duckdb"):
        self.path = path
        self.con = duckdb.connect(path)

    def close(self) -> None:
        """Close the database connection."""
        self.con.close()

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> None:
        """Execute a SQL statement."""
        if params is None:
            self.con.execute(sql)
        else:
            self.con.execute(sql, params)

    def execute_file(self, path: str) -> None:
        """Execute SQL statements from a .sql file."""
        sql = Path(path).read_text(encoding="utf-8")
        self.con.execute(sql)

    def write_df(self, df: pl.DataFrame, table: str, mode: str = "append") -> None:
        """Write a Polars DataFrame to a DuckDB table."""

        if mode not in ("append", "replace"):
            raise ValueError("mode must be 'append' or 'replace'")

        self.con.register("tmp_df", df.to_arrow())

        table_name = quote_identifier(table)

        if mode == "replace":
            self.con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM tmp_df")
        else:
            self.con.execute(f"INSERT INTO {table_name} SELECT * FROM tmp_df")

        self.con.unregister("tmp_df")

    def read_df(self, sql: str, params: Sequence[Any] | None = None) -> pl.DataFrame:
        """Read a Polars DataFrame from a SQL query."""
        if params is None:
            result = self.con.execute(sql)
        else:
            result = self.con.execute(sql, params)
        return pl.from_arrow(result.arrow())
