"""Risk scoring from findings."""
from collections import defaultdict
from typing import Any

from cspm.constants import SEVERITY_MAP


class RiskEngine:
    def compute(self, findings: list[dict[str, Any]]) -> tuple[float, dict[str, int]]:
        by_severity = defaultdict(int)
        total = 0.0
        for f in findings:
            sev = f.get("severity", "medium")
            score = SEVERITY_MAP.get(sev.lower(), -4)
            by_severity[sev] += 1
            total += score
        return total, dict(by_severity)
