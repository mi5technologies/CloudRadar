"""Unified asset catalog for audit: normalize and list all assets."""
from datetime import datetime
from typing import Any


def build_catalog(
    assets: dict[str, list[dict[str, Any]]],
    cloud: str,
    account_id: str,
    region: str,
    snapshot_id: str | None = None,
) -> list[dict[str, Any]]:
    catalog = []
    for resource_type, items in assets.items():
        for a in items:
            entry = {
                "id": a.get("id") or a.get("name") or a.get("arn") or "",
                "type": resource_type,
                "cloud": cloud,
                "account_id": account_id,
                "region": region,
                "tags": a.get("tags") or {},
                "last_seen": datetime.utcnow().isoformat() + "Z",
                "metadata": _safe_metadata(a),
            }
            if snapshot_id:
                entry["snapshot_id"] = snapshot_id
            catalog.append(entry)
    return catalog


def _safe_metadata(a: dict) -> dict:
    """Flatten key attributes for audit (no large blobs)."""
    out = {}
    for k in ("state", "instance_type", "engine", "runtime", "scheme", "public", "publicly_accessible"):
        if k in a and a[k] is not None:
            out[k] = a[k]
    return out


def filter_catalog(
    catalog: list[dict],
    cloud: str | None = None,
    resource_type: str | None = None,
    tag_key: str | None = None,
    tag_value: str | None = None,
) -> list[dict]:
    out = catalog
    if cloud:
        out = [e for e in out if e.get("cloud") == cloud]
    if resource_type:
        out = [e for e in out if e.get("type") == resource_type]
    if tag_key:
        out = [e for e in out if (e.get("tags") or {}).get(tag_key) is not None]
        if tag_value:
            out = [e for e in out if (e.get("tags") or {}).get(tag_key) == tag_value]
    return out
