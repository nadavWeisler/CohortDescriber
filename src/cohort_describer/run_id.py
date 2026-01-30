"""Generate a unique run ID based on the current timestamp."""
from __future__ import annotations
from datetime import datetime

def make_run_id(prefix: str = "run") -> str:
    """Generate a unique run ID based on the current timestamp."""
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
