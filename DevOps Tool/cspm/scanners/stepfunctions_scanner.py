"""Step Functions state machine scanner."""
from typing import Any


def scan_stepfunctions(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich Step Functions state machines for rule evaluation."""
    return [dict(a) for a in assets]
