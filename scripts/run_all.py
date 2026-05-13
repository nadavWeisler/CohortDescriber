"""Run the full dataset describer pipeline end to end."""

from cohort_describer.pipeline import run_all


if __name__ == "__main__":
    run_id, raw_table, n = run_all(
        input_path="data/customers_test.csv",
        run_id="r1",
        out_base="report",
        formats=("md", "json", "csv"),
    )
    print(f"OK: run_id={run_id}, rows={n}, raw_table={raw_table}")
