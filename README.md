# Cohort Describer

A small, DB-backed **cohort profiling** tool that computes **cohort metrics** (counts, means, quantiles, missingness, etc.) and **data quality checks** from a config file — using **Polars** for compute, **SQL (DuckDB)** for storage/querying, and **NumPy** (optional) for stats extensions.

The design is **config-driven**: to run on a new dataset, you mainly edit `config/describer.yml` (cohorts, dimensions, metrics, checks), not code.

---

## What it does

Given a dataset (CSV/Parquet):

- Ingests it into DuckDB with a `run_id`
- Derives cohort keys (e.g., month cohorts, binned cohorts)
- Aggregates metrics per `(cohort_id × dimensions)` into a **long-form** table `cohort_metrics`
- Runs QA checks (duplicates, missingness thresholds, ranges, min group sizes) into `checks`
- Creates SQL views and generates a lightweight `report.md`

---

## Install

Create/activate a virtual environment, then:

```bash
python -m pip install -r requirements.txt
```

---

## Project layout (high level)

- `config/describer.yml` — what cohorts/metrics/checks to compute (main entrypoint)
- `sql/schema.sql` — DB tables
- `sql/views.sql` — convenience views (latest run, failed checks, etc.)
- `scripts/run_all.py` — end-to-end runner (ingest → metrics → checks → report)
- `src/cohort_describer/` — library code (Polars + DB adapter + registries)

---

## Using your own data (recommended workflow)

### 1) Put your dataset somewhere
Example:
- `data/my_cohort.csv` or `data/my_cohort.parquet`

### 2) Edit `config/describer.yml`
At minimum, set:

- `table`: the raw table name to store in DB (e.g., `raw_people`)
- `id_col`: entity ID column (e.g., `person_id`)
- `cohorts`: how to derive cohort keys (month/bin)
- `dimensions`: how to slice results (sex/site/etc.)
- `metrics`: what to compute (count/mean/quantile/missing rate)
- `checks`: QA rules

Example:

```yaml
table: raw_people
id_col: person_id

cohorts:
  - name: signup_month
    from: signup_date
    type: month
  - name: age_bin
    from: age
    type: bins
    bins: [18, 25, 35, 45, 60, 80]

dimensions: [sex, site]

metrics:
  - name: n
    type: count
  - name: mean_score
    type: mean
    column: score
  - name: p50_score
    type: quantile
    column: score
    q: 0.5

checks:
  - type: duplicates
    cols: [person_id]
  - type: missing_rate_max
    column: score
    max: 0.1
```

### 3) Run end-to-end
Update `scripts/run_all.py` to point to your input file + run id:

- `input_path = "data/my_cohort.csv"`
- `run_id = "r1"` (use a new run_id for each version)

Then run:

```bash
python scripts/run_all.py
```

Outputs:
- `cohort.duckdb` (database)
- `report.md` (summary report)

---

## Inspect results

### Quick inspection (via the DB adapter)
```bash
python -c "from cohort_describer.db.duckdb import DuckDBDB; db=DuckDBDB('cohort.duckdb'); print(db.read_df('SELECT * FROM cohort_metrics LIMIT 10')); print(db.read_df('SELECT * FROM checks'))"
```

### Use views
`sql/views.sql` defines:
- `latest_run`
- `latest_cohort_metrics`
- `failed_checks_latest`

You can query those via the same snippet, e.g.:
```sql
SELECT * FROM latest_cohort_metrics WHERE metric='mean_score' LIMIT 20;
```

---

## Notes on `generate_sample`
`scripts/generate_sample.py` is only for **local testing**. Real usage assumes you bring your own dataset and update `config/describer.yml` + `scripts/run_all.py` input path.

---

## Extending (open-source friendly)

### Add a new metric type
Edit `src/cohort_describer/metrics_registry.py` and implement a new `type`, then use it in YAML.

Good additions:
- `sum`, `std`, `n_unique`
- `rate` (numerator/denominator)
- `top_k` for categorical columns

### Add a new check type
Edit `src/cohort_describer/checks_registry.py` and implement a new `type`, then use it in YAML.

Good additions:
- allowed categories check
- “min cohort size” check per cohort definition
- drift vs baseline run (compare `run_id` to `baseline_run_id`)

### DB portability
The core computes in Polars and stores in SQL. DuckDB is the default; Snowflake can be added via a second adapter under `src/cohort_describer/db/snowflake.py`.

---

## License
MIT (see `LICENSE`).
