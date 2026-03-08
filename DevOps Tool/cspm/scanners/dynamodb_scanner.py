"""DynamoDB table scanner."""
from typing import Any


def scan_dynamodb(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]
