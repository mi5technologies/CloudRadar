"""Compare snapshots and emit new/deleted/modified assets and findings."""
from typing import Any


class ChangeDetector:
    def __init__(self, snapshot_manager):
        self.snapshot_manager = snapshot_manager

    def diff(
        self,
        snapshot_before_id: str,
        snapshot_after_id: str,
    ) -> dict[str, Any]:
        before = self.snapshot_manager.load(snapshot_before_id)
        after = self.snapshot_manager.load(snapshot_after_id)
        if not before or not after:
            return {"error": "Snapshot not found", "added": [], "removed": [], "modified": []}

        cat_before = {_asset_key(a): a for a in before.get("catalog", [])}
        cat_after = {_asset_key(a): a for a in after.get("catalog", [])}
        keys_before = set(cat_before)
        keys_after = set(cat_after)

        added = [cat_after[k] for k in (keys_after - keys_before)]
        removed = [cat_before[k] for k in (keys_before - keys_after)]
        modified = []
        for k in keys_before & keys_after:
            b, a = cat_before[k], cat_after[k]
            if _metadata_changed(b, a):
                modified.append({"before": b, "after": a})

        findings_before = {_finding_key(f): f for f in before.get("findings", [])}
        findings_after = {_finding_key(f): f for f in after.get("findings", [])}
        findings_new = [findings_after[k] for k in findings_after if k not in findings_before]
        findings_resolved = [findings_before[k] for k in findings_before if k not in findings_after]

        return {
            "snapshot_before": snapshot_before_id,
            "snapshot_after": snapshot_after_id,
            "added": added,
            "removed": removed,
            "modified": modified,
            "findings_new": findings_new,
            "findings_resolved": findings_resolved,
        }

    def changes_since_last(
        self,
        cloud: str,
        account_id: str,
        region: str,
        current_assets: dict[str, list],
        current_findings: list[dict],
        current_catalog: list[dict],
    ) -> dict[str, Any] | None:
        latest = self.snapshot_manager.get_latest(cloud=cloud, account_id=account_id)
        if not latest:
            return None
        cat_before = {_asset_key(a): a for a in latest.get("catalog", [])}
        cat_after = {_asset_key(a): a for a in current_catalog}
        keys_before = set(cat_before)
        keys_after = set(cat_after)
        added = [cat_after[k] for k in (keys_after - keys_before)]
        removed = [cat_before[k] for k in (keys_before - keys_after)]
        modified = []
        for k in keys_before & keys_after:
            b, a = cat_before[k], cat_after[k]
            if _metadata_changed(b, a):
                modified.append({"before": b, "after": a})
        findings_before = {_finding_key(f): f for f in latest.get("findings", [])}
        findings_after = {_finding_key(f): f for f in current_findings}
        findings_new = [findings_after[k] for k in findings_after if k not in findings_before]
        findings_resolved = [findings_before[k] for k in findings_before if k not in findings_after]
        return {
            "snapshot_before": latest.get("snapshot_id"),
            "added": added,
            "removed": removed,
            "modified": modified,
            "findings_new": findings_new,
            "findings_resolved": findings_resolved,
        }


def _asset_key(a: dict) -> str:
    return f"{a.get('cloud', '')}:{a.get('account_id', '')}:{a.get('region', '')}:{a.get('type', '')}:{a.get('id', '')}"


def _metadata_changed(b: dict, a: dict) -> bool:
    return (b.get("metadata") or {}) != (a.get("metadata") or {})


def _finding_key(f: dict) -> str:
    return f"{f.get('rule_id', '')}:{f.get('resource_type', '')}:{f.get('resource_id', '')}"
