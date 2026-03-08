"""Risk summary for reports."""
from typing import Any


def risk_summary(scan_result: dict[str, Any]) -> str:
    by_sev = scan_result.get("by_severity", {})
    score = scan_result.get("risk_score", 0)
    lines = [
        f"Risk score: {score}",
        f"Critical: {by_sev.get('critical', 0)}",
        f"High: {by_sev.get('high', 0)}",
        f"Medium: {by_sev.get('medium', 0)}",
        f"Low: {by_sev.get('low', 0)}",
    ]
    return "\n".join(lines)
