"""SNS scanner: pass-through (rules handle checks)."""
from typing import Any


def scan_sns(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list(assets)
