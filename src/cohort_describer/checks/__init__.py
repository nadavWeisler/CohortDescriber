"""Cohort describer checks package."""

from __future__ import annotations

from . import duplicates, missing_rate, range_check  # noqa: F401
from .registry import run_check, register_check
