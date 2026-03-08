"""RDS scanner: encryption, public (already in discovery)."""
from typing import Any


def scan_rds(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]
