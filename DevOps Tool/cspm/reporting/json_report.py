"""JSON report generation."""
import json
from typing import Any


def generate_json_report(scan_result: dict[str, Any]) -> str:
    out = {
        "cloud": scan_result.get("cloud"),
        "account_id": scan_result.get("account_id"),
        "region": scan_result.get("region"),
        "risk_score": scan_result.get("risk_score"),
        "by_severity": scan_result.get("by_severity"),
        "findings_count": len(scan_result.get("findings", [])),
        "findings": scan_result.get("findings", []),
        "snapshot_id": scan_result.get("snapshot_id"),
    }
    return json.dumps(out, indent=2, default=str)
