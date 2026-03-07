"""Resource policy: forbidden instance types, allowed regions, etc."""
from typing import Any


class ResourcePolicyEngine:
    def __init__(
        self,
        forbidden_instance_types: list[str] | None = None,
        allowed_regions: list[str] | None = None,
    ):
        self.forbidden_instance_types = set(forbidden_instance_types or [])
        self.allowed_regions = set(allowed_regions) if allowed_regions else None

    def evaluate(self, catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
        violations = []
        for asset in catalog:
            at = asset.get("type")
            if at == "ec2":
                it = (asset.get("metadata") or {}).get("instance_type")
                if it and it in self.forbidden_instance_types:
                    violations.append({
                        "policy": "forbidden_instance_type",
                        "asset": asset,
                        "value": it,
                    })
            if self.allowed_regions:
                reg = asset.get("region")
                if reg and reg not in self.allowed_regions:
                    violations.append({
                        "policy": "region_not_allowed",
                        "asset": asset,
                        "value": reg,
                    })
        return violations
