"""Lambda function discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        lam = get_client("lambda", region)
        paginator = lam.get_paginator("list_functions")
        for page in paginator.paginate():
            for fn in page.get("Functions", []):
                assets.append({
                    "id": fn.get("FunctionName"),
                    "type": "lambda",
                    "region": region,
                    "runtime": fn.get("Runtime"),
                    "timeout": fn.get("Timeout"),
                    "memory_size": fn.get("MemorySize"),
                    "environment": fn.get("Environment", {}).get("Variables") or {},
                    "tags": fn.get("Tags") or {},
                })
    except Exception:
        pass
    return assets
