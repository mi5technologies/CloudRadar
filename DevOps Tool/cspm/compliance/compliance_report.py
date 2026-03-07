"""Compliance report: per-framework pass/fail summary."""
import json
from typing import Any

from cspm.compliance.cis_checks import get_cis_checks, CIS_MAP
from cspm.compliance.soc2_checks import get_soc2_checks, SOC2_MAP
from cspm.compliance.hipaa_checks import get_hipaa_checks
from cspm.compliance.pci_checks import get_pci_checks
from cspm.compliance.iso27001_checks import get_iso27001_checks
from cspm.compliance.compliance_mapper import map_findings_to_controls


def generate_compliance_report(
    findings: list[dict],
    framework: str,
    output_format: str = "json",
) -> str:
    framework = framework.lower()
    if framework == "cis":
        checks = get_cis_checks()
        control_ids = {c["id"] for c in checks}
    elif framework == "soc2":
        checks = get_soc2_checks()
        control_ids = {c["id"] for c in checks}
    elif framework == "hipaa":
        checks = get_hipaa_checks()
        control_ids = {c["id"] for c in checks}
    elif framework == "pci":
        checks = get_pci_checks()
        control_ids = {c["id"] for c in checks}
    elif framework == "iso27001":
        checks = get_iso27001_checks()
        control_ids = {c["id"] for c in checks}
    else:
        return json.dumps({"error": f"Unknown framework: {framework}"})

    failures = map_findings_to_controls(findings, framework)
    passed = [c for c in control_ids if c not in failures]
    failed = list(failures.keys())
    not_applicable = []

    summary = {
        "framework": framework,
        "passed": len(passed),
        "failed": len(failed),
        "not_applicable": len(not_applicable),
        "passed_controls": passed,
        "failed_controls": failed,
        "failures_detail": {ctrl: [{"rule_id": f["rule_id"], "resource_id": f["resource_id"]} for f in findings_list] for ctrl, findings_list in failures.items()},
    }

    if output_format == "html":
        return _compliance_report_html(summary)
    return json.dumps(summary, indent=2)


def _compliance_report_html(summary: dict) -> str:
    failed = summary.get("failed_controls", [])
    detail = summary.get("failures_detail", {})
    rows = ""
    for ctrl in failed:
        for item in detail.get(ctrl, []):
            rows += f"<tr><td>{ctrl}</td><td>{item.get('rule_id')}</td><td>{item.get('resource_id')}</td></tr>"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Compliance Report - {summary.get('framework')}</title></head>
<body>
<h1>Compliance Report: {summary.get('framework').upper()}</h1>
<p>Passed: {summary.get('passed')} | Failed: {summary.get('failed')}</p>
<h2>Failed Controls</h2>
<table border="1"><tr><th>Control</th><th>Rule</th><th>Resource</th></tr>{rows}</table>
</body>
</html>"""
