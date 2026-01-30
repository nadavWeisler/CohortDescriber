def raw_table_name(table_prefix: str, run_id: str) -> str:
    """Generate a raw table name based on the prefix and run ID."""
    # keep it simple; assume run_id has safe chars
    return f"{table_prefix}__{run_id}"