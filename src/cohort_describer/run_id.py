"""Generate a unique run ID based on the current timestamp."""
from __future__ import annotations
from datetime import datetime

from cohort_describer.utils import validate_safe_token

def make_run_id(prefix: str = "run") -> str:
    """Generate a unique run ID based on the current timestamp."""
    validate_safe_token(prefix, "run_id prefix")
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
