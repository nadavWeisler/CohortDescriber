# Cohort Describer

Simple pipeline for describing a dataset with:
- ingestion into DuckDB
- dataset-level and grouped metrics
- data-quality checks
- markdown/JSON/CSV reports

Keywords: `cohort`, `duckdb`, `data-quality`, `metrics`, `reporting`.

## What this project contains

- `config/describer.yml` – validated pipeline configuration
- `sql/schema.sql` – database schema
- `scripts/generate_sample.py` – generates sample input data
- `src/cohort_describer/cli.py` – CLI entrypoint
- `src/cohort_describer/` – core implementation

## Quick start

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Generate sample data:

```bash
python scripts/generate_sample.py
```

3. Run the full pipeline:

```bash
PYTHONPATH=src python -m cohort_describer.cli all data/customers_test.csv --run-id r1 --formats md,json,csv
```

4. Check outputs:
- `cohort.duckdb`
- `report.md`
- `report.json`
- `report_metrics.csv`
- `report_grouped_metrics.csv`

## CLI

The package entrypoint is defined in `pyproject.toml`:

```bash
python -m cohort_describer.cli --help
```

Available commands:
- `init`
- `ingest`
- `metrics`
- `checks`
- `report`
- `all`

Example step-by-step run:

```bash
PYTHONPATH=src python scripts/init_and_check.py
PYTHONPATH=src python scripts/run_ingest.py
PYTHONPATH=src python scripts/run_metrics.py
PYTHONPATH=src python scripts/run_checks.py
PYTHONPATH=src python scripts/run_report.py
```

## Configuration

Main config file: `config/describer.yml`

Current keys:
- `table_prefix`
- `id_col`
- `group_by` (optional)
- `ingest` (optional): `mapping`, `date_columns`, `dtypes`
- `metrics`
- `checks` (optional)

Example:

```yaml
table_prefix: raw_input
id_col: id

group_by:
  - marketing_sector

metrics:
  - name: n
    type: count
  - name: distinct_ids
    type: n_unique
    column: id
  - name: total_lifetime_value
    type: sum
    column: lifetime_value

checks:
  - type: unique
    cols: [id]
  - type: accepted_values
    column: marketing_sector
    values: [retail, b2b, health, finance, gaming]
```

Supported metric types:
- `count`
- `mean`
- `sum`
- `min`
- `max`
- `stddev`
- `quantile`
- `missing_rate`
- `n_unique`

Supported check types:
- `duplicates`
- `unique`
- `missing_rate`
- `range`
- `accepted_values`
- `row_count`
- `referential`

## Querying results

Example:

```bash
PYTHONPATH=src python -c "from cohort_describer.duckdb import DuckDBDB; db=DuckDBDB('cohort.duckdb'); print(db.read_df('SELECT * FROM \"dataset_runs\" ORDER BY created_at DESC LIMIT 5')); print(db.read_df('SELECT * FROM \"dataset_metrics\" ORDER BY metric LIMIT 20')); print(db.read_df('SELECT * FROM \"dataset_metric_groups\" ORDER BY group_name, group_value, metric LIMIT 20')); print(db.read_df('SELECT * FROM \"checks\" ORDER BY check_name LIMIT 20'))"
```

## Tests

Run the suite with:

```bash
PYTHONPATH=src python -m pytest
```

## License

MIT (see `LICENSE`).
