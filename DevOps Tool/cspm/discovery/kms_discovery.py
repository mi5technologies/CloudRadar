"""KMS key discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        kms = get_client("kms", region)
        paginator = kms.get_paginator("list_keys")
        for page in paginator.paginate():
            for key_item in page.get("Keys", []):
                key_id = key_item.get("KeyId")
                try:
                    meta = kms.describe_key(KeyId=key_id).get("KeyMetadata", {})
                    if meta.get("KeyManager") != "CUSTOMER":
                        continue
                    rotation_status = False
                    try:
                        rot = kms.get_key_rotation_status(KeyId=key_id)
                        rotation_status = rot.get("KeyRotationEnabled", False)
                    except Exception:
                        pass
                    assets.append({
                        "id": key_id,
                        "arn": meta.get("Arn"),
                        "type": "kms",
                        "region": region,
                        "description": meta.get("Description", ""),
                        "enabled": meta.get("Enabled", False),
                        "key_state": meta.get("KeyState"),
                        "key_rotation_enabled": rotation_status,
                        "multi_region": meta.get("MultiRegion", False),
                    })
                except Exception:
                    pass
    except Exception:
        pass
    return assets
