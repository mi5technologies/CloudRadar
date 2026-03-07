"""IAM remediation actions."""
from __future__ import annotations

import json
from typing import Any

from cspm.utils.aws_helpers import get_client
from cspm.utils.logger import get_logger

logger = get_logger(__name__)


def detach_admin_policies(
    role_name: str,
    dry_run: bool = True,
    region: str = "us-east-1",
) -> dict:
    """Detach managed policies whose name contains 'Admin' or 'Full' from *role_name*."""
    actions: list[dict[str, Any]] = []
    try:
        iam = get_client("iam", region)
        paginator = iam.get_paginator("list_attached_role_policies")
        admin_policies = []
        for page in paginator.paginate(RoleName=role_name):
            for policy in page.get("AttachedPolicies", []):
                name = policy.get("PolicyName", "")
                if "Admin" in name or "Full" in name:
                    admin_policies.append(policy)

        if not admin_policies:
            return {
                "applied": False,
                "dry_run": dry_run,
                "actions": [],
                "error": None,
                "detail": "No admin/full-access policies found",
            }

        for policy in admin_policies:
            action = {
                "action": "iam:DetachRolePolicy",
                "role": role_name,
                "policy_arn": policy["PolicyArn"],
                "policy_name": policy["PolicyName"],
            }
            actions.append(action)
            if not dry_run:
                iam.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])
                logger.info("Detached %s from role %s", policy["PolicyArn"], role_name)
            else:
                logger.info(
                    "DRY-RUN: would detach %s from role %s",
                    policy["PolicyArn"],
                    role_name,
                )

        return {"applied": not dry_run, "dry_run": dry_run, "actions": actions, "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.error("detach_admin_policies failed for role %s: %s", role_name, exc)
        return {"applied": False, "dry_run": dry_run, "actions": actions, "error": str(exc)}


def remove_inline_wildcard_policies(
    role_name: str,
    dry_run: bool = True,
    region: str = "us-east-1",
) -> dict:
    """Delete inline policies on *role_name* that contain ``"Action": "*"``."""
    actions: list[dict[str, Any]] = []
    try:
        iam = get_client("iam", region)
        paginator = iam.get_paginator("list_role_policies")
        wildcard_policies = []
        for page in paginator.paginate(RoleName=role_name):
            for policy_name in page.get("PolicyNames", []):
                resp = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                doc = resp.get("PolicyDocument", {})
                if isinstance(doc, str):
                    doc = json.loads(doc)
                for statement in doc.get("Statement", []):
                    action_val = statement.get("Action", [])
                    if action_val == "*" or (isinstance(action_val, list) and "*" in action_val):
                        wildcard_policies.append(policy_name)
                        break

        if not wildcard_policies:
            return {
                "applied": False,
                "dry_run": dry_run,
                "actions": [],
                "error": None,
                "detail": "No wildcard inline policies found",
            }

        for policy_name in wildcard_policies:
            action = {
                "action": "iam:DeleteRolePolicy",
                "role": role_name,
                "policy_name": policy_name,
            }
            actions.append(action)
            if not dry_run:
                iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                logger.info("Deleted inline policy %s from role %s", policy_name, role_name)
            else:
                logger.info(
                    "DRY-RUN: would delete inline policy %s from role %s",
                    policy_name,
                    role_name,
                )

        return {"applied": not dry_run, "dry_run": dry_run, "actions": actions, "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.error("remove_inline_wildcard_policies failed for role %s: %s", role_name, exc)
        return {"applied": False, "dry_run": dry_run, "actions": actions, "error": str(exc)}
