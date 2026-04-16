# Cohort Describer

Simple pipeline for describing a dataset with:
- ingestion into DuckDB
- dataset-level metrics
- data-quality checks
- a markdown report

## What this project contains

- `config/describer.yml` – pipeline configuration (id column, metric specs, checks, optional ingest mapping/casts)
- `sql/schema.sql` – database schema
- `scripts/generate_sample.py` – generates sample input data
- `scripts/run_all.py` – full pipeline (ingest → metrics → checks → report)
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
PYTHONPATH=src python scripts/run_all.py
```

4. Check outputs:
- `cohort.duckdb`
- `report.md`

## Configuration

Main config file: `config/describer.yml`

Current expected keys:
- `table_prefix`
- `id_col`
- `ingest` (optional): `mapping`, `date_columns`, `dtypes`
- `metrics` (required)
- `checks` (optional)

Minimal example:

```yaml
table_prefix: raw_input
id_col: id

metrics:
  - name: n
    type: count

checks:
  - type: duplicates
    cols: [id]
```

## Running pipeline steps separately

You can run individual steps if needed:

```bash
PYTHONPATH=src python scripts/init_and_check.py
PYTHONPATH=src python scripts/run_ingest.py
PYTHONPATH=src python scripts/run_metrics.py
PYTHONPATH=src python scripts/run_checks.py
```

## Querying results

Example:

```bash
PYTHONPATH=src python -c "from cohort_describer.duckdb import DuckDBDB; db=DuckDBDB('cohort.duckdb'); print(db.read_df('SELECT * FROM dataset_runs ORDER BY created_at DESC LIMIT 5')); print(db.read_df('SELECT * FROM dataset_metrics ORDER BY metric LIMIT 20')); print(db.read_df('SELECT * FROM checks ORDER BY check_name LIMIT 20'))"
```

## License

MIT (see `LICENSE`).
