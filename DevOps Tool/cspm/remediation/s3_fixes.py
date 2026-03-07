"""S3 remediation actions."""
from __future__ import annotations

from cspm.utils.aws_helpers import get_client
from cspm.utils.logger import get_logger

logger = get_logger(__name__)


def fix_public_access(
    bucket: str,
    dry_run: bool = True,
    region: str = "us-east-1",
) -> dict:
    """Block all public access on *bucket*.

    When *dry_run* is True the change is described but not applied.
    """
    action = {
        "action": "s3:PutPublicAccessBlock",
        "bucket": bucket,
        "settings": {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    }
    if dry_run:
        logger.info("DRY-RUN: would apply %s on %s", action["action"], bucket)
        return {"applied": False, "dry_run": True, "actions": [action], "error": None}

    try:
        s3 = get_client("s3", region)
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        logger.info("Applied public access block on bucket %s", bucket)
        return {"applied": True, "dry_run": False, "actions": [action], "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.error("fix_public_access failed for %s: %s", bucket, exc)
        return {"applied": False, "dry_run": False, "actions": [action], "error": str(exc)}


def fix_encryption(
    bucket: str,
    dry_run: bool = True,
    region: str = "us-east-1",
) -> dict:
    """Enable AES256 server-side encryption on *bucket*."""
    action = {
        "action": "s3:PutBucketEncryption",
        "bucket": bucket,
        "algorithm": "AES256",
    }
    if dry_run:
        logger.info("DRY-RUN: would apply %s on %s", action["action"], bucket)
        return {"applied": False, "dry_run": True, "actions": [action], "error": None}

    try:
        s3 = get_client("s3", region)
        s3.put_bucket_encryption(
            Bucket=bucket,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        },
                        "BucketKeyEnabled": True,
                    }
                ]
            },
        )
        logger.info("Applied AES256 encryption on bucket %s", bucket)
        return {"applied": True, "dry_run": False, "actions": [action], "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.error("fix_encryption failed for %s: %s", bucket, exc)
        return {"applied": False, "dry_run": False, "actions": [action], "error": str(exc)}
