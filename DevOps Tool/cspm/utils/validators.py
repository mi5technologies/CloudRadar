"""Validation helpers."""
from typing import Any


def require_keys(obj: dict, keys: list[str], name: str = "object") -> None:
    for k in keys:
        if k not in obj:
            raise ValueError(f"{name} missing required key: {k}")


def safe_get(obj: dict, *keys: str, default: Any = None) -> Any:
    for k in keys:
        obj = obj.get(k) if isinstance(obj, dict) else default
        if obj is None:
            return default
    return obj
