"""Remediation engine: apply fixes for known finding types."""
from typing import Any

import boto3


def apply_fix(finding: dict, dry_run: bool = True) -> dict:
    """Apply a remediation for the given finding.

    Returns a result dict with keys: applied (bool), message (str).
    When dry_run=True no changes are made.
    """
    resource_type = finding.get("resource_type", "")
    resource_id = finding.get("resource_id", "")
    rule_id = finding.get("rule_id", "")

    if not resource_id:
        return {"applied": False, "message": "No resource_id in finding"}

    if resource_type == "s3":
        return _fix_s3(resource_id, rule_id, dry_run)

    return {"applied": False, "message": f"No remediation implemented for resource_type={resource_type!r}"}


def _fix_s3(bucket: str, rule_id: str, dry_run: bool) -> dict:
    if rule_id in ("s3_encryption", "ebs_volume_not_encrypted") or "encrypt" in rule_id:
        if dry_run:
            return {"applied": False, "dry_run": True, "message": f"Would enable AES-256 encryption on s3://{bucket}"}
        try:
            s3 = boto3.client("s3")
            s3.put_bucket_encryption(
                Bucket=bucket,
                ServerSideEncryptionConfiguration={
                    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
                },
            )
            return {"applied": True, "message": f"Enabled AES-256 encryption on s3://{bucket}"}
        except Exception as exc:
            return {"applied": False, "message": str(exc)}

    if rule_id == "s3_public_block":
        if dry_run:
            return {"applied": False, "dry_run": True, "message": f"Would enable public access block on s3://{bucket}"}
        try:
            s3 = boto3.client("s3")
            s3.put_public_access_block(
                Bucket=bucket,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )
            return {"applied": True, "message": f"Enabled public access block on s3://{bucket}"}
        except Exception as exc:
            return {"applied": False, "message": str(exc)}

    return {"applied": False, "message": f"No S3 remediation for rule {rule_id!r}"}
