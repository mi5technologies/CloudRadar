"""Tag policy: required tags and compliance."""
from typing import Any


class TagPolicyEngine:
    def __init__(self, required_tags: list[str] | None = None):
        self.required_tags = required_tags or ["Owner", "Environment", "Project"]

    def evaluate(self, catalog: list[dict[str, Any]]) -> dict[str, Any]:
        compliant = []
        non_compliant = []
        for asset in catalog:
            tags = asset.get("tags") or {}
            missing = [t for t in self.required_tags if t not in tags or not tags[t]]
            if not missing:
                compliant.append(asset)
            else:
                non_compliant.append({
                    "asset": asset,
                    "missing_tags": missing,
                })
        return {
            "required_tags": self.required_tags,
            "compliant_count": len(compliant),
            "non_compliant_count": len(non_compliant),
            "non_compliant": non_compliant,
        }
