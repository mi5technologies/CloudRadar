"""Governance report: tag and policy summary."""
import json
from typing import Any

from cspm.governance.tag_policy_engine import TagPolicyEngine
from cspm.governance.resource_policy_engine import ResourcePolicyEngine


def generate_governance_report(
    catalog: list[dict],
    required_tags: list[str] | None = None,
    forbidden_instance_types: list[str] | None = None,
    output_format: str = "json",
) -> str:
    tag_engine = TagPolicyEngine(required_tags=required_tags)
    tag_result = tag_engine.evaluate(catalog)
    resource_engine = ResourcePolicyEngine(forbidden_instance_types=forbidden_instance_types)
    policy_violations = resource_engine.evaluate(catalog)
    summary = {
        "tag_compliance": {
            "required_tags": tag_result["required_tags"],
            "compliant_count": tag_result["compliant_count"],
            "non_compliant_count": tag_result["non_compliant_count"],
        },
        "policy_violations_count": len(policy_violations),
        "policy_violations": policy_violations,
    }
    if output_format == "html":
        return _governance_report_html(summary)
    return json.dumps(summary, indent=2)


def _governance_report_html(summary: dict) -> str:
    tc = summary.get("tag_compliance", {})
    rows = ""
    for v in summary.get("policy_violations", [])[:50]:
        rows += f"<tr><td>{v.get('policy')}</td><td>{v.get('asset', {}).get('id')}</td><td>{v.get('value')}</td></tr>"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Governance Report</title></head>
<body>
<h1>Governance Report</h1>
<h2>Tag Compliance</h2>
<p>Required tags: {tc.get('required_tags')}</p>
<p>Compliant: {tc.get('compliant_count')} | Non-compliant: {tc.get('non_compliant_count')}</p>
<h2>Policy Violations</h2>
<table border="1"><tr><th>Policy</th><th>Asset</th><th>Value</th></tr>{rows}</table>
</body>
</html>"""
