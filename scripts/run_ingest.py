"""Ingest sample data into DuckDB for cohort describer."""

from cohort_describer.pipeline import ingest_step


if __name__ == "__main__":
    run_id, raw_table, n = ingest_step(
        "data/customers_test.csv",
        run_id="r1",
        dataset_name="data/customers_test.csv",
        source="local",
    )
    print("ingested rows:", (run_id, raw_table, n))
