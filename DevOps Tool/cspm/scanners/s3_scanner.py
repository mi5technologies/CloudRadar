"""S3 scanner: bucket policy, public access block, encryption."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def scan_s3(assets: list[dict[str, Any]], region: str) -> list[dict[str, Any]]:
    enriched = []
    s3 = get_client("s3", region)
    for a in assets:
        a = dict(a)
        name = a.get("name") or a.get("id")
        if not name:
            enriched.append(a)
            continue
        try:
            try:
                pub = s3.get_public_access_block(Bucket=name)
                block = pub.get("PublicAccessBlockConfiguration", {})
                a["block_public_acls"] = block.get("BlockPublicAcls") and block.get("IgnorePublicAcls")
                a["block_public_policy"] = block.get("BlockPublicPolicy")
            except Exception:
                a["block_public_acls"] = False
                a["block_public_policy"] = False
            try:
                enc = s3.get_bucket_encryption(Bucket=name)
                a["encryption_enabled"] = bool(enc.get("ServerSideEncryptionConfiguration", {}).get("Rules"))
            except Exception:
                a["encryption_enabled"] = False
        except Exception:
            pass
        enriched.append(a)
    return enriched
