"""HTML report generation."""
from typing import Any


def generate_html_report(scan_result: dict[str, Any]) -> str:
    findings = scan_result.get("findings", [])
    by_sev = scan_result.get("by_severity", {})
    rows = ""
    for f in findings[:200]:
        rows += f"<tr><td>{f.get('severity')}</td><td>{f.get('rule_id')}</td><td>{f.get('resource_type')}</td><td>{f.get('resource_id')}</td><td>{f.get('title')}</td></tr>"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>CSPM Report</title></head>
<body>
<h1>CSPM Scan Report</h1>
<p>Cloud: {scan_result.get('cloud')} | Account: {scan_result.get('account_id')} | Region: {scan_result.get('region')}</p>
<p>Risk score: {scan_result.get('risk_score')} | Snapshot: {scan_result.get('snapshot_id') or 'N/A'}</p>
<h2>Summary</h2>
<ul>
<li>Critical: {by_sev.get('critical', 0)}</li>
<li>High: {by_sev.get('high', 0)}</li>
<li>Medium: {by_sev.get('medium', 0)}</li>
<li>Low: {by_sev.get('low', 0)}</li>
</ul>
<h2>Findings</h2>
<table border="1">
<tr><th>Severity</th><th>Rule</th><th>Resource Type</th><th>Resource ID</th><th>Title</th></tr>
{rows}
</table>
</body>
</html>"""
