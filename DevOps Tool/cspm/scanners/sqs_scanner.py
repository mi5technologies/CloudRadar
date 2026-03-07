"""SQS queue scanner."""
from typing import Any


def scan_sqs(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]
