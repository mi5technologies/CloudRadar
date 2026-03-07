"""API Gateway scanner."""
from typing import Any


def scan_apigateway(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]
