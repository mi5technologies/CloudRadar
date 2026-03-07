"""Network / security-group remediation actions."""
from __future__ import annotations

from typing import Any

from cspm.utils.aws_helpers import get_client
from cspm.utils.logger import get_logger

logger = get_logger(__name__)

_OPEN_CIDRS = {"0.0.0.0/0", "::/0"}


def revoke_open_ingress(
    sg_id: str,
    dry_run: bool = True,
    region: str = "us-east-1",
) -> dict:
    """Revoke all inbound rules on *sg_id* that allow traffic from 0.0.0.0/0 or ::/0."""
    actions: list[dict[str, Any]] = []
    try:
        ec2 = get_client("ec2", region)
        resp = ec2.describe_security_groups(GroupIds=[sg_id])
        groups = resp.get("SecurityGroups", [])
        if not groups:
            return {
                "applied": False,
                "dry_run": dry_run,
                "actions": [],
                "error": f"Security group {sg_id} not found",
            }

        sg = groups[0]
        open_rules: list[dict[str, Any]] = []
        for rule in sg.get("IpPermissions", []):
            open_ranges = [r for r in rule.get("IpRanges", []) if r.get("CidrIp") in _OPEN_CIDRS]
            open_v6_ranges = [r for r in rule.get("Ipv6Ranges", []) if r.get("CidrIpv6") in _OPEN_CIDRS]
            if open_ranges or open_v6_ranges:
                filtered_rule = dict(rule)
                if open_ranges:
                    filtered_rule["IpRanges"] = open_ranges
                else:
                    filtered_rule.pop("IpRanges", None)
                if open_v6_ranges:
                    filtered_rule["Ipv6Ranges"] = open_v6_ranges
                else:
                    filtered_rule.pop("Ipv6Ranges", None)
                filtered_rule.pop("UserIdGroupPairs", None)
                filtered_rule.pop("PrefixListIds", None)
                open_rules.append(filtered_rule)
                actions.append({
                    "action": "ec2:RevokeSecurityGroupIngress",
                    "sg_id": sg_id,
                    "rule": {
                        "protocol": rule.get("IpProtocol"),
                        "from_port": rule.get("FromPort"),
                        "to_port": rule.get("ToPort"),
                        "open_cidrs": [r.get("CidrIp") for r in open_ranges]
                        + [r.get("CidrIpv6") for r in open_v6_ranges],
                    },
                })

        if not open_rules:
            return {
                "applied": False,
                "dry_run": dry_run,
                "actions": [],
                "error": None,
                "detail": "No open ingress rules found",
            }

        if not dry_run:
            ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=open_rules)
            logger.info("Revoked %d open ingress rules from %s", len(open_rules), sg_id)
        else:
            logger.info(
                "DRY-RUN: would revoke %d open ingress rules from %s",
                len(open_rules),
                sg_id,
            )

        return {"applied": not dry_run, "dry_run": dry_run, "actions": actions, "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.error("revoke_open_ingress failed for %s: %s", sg_id, exc)
        return {"applied": False, "dry_run": dry_run, "actions": actions, "error": str(exc)}
