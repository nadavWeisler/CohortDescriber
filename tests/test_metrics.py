"""Tests for metric computation."""

from types import SimpleNamespace

import polars as pl

from cohort_describer.compute_metrics import compute_grouped_metrics_df, compute_metrics_df


def test_compute_metrics_df_supports_extended_metrics():
    df = pl.DataFrame(
        {
            "id": ["a", "a", "b"],
            "segment": ["x", "x", "y"],
            "value": [1.0, 2.0, 3.0],
        }
    )
    cfg = SimpleNamespace(
        metrics=[
            {"name": "n", "type": "count"},
            {"name": "distinct_ids", "type": "n_unique", "column": "id"},
            {"name": "sum_value", "type": "sum", "column": "value"},
            {"name": "mean_value", "type": "mean", "column": "value"},
        ],
        group_by=["segment"],
    )

    out = compute_metrics_df(df, cfg).sort("metric")

    assert out.filter(pl.col("metric") == "n")["value"].item() == 3.0
    assert out.filter(pl.col("metric") == "distinct_ids")["value"].item() == 2.0
    assert out.filter(pl.col("metric") == "sum_value")["value"].item() == 6.0
    assert out.filter(pl.col("metric") == "mean_value")["value"].item() == 2.0


def test_compute_grouped_metrics_df_returns_group_summaries():
    df = pl.DataFrame(
        {
            "id": ["a", "a", "b"],
            "segment": ["x", "x", "y"],
            "value": [1.0, 2.0, 3.0],
        }
    )
    cfg = SimpleNamespace(
        metrics=[
            {"name": "n", "type": "count"},
            {"name": "sum_value", "type": "sum", "column": "value"},
        ],
        group_by=["segment"],
    )

    out = compute_grouped_metrics_df(df, cfg).sort(["group_value", "metric"])

    assert out.height == 4
    assert (
        out.filter(
            (pl.col("group_name") == "segment")
            & (pl.col("group_value") == "x")
            & (pl.col("metric") == "n")
        )["value"].item()
        == 2.0
    )
    assert (
        out.filter(
            (pl.col("group_name") == "segment")
            & (pl.col("group_value") == "y")
            & (pl.col("metric") == "sum_value")
        )["value"].item()
        == 3.0
    )
