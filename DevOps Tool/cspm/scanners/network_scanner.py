"""Network scanner: flag SGs open to 0.0.0.0/0 on sensitive ports."""
from typing import Any

from cspm.constants import SENSITIVE_PORTS


def scan_network(sgs: list[dict[str, Any]], albs: list[dict]) -> list[dict[str, Any]]:
    enriched_sgs = []
    for sg in sgs:
        sg = dict(sg)
        sg["open_to_world"] = _is_open_to_world(sg.get("ip_permissions") or [])
        enriched_sgs.append(sg)
    return enriched_sgs


def _is_open_to_world(ip_permissions: list[dict]) -> bool:
    for perm in ip_permissions:
        cidr = (perm.get("cidr") or "").strip()
        if cidr in ("0.0.0.0/0", "::/0"):
            from_p = perm.get("from_port")
            to_p = perm.get("to_port")
            if from_p is None or to_p is None:
                return True
            for port in SENSITIVE_PORTS:
                if from_p <= port <= to_p:
                    return True
    return False
