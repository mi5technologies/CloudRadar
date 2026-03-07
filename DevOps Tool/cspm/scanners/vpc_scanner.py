"""VPC and EBS scanner."""
from typing import Any


def scan_vpc(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]


def scan_ebs(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]
