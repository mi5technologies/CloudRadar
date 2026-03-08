"""Tests for S3 scanner using moto."""
import pytest

moto = pytest.importorskip("moto", reason="moto not installed")

try:
    from moto import mock_aws
except ImportError:
    from moto import mock_s3 as mock_aws  # moto v4 fallback

import boto3
from cspm.scanners.s3_scanner import scan_s3


@mock_aws
def test_scan_s3_no_encryption():
    """Bucket without encryption -> encryption_enabled=False."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="unencrypted-bucket")

    assets = [{"id": "unencrypted-bucket", "name": "unencrypted-bucket", "type": "s3"}]
    enriched = scan_s3(assets, "us-east-1")

    assert len(enriched) == 1
    assert enriched[0]["encryption_enabled"] is False


@mock_aws
def test_scan_s3_with_aes256_encryption():
    """Bucket with AES-256 SSE -> encryption_enabled=True."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="encrypted-bucket")
    s3.put_bucket_encryption(
        Bucket="encrypted-bucket",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    assets = [{"id": "encrypted-bucket", "name": "encrypted-bucket", "type": "s3"}]
    enriched = scan_s3(assets, "us-east-1")

    assert len(enriched) == 1
    assert enriched[0]["encryption_enabled"] is True


@mock_aws
def test_scan_s3_public_access_block_present():
    """Bucket with public access block set -> block_public_acls=True."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="blocked-bucket")
    s3.put_public_access_block(
        Bucket="blocked-bucket",
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    assets = [{"id": "blocked-bucket", "name": "blocked-bucket", "type": "s3"}]
    enriched = scan_s3(assets, "us-east-1")

    assert enriched[0]["block_public_acls"] is True
    assert enriched[0]["block_public_policy"] is True


@mock_aws
def test_scan_s3_empty_asset_list():
    """Empty input returns empty output."""
    result = scan_s3([], "us-east-1")
    assert result == []


@mock_aws
def test_scan_s3_multiple_buckets_mixed():
    """Multiple buckets: encrypted and unencrypted handled independently."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="bucket-a")
    s3.create_bucket(Bucket="bucket-b")
    s3.put_bucket_encryption(
        Bucket="bucket-b",
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    assets = [
        {"id": "bucket-a", "name": "bucket-a", "type": "s3"},
        {"id": "bucket-b", "name": "bucket-b", "type": "s3"},
    ]
    enriched = scan_s3(assets, "us-east-1")
    by_name = {a["name"]: a for a in enriched}

    assert by_name["bucket-a"]["encryption_enabled"] is False
    assert by_name["bucket-b"]["encryption_enabled"] is True
