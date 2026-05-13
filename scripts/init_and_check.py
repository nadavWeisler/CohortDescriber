"""Initialize and check the database schema."""

from __future__ import annotations

from cohort_describer.pipeline import init_db


if __name__ == "__main__":
    db = init_db()
    print(db.read_df("SHOW TABLES"))
    db.close()
