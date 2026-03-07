"""WAF scanner: flag ALBs without WAF attached."""
from typing import Any

from cspm.discovery.waf_discovery import get_web_acl_associations


def scan_waf(albs: list[dict[str, Any]], region: str) -> list[dict[str, Any]]:
    associations = get_web_acl_associations(region)
    enriched = []
    for alb in albs:
        alb = dict(alb)
        arn = alb.get("id")  # LoadBalancerArn
        alb["waf_attached"] = (arn in associations) if arn else False
        enriched.append(alb)
    return enriched
