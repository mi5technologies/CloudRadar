"""Audit export: CSV and JSON catalog for auditors."""
import csv
import json
from io import StringIO
from typing import Any


def export_audit_csv(catalog: list[dict[str, Any]], columns: list[str] | None = None) -> str:
    if not catalog:
        return ""
    cols = columns or ["id", "type", "cloud", "account_id", "region", "last_seen", "tags"]
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for row in catalog:
        writer.writerow({k: _cell(row.get(k)) for k in cols})
    return buf.getvalue()


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, dict):
        return json.dumps(v)
    return str(v)


def export_audit_json(catalog: list[dict], snapshot_id: str | None = None) -> str:
    out = {"catalog": catalog, "count": len(catalog)}
    if snapshot_id:
        out["snapshot_id"] = snapshot_id
    return json.dumps(out, indent=2, default=str)
