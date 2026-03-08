"""Attack path analyzer.

Identifies multi-hop risk chains from a snapshot of cloud assets and findings.
"""
from __future__ import annotations

from typing import Any

from cspm.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _findings_by_type(findings: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for f in findings:
        rt = (f.get("resource_type") or "").lower()
        index.setdefault(rt, []).append(f)
    return index


def _has_finding(findings: list[dict], rule_fragment: str) -> bool:
    frag = rule_fragment.lower()
    return any(frag in (f.get("rule_id") or "").lower() for f in findings)


def _finding_resource_ids(findings: list[dict], rule_fragment: str) -> set[str]:
    frag = rule_fragment.lower()
    return {
        f.get("resource_id") or f.get("resource") or ""
        for f in findings
        if frag in (f.get("rule_id") or "").lower()
    }


def _get_assets(assets: dict, key: str) -> list[dict]:
    val = assets.get(key, [])
    return val if isinstance(val, list) else []


# ---------------------------------------------------------------------------
# Individual path checks
# ---------------------------------------------------------------------------


def _check_ec2_sg_iam_s3(
    assets: dict,
    findings_by_type: dict[str, list[dict]],
    all_findings: list[dict],
) -> list[dict]:
    """Internet-exposed EC2 + open SG → IAM role with wildcard → S3 without encryption."""
    paths: list[dict] = []
    ec2_public = _finding_resource_ids(all_findings, "ec2_public")
    if not ec2_public:
        return paths

    sg_open = _finding_resource_ids(all_findings, "security_group_open")
    iam_wildcard = _finding_resource_ids(all_findings, "iam_wildcard")
    s3_no_enc = _finding_resource_ids(all_findings, "s3_encryption")

    if not sg_open or not iam_wildcard:
        return paths

    for ec2_id in ec2_public:
        ec2_assets = _get_assets(assets, "ec2_instances")
        ec2_asset = next((a for a in ec2_assets if a.get("InstanceId") == ec2_id), {})
        profile = ec2_asset.get("IamInstanceProfile", {})
        profile_arn = (profile.get("Arn") or "") if isinstance(profile, dict) else ""

        path_nodes = [
            {"resource_type": "ec2", "resource_id": ec2_id, "risk": "internet-exposed instance"},
        ]
        if sg_open:
            sample_sg = next(iter(sg_open))
            path_nodes.append({
                "resource_type": "security_group",
                "resource_id": sample_sg,
                "risk": "open inbound 0.0.0.0/0",
            })
        for role_id in iam_wildcard:
            path_nodes.append({
                "resource_type": "iam_role",
                "resource_id": role_id,
                "risk": "wildcard IAM policy (Action: *)",
            })
            break  # one representative
        if s3_no_enc:
            sample_s3 = next(iter(s3_no_enc))
            path_nodes.append({
                "resource_type": "s3",
                "resource_id": sample_s3,
                "risk": "bucket missing encryption",
            })

        paths.append({
            "path": path_nodes,
            "severity": "critical",
            "description": (
                f"Internet-exposed EC2 instance {ec2_id} sits behind an open security group. "
                "Its IAM role has wildcard permissions, allowing an attacker to pivot to "
                "unencrypted S3 buckets and exfiltrate data."
            ),
        })

    return paths


def _check_public_s3_no_encryption(
    assets: dict,
    findings_by_type: dict[str, list[dict]],
    all_findings: list[dict],
) -> list[dict]:
    """Public S3 bucket + missing encryption."""
    paths: list[dict] = []
    public_ids = _finding_resource_ids(all_findings, "s3_public")
    no_enc_ids = _finding_resource_ids(all_findings, "s3_encryption")
    combined = public_ids & no_enc_ids
    for bid in combined:
        paths.append({
            "path": [
                {"resource_type": "s3", "resource_id": bid, "risk": "publicly accessible bucket"},
                {"resource_type": "s3", "resource_id": bid, "risk": "missing server-side encryption"},
            ],
            "severity": "high",
            "description": (
                f"S3 bucket {bid} is publicly accessible AND lacks server-side encryption. "
                "Any sensitive data in this bucket is exposed in cleartext."
            ),
        })
    return paths


def _check_eks_public_no_secrets_encryption(
    assets: dict,
    findings_by_type: dict[str, list[dict]],
    all_findings: list[dict],
) -> list[dict]:
    """EKS cluster with public endpoint + secrets not encrypted."""
    paths: list[dict] = []
    eks_public = _finding_resource_ids(all_findings, "eks_public")
    eks_no_enc = _finding_resource_ids(all_findings, "eks_secret")
    combined = eks_public | eks_no_enc
    for cluster_id in combined:
        nodes = []
        if cluster_id in eks_public:
            nodes.append({
                "resource_type": "eks",
                "resource_id": cluster_id,
                "risk": "public API endpoint enabled",
            })
        if cluster_id in eks_no_enc:
            nodes.append({
                "resource_type": "eks",
                "resource_id": cluster_id,
                "risk": "Kubernetes secrets not encrypted with KMS",
            })
        if len(nodes) >= 1:
            paths.append({
                "path": nodes,
                "severity": "high",
                "description": (
                    f"EKS cluster {cluster_id} exposes its API endpoint publicly "
                    "and/or stores Kubernetes secrets without KMS envelope encryption."
                ),
            })
    return paths


def _check_public_rds_no_encryption(
    assets: dict,
    findings_by_type: dict[str, list[dict]],
    all_findings: list[dict],
) -> list[dict]:
    """Public RDS instance + no encryption at rest."""
    paths: list[dict] = []
    rds_public = _finding_resource_ids(all_findings, "rds_public")
    rds_no_enc = _finding_resource_ids(all_findings, "rds_encrypt")
    combined = rds_public & rds_no_enc
    for db_id in combined:
        paths.append({
            "path": [
                {"resource_type": "rds", "resource_id": db_id, "risk": "publicly accessible RDS"},
                {"resource_type": "rds", "resource_id": db_id, "risk": "RDS storage not encrypted"},
            ],
            "severity": "critical",
            "description": (
                f"RDS instance {db_id} is publicly accessible and its storage is not encrypted. "
                "Database contents can be read directly from the internet."
            ),
        })
    return paths


def _check_blind_spot(
    assets: dict,
    findings_by_type: dict[str, list[dict]],
    all_findings: list[dict],
) -> list[dict]:
    """GuardDuty not enabled + CloudTrail not logging → attacker blind spot."""
    paths: list[dict] = []
    gd_disabled = _has_finding(all_findings, "guardduty")
    ct_disabled = _has_finding(all_findings, "cloudtrail")
    if gd_disabled and ct_disabled:
        nodes = []
        if gd_disabled:
            nodes.append({
                "resource_type": "guardduty",
                "resource_id": "account",
                "risk": "GuardDuty threat detection not enabled",
            })
        if ct_disabled:
            nodes.append({
                "resource_type": "cloudtrail",
                "resource_id": "account",
                "risk": "CloudTrail API logging not active",
            })
        paths.append({
            "path": nodes,
            "severity": "high",
            "description": (
                "GuardDuty is not enabled and CloudTrail is not logging. "
                "An attacker can operate in this account without triggering any alerts "
                "or leaving an audit trail."
            ),
        })
    return paths


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_paths(assets: dict, findings: list[dict]) -> list[dict]:
    """Return a list of attack-path dicts found in *assets* + *findings*.

    Each entry has the shape::

        {
            "path": [{"resource_type": str, "resource_id": str, "risk": str}, ...],
            "severity": "critical" | "high" | "medium",
            "description": str,
        }
    """
    if not findings:
        return []

    findings_by_type = _findings_by_type(findings)
    results: list[dict] = []

    checkers = [
        _check_ec2_sg_iam_s3,
        _check_public_s3_no_encryption,
        _check_eks_public_no_secrets_encryption,
        _check_public_rds_no_encryption,
        _check_blind_spot,
    ]

    for checker in checkers:
        try:
            found = checker(assets, findings_by_type, findings)
            results.extend(found)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Attack path checker %s failed: %s", checker.__name__, exc)

    logger.info("Attack path analysis found %d paths", len(results))
    return results
