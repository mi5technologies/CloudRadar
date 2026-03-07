"""IAM scanner: admin policy, wildcard actions."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def scan_iam(users: list[dict], roles: list[dict], region: str) -> tuple[list[dict], list[dict]]:
    iam = get_client("iam", region)
    admin_arns = _get_admin_policy_arns(iam)
    enriched_roles = []
    for r in roles:
        r = dict(r)
        r["has_admin_policy"] = _role_has_admin(iam, r.get("id"), admin_arns)
        r["has_wildcard_action"] = _role_has_wildcard(iam, r.get("id"))
        enriched_roles.append(r)
    return users, enriched_roles


def _get_admin_policy_arns(iam_client) -> set:
    out = set()
    try:
        paginator = iam_client.get_paginator("list_policies")
        for page in paginator.paginate(Scope="AWS"):
            for p in page.get("Policies", []):
                if "Admin" in (p.get("PolicyName") or ""):
                    out.add(p.get("Arn"))
        return out
    except Exception:
        return out


def _role_has_admin(iam_client, role_name: str | None, admin_arns: set) -> bool:
    if not role_name:
        return False
    try:
        att = iam_client.list_attached_role_policies(RoleName=role_name)
        for p in att.get("AttachedPolicies", []):
            if p.get("PolicyArn") in admin_arns:
                return True
        return False
    except Exception:
        return False


def _role_has_wildcard(iam_client, role_name: str | None) -> bool:
    if not role_name:
        return False
    try:
        att = iam_client.list_attached_role_policies(RoleName=role_name)
        for p in att.get("AttachedPolicies", []):
            doc = iam_client.get_policy_version(PolicyArn=p["PolicyArn"], VersionId=iam_client.get_policy(PolicyArn=p["PolicyArn"])["Policy"]["DefaultVersionId"])
            # simplified: check for "*" in Action
            import json
            d = json.loads(doc["PolicyVersion"]["Document"])
            if _doc_has_wildcard_action(d):
                return True
        return False
    except Exception:
        return False


def _doc_has_wildcard_action(d: dict) -> bool:
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "Action" and (v == "*" or (isinstance(v, list) and "*" in v)):
                return True
            if _doc_has_wildcard_action(v):
                return True
    elif isinstance(d, list):
        for x in d:
            if _doc_has_wildcard_action(x):
                return True
    return False
