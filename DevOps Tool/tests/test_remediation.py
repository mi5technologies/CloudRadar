"""Tests for remediation engine using moto."""
import pytest

moto = pytest.importorskip("moto", reason="moto not installed")

try:
    from moto import mock_aws
except ImportError:
    from moto import mock_s3 as mock_aws  # moto v4 fallback

import boto3
from cspm.remediation.remediation_engine import apply_fix


def _make_finding(resource_id: str, rule_id: str = "s3_encryption", resource_type: str = "s3") -> dict:
    return {
        "rule_id": rule_id,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "severity": "high",
    }


# ---------------------------------------------------------------------------
# S3 encryption remediation
# ---------------------------------------------------------------------------

@mock_aws
def test_apply_fix_s3_encryption_dry_run_does_not_encrypt():
    """dry_run=True must not modify the bucket."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="dry-bucket")

    result = apply_fix(_make_finding("dry-bucket"), dry_run=True)

    assert result["applied"] is False
    assert result.get("dry_run") is True

    # Bucket must still have no encryption
    try:
        s3.get_bucket_encryption(Bucket="dry-bucket")
        encrypted = True
    except s3.exceptions.from_code("ServerSideEncryptionConfigurationNotFoundError").__class__:
        encrypted = False
    except Exception:
        encrypted = False

    assert not encrypted


@mock_aws
def test_apply_fix_s3_encryption_applies_when_not_dry_run():
    """dry_run=False must enable AES-256 encryption on the bucket."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="fix-bucket")

    result = apply_fix(_make_finding("fix-bucket"), dry_run=False)

    assert result["applied"] is True

    enc = s3.get_bucket_encryption(Bucket="fix-bucket")
    rules = enc["ServerSideEncryptionConfiguration"]["Rules"]
    assert len(rules) == 1
    assert rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] == "AES256"


@mock_aws
def test_apply_fix_s3_idempotent():
    """Calling apply_fix twice on an already-encrypted bucket should succeed both times."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="already-encrypted")
    s3.put_bucket_encryption(
        Bucket="already-encrypted",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    result1 = apply_fix(_make_finding("already-encrypted"), dry_run=False)
    result2 = apply_fix(_make_finding("already-encrypted"), dry_run=False)

    assert result1["applied"] is True
    assert result2["applied"] is True


# ---------------------------------------------------------------------------
# S3 public access block remediation
# ---------------------------------------------------------------------------

@mock_aws
def test_apply_fix_s3_public_block_dry_run():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="public-bucket")

    result = apply_fix(_make_finding("public-bucket", rule_id="s3_public_block"), dry_run=True)

    assert result["applied"] is False
    assert result.get("dry_run") is True


@mock_aws
def test_apply_fix_s3_public_block_applies():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="public-bucket2")

    result = apply_fix(_make_finding("public-bucket2", rule_id="s3_public_block"), dry_run=False)

    assert result["applied"] is True

    cfg = s3.get_public_access_block(Bucket="public-bucket2")["PublicAccessBlockConfiguration"]
    assert cfg["BlockPublicAcls"] is True
    assert cfg["BlockPublicPolicy"] is True


# ---------------------------------------------------------------------------
# Missing resource_id
# ---------------------------------------------------------------------------

def test_apply_fix_no_resource_id_returns_error():
    result = apply_fix({"rule_id": "s3_encryption", "resource_type": "s3"})
    assert result["applied"] is False
    assert "resource_id" in result["message"].lower() or "No" in result["message"]


# ---------------------------------------------------------------------------
# Unsupported resource type
# ---------------------------------------------------------------------------

def test_apply_fix_unsupported_resource_type():
    result = apply_fix({"rule_id": "some_rule", "resource_id": "res-1", "resource_type": "lambda"})
    assert result["applied"] is False
