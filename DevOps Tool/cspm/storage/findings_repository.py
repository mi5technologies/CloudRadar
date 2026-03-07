"""Findings repository; store with finding_type for vulnerability etc."""
from typing import Any


def save_findings(findings: list[dict], finding_type: str = "misconfiguration", storage=None) -> None:
    pass


def load_findings(snapshot_id: str, storage) -> list[dict]:
    return []
