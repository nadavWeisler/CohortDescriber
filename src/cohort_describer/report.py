"""Generate Markdown reports from cohort description runs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import polars as pl

from cohort_describer.duckdb import DuckDBDB


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

    def fmt_row(vals):
        return (
            "| " + " | ".join(vals[i].ljust(widths[i]) for i in range(len(cols))) + " |"
        )

    header = fmt_row(cols)
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(cols))) + " |"
    body = "\n".join(fmt_row(r) for r in str_rows)

    more = ""
    if df.height > max_rows:
        more = f"\n\n_(showing first {max_rows} of {df.height} rows)_\n"

    return header + "\n" + sep + "\n" + body + more + "\n"


def generate_report(
    db: DuckDBDB,
    table: str,
    out_path: str = "report.md",
    run_id: Optional[str] = None,
) -> None:
    """
    Generate a Markdown report for a given run_id (defaults to latest run).

    Requires tables:
    - dataset_runs
    - dataset_metrics
    - checks
    - raw table: `table` with a run_id column
    """
    # determine run_id
    if run_id is None:
        latest = db.read_df(
            "SELECT run_id FROM dataset_runs ORDER BY created_at DESC LIMIT 1"
        )
        if latest.height == 0:
            Path(out_path).write_text(
                "# Dataset Report\n\n_No runs found in dataset_runs._\n",
                encoding="utf-8",
            )
            return
        run_id = latest["run_id"][0]

    # counts
    n_raw = db.read_df(f"SELECT COUNT(*) AS n FROM {table} WHERE run_id='{run_id}'")[
        "n"
    ][0]

    # metrics
    metrics = db.read_df(
        f"SELECT metric, value, n FROM dataset_metrics WHERE run_id='{run_id}' ORDER BY metric"
    )

    # failed checks
    failed = db.read_df(
        f"SELECT check_name, details_json FROM checks WHERE run_id='{run_id}' AND passed=0 ORDER BY check_name"
    )

    # all checks (summary)
    checks_summary = db.read_df(
        f"""
        SELECT
        SUM(CASE WHEN passed=1 THEN 1 ELSE 0 END) AS passed,
        SUM(CASE WHEN passed=0 THEN 1 ELSE 0 END) AS failed
        FROM checks
        WHERE run_id='{run_id}'
        """
    )

    md = []
    md.append("# Dataset Report\n\n")
    md.append(f"**run_id:** `{run_id}`  \n")
    md.append(f"**raw table:** `{table}`  \n")
    md.append(f"**rows in run:** `{n_raw}`  \n\n")

    md.append("## Checks summary\n\n")
    md.append(_md_table(checks_summary))

    md.append("## Failed checks\n\n")
    md.append(_md_table(failed))

    md.append("## Dataset metrics\n\n")
    md.append(_md_table(metrics))

    Path(out_path).write_text("".join(md), encoding="utf-8")
