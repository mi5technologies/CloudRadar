"""Change report: JSON and HTML summary of changes since last run."""
import json
from typing import Any


def generate_change_report(diff_result: dict[str, Any], format: str = "json") -> str:
    if format == "html":
        return _change_report_html(diff_result)
    return json.dumps(diff_result, indent=2, default=str)


def _change_report_html(diff: dict) -> str:
    added = diff.get("added", [])
    removed = diff.get("removed", [])
    modified = diff.get("modified", [])
    fn = diff.get("findings_new", [])
    fr = diff.get("findings_resolved", [])
    rows_added = "".join(f"<tr><td>{a.get('type')}</td><td>{a.get('id')}</td></tr>" for a in added[:100])
    rows_removed = "".join(f"<tr><td>{r.get('type')}</td><td>{r.get('id')}</td></tr>" for r in removed[:100])
    rows_mod = "".join(f"<tr><td>{m.get('after', {}).get('type')}</td><td>{m.get('after', {}).get('id')}</td></tr>" for m in modified[:100])
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Change Report</title></head>
<body>
<h1>Change Report</h1>
<p>Before: {diff.get('snapshot_before')} | After: {diff.get('snapshot_after', 'current')}</p>
<h2>Assets Added ({len(added)})</h2>
<table border="1"><tr><th>Type</th><th>ID</th></tr>{rows_added}</table>
<h2>Assets Removed ({len(removed)})</h2>
<table border="1"><tr><th>Type</th><th>ID</th></tr>{rows_removed}</table>
<h2>Assets Modified ({len(modified)})</h2>
<table border="1"><tr><th>Type</th><th>ID</th></tr>{rows_mod}</table>
<h2>New Findings ({len(fn)})</h2>
<p>{len(fn)} new findings since last run.</p>
<h2>Resolved Findings ({len(fr)})</h2>
<p>{len(fr)} findings no longer present.</p>
</body>
</html>"""
