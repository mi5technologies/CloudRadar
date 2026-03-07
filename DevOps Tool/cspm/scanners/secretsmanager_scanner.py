"""Secrets Manager scanner: pass-through (rules handle checks)."""
from typing import Any


def scan_secretsmanager(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list(assets)
