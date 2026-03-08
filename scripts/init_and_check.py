"""Initialize and check the database schema."""

from __future__ import annotations

from cohort_describer.duckdb import DuckDBDB

db = DuckDBDB("cohort.duckdb")
db.execute_file("sql/schema.sql")
print(db.read_df("SHOW TABLES"))
