CREATE TABLE
    IF NOT EXISTS dataset_runs (
        run_id VARCHAR PRIMARY KEY,
        dataset_name VARCHAR,
        created_at TIMESTAMP,
        source VARCHAR
    );

CREATE TABLE
    IF NOT EXISTS dataset_metrics (
        run_id VARCHAR,
        metric VARCHAR,
        value DOUBLE,
        n INTEGER
    );

CREATE TABLE
    IF NOT EXISTS dataset_metric_groups (
        run_id VARCHAR,
        group_name VARCHAR,
        group_value VARCHAR,
        metric VARCHAR,
        value DOUBLE,
        n INTEGER
    );

CREATE TABLE
    IF NOT EXISTS checks (
        run_id VARCHAR,
        check_name VARCHAR,
        passed INTEGER,
        details_json VARCHAR
    );
