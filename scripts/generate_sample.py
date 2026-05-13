"""Generate a sample customer dataset with controlled characteristics."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import numpy as np
import polars as pl


def main(
    out_dir: str = "data",
    n: int = 50_000,
    seed: int = 7,
    dup_id_rate: float = 0.01,
    missing_birth_rate: float = 0.03,
    missing_last_purchase_rate: float = 0.08,
) -> None:
    """Generate a sample customer dataset with controlled characteristics."""

    rng = np.random.default_rng(seed)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # IDs as plain Python list (Utf8, not Object)
    ids = [f"C{i:07d}" for i in range(1, n + 1)]

    # Inject duplicates
    n_dups = int(n * dup_id_rate)
    if n_dups > 0:
        dup_positions = rng.choice(np.arange(n), size=n_dups, replace=False)
        source_positions = rng.choice(np.arange(n), size=n_dups, replace=True)
        for dp, sp in zip(dup_positions, source_positions):
            ids[int(dp)] = ids[int(sp)]

    # Dates as Python date list (Polars can cast to Date cleanly)
    birth_start = date(1940, 1, 1)
    birth_days = rng.integers(0, 365 * 68, size=n)
    birth_dates = [birth_start + timedelta(days=int(d)) for d in birth_days]

    lp_start = date(2023, 1, 1)
    lp_days = rng.integers(0, 365 * 3, size=n)
    last_purchase_dates = [lp_start + timedelta(days=int(d)) for d in lp_days]

    sectors = ["retail", "b2b", "health", "finance", "gaming"]
    marketing_sector = rng.choice(
        sectors, size=n, p=[0.35, 0.20, 0.15, 0.15, 0.15]
    ).tolist()

    items = [
        "subscription",
        "bundle",
        "single_item",
        "upgrade",
        "gift_card",
        "addon",
        "service_fee",
    ]
    last_purchase_item = rng.choice(
        items, size=n, p=[0.18, 0.12, 0.35, 0.10, 0.08, 0.12, 0.05]
    ).tolist()
    purchase_count = rng.integers(1, 25, size=n).tolist()
    lifetime_value = np.round(rng.lognormal(mean=4.0, sigma=0.45, size=n), 2).tolist()

    df = pl.DataFrame(
        {
            "id": ids,
            "birth_date": birth_dates,
            "marketing_sector": marketing_sector,
            "last_purchase_date": last_purchase_dates,
            "last_purchase_item": last_purchase_item,
            "purchase_count": purchase_count,
            "lifetime_value": lifetime_value,
        }
    ).with_columns(
        # Force stable dtypes (prevents Object)
        pl.col("id").cast(pl.Utf8),
        pl.col("marketing_sector").cast(pl.Utf8),
        pl.col("last_purchase_item").cast(pl.Utf8),
        pl.col("birth_date").cast(pl.Date, strict=False),
        pl.col("last_purchase_date").cast(pl.Date, strict=False),
        pl.col("purchase_count").cast(pl.Int64, strict=False),
        pl.col("lifetime_value").cast(pl.Float64, strict=False),
    )

    # Missingness masks as Polars boolean Series
    if missing_birth_rate > 0:
        m = pl.Series(rng.random(n) < missing_birth_rate)
        df = df.with_columns(
            pl.when(m).then(None).otherwise(pl.col("birth_date")).alias("birth_date")
        )

    if missing_last_purchase_rate > 0:
        m = pl.Series(rng.random(n) < missing_last_purchase_rate)
        df = df.with_columns(
            pl.when(m)
            .then(None)
            .otherwise(pl.col("last_purchase_date"))
            .alias("last_purchase_date")
        )

    # Re-cast after injecting nulls (keeps Date dtype)
    df = df.with_columns(
        pl.col("birth_date").cast(pl.Date, strict=False),
        pl.col("last_purchase_date").cast(pl.Date, strict=False),
    )

    csv_path = out_path / "customers_test.csv"
    pq_path = out_path / "customers_test.parquet"

    df.write_csv(csv_path)
    df.write_parquet(pq_path)

    print(f"Wrote: {csv_path} ({df.height} rows)")
    print(f"Wrote: {pq_path} ({df.height} rows)")


if __name__ == "__main__":
    main()
