"""S3 bucket discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        s3 = get_client("s3", region)
        buckets = s3.list_buckets().get("Buckets", [])
        for b in buckets:
            name = b.get("Name")
            loc = _get_bucket_region(s3, name)
            assets.append({
                "id": name,
                "name": name,
                "type": "s3",
                "region": loc or region,
                "created": b.get("CreationDate").isoformat() if b.get("CreationDate") else None,
                "tags": {},
            })
    except Exception:
        pass
    return assets


def _get_bucket_region(s3_client, bucket: str) -> str | None:
    try:
        loc = s3_client.get_bucket_location(Bucket=bucket)
        return loc.get("LocationConstraint") or "us-east-1"
    except Exception:
        return None
