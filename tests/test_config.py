"""Tests for configuration validation."""

from pathlib import Path

import pytest

from cohort_describer.config import load_config
from cohort_describer.utils import raw_table_name


def test_load_config_rejects_invalid_table_prefix(tmp_path: Path):
    config_path = tmp_path / "invalid.yml"
    config_path.write_text(
        """
table_prefix: bad-prefix
id_col: id
metrics:
  - name: n
    type: count
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="table_prefix"):
        load_config(str(config_path))


def test_raw_table_name_rejects_unsafe_run_id():
    with pytest.raises(ValueError, match="run_id"):
        raw_table_name("raw_input", "bad-run-id")
