"""Tests for cohort_keys.py"""

import polars as pl

from cohort_describer.cohort_keys import add_signup_month, add_age_bin


def test_cohort_keys():
    """
    Test cohort key functions.
    """
    df = pl.DataFrame(
        {
            "signup_date": ["2025-01-03", "2025-02-10"],
            "age": [24, 35],
        }
    )

    df = add_signup_month(df, "signup_date")
    assert df["signup_month"].to_list() == ["2025-01", "2025-02"]

    df = add_age_bin(df, "age", bins=[18, 25, 35, 45])
    b = df["age_bin"].to_list()

    assert "18" in str(b[0]) and "25" in str(b[0])  # 24 falls in 18–25 bucket
    assert "35" in str(b[1]) and "45" in str(b[1])  # 35 falls in 35–45 bucket
