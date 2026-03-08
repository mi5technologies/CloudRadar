"""EC2 scanner: public IP, forbidden instance types."""
from typing import Any


def scan_ec2(assets: list[dict[str, Any]], forbidden_types: list[str] | None = None) -> list[dict[str, Any]]:
    forbidden = set(forbidden_types or [])
    enriched = []
    for a in assets:
        a = dict(a)
        a["public_ip"] = bool(a.get("public_ip"))
        it = a.get("instance_type") or ""
        a["instance_type_forbidden"] = it in forbidden
        a.setdefault("tags", {})
        a["has_tag_Owner"] = "Owner" in a.get("tags", {})
        a["has_tag_Environment"] = "Environment" in a.get("tags", {})
        enriched.append(a)
    return enriched
