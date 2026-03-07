"""WAF and Web ACL discovery (AWS)."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    """Discover WAFv2 Web ACLs and which resources they are associated with."""
    result: list[dict[str, Any]] = []
    try:
        wafv2 = get_client("wafv2", region)
        # WAFv2 regional (for ALB, API Gateway)
        for scope in ["REGIONAL", "CLOUDFRONT"]:
            try:
                resp = wafv2.list_web_acls(Scope=scope)
                for acl in resp.get("WebACLs", []):
                    result.append({
                        "id": acl.get("Id"),
                        "name": acl.get("Name"),
                        "arn": acl.get("ARN"),
                        "type": "waf",
                        "region": region,
                        "scope": scope,
                    })
            except Exception:
                pass
    except Exception:
        pass
    return result


def get_web_acl_associations(region: str) -> dict[str, str]:
    """Return resource_arn -> web_acl_arn for ALBs and API Gateway."""
    associations: dict[str, str] = {}
    try:
        wafv2 = get_client("wafv2", region)
        resp = wafv2.list_web_acls(Scope="REGIONAL")
        for acl in resp.get("WebACLs", []):
            acl_arn = acl.get("ARN")
            if not acl_arn:
                continue
            try:
                arns_resp = wafv2.list_resources_for_web_acl(WebACLArn=acl_arn)
                for arn in arns_resp.get("ResourceArns", []):
                    associations[arn] = acl_arn
            except Exception:
                pass
    except Exception:
        pass
    return associations
