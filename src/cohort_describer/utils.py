"""Shared helpers for validation and SQL-safe identifier handling."""

from __future__ import annotations

import re

_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_safe_token(value: str, field_name: str) -> str:
    """Validate an identifier-like token used for table prefixes and run IDs."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _SAFE_TOKEN_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must match {_SAFE_TOKEN_RE.pattern!r}; got {value!r}"
        )
    return value


def quote_identifier(identifier: str) -> str:
    """Quote a SQL identifier, including dotted names."""
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("identifier must be a non-empty string")
    parts = [part.strip() for part in identifier.split(".")]
    if any(not part for part in parts):
        raise ValueError(f"Invalid identifier: {identifier!r}")
    return ".".join('"' + part.replace('"', '""') + '"' for part in parts)


def raw_table_name(table_prefix: str, run_id: str) -> str:
    """Generate a safe raw table name based on the prefix and run ID."""
    validate_safe_token(table_prefix, "table_prefix")
    validate_safe_token(run_id, "run_id")
    return f"{table_prefix}__{run_id}"
