"""ECS cluster and task definition scanner."""
from typing import Any


def scan_ecs_clusters(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]


def scan_ecs_task_defs(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(a) for a in assets]
