"""Secrets Manager discovery: list secrets with rotation details."""
from datetime import datetime, timezone
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    try:
        client = get_client("secretsmanager", region)
        paginator = client.get_paginator("list_secrets")
        secrets = []
        for page in paginator.paginate():
            for s in page.get("SecretList", []):
                secret = _enrich(client, s, region)
                secrets.append(secret)
        return secrets
    except Exception:
        return []


def _enrich(client, s: dict, region: str) -> dict[str, Any]:
    arn = s.get("ARN", "")
    name = s.get("Name", "")
    rotation_enabled = s.get("RotationEnabled", False)
    last_rotated_raw = s.get("LastRotatedDate")
    kms_key_id = s.get("KmsKeyId")
    tags = {t["Key"]: t["Value"] for t in s.get("Tags", [])}

    last_rotated_date: str | None = None
    days_since_rotation: int | None = None

    try:
        detail = client.describe_secret(SecretId=arn)
        if not last_rotated_raw:
            last_rotated_raw = detail.get("LastRotatedDate")
        if not kms_key_id:
            kms_key_id = detail.get("KmsKeyId")
    except Exception:
        pass

    if last_rotated_raw:
        if isinstance(last_rotated_raw, datetime):
            last_rotated_dt = last_rotated_raw
        else:
            last_rotated_dt = datetime.fromisoformat(str(last_rotated_raw))
        if last_rotated_dt.tzinfo is None:
            last_rotated_dt = last_rotated_dt.replace(tzinfo=timezone.utc)
        last_rotated_date = last_rotated_dt.isoformat()
        days_since_rotation = (datetime.now(timezone.utc) - last_rotated_dt).days

    return {
        "id": arn,
        "name": name,
        "type": "secretsmanager",
        "region": region,
        "rotation_enabled": rotation_enabled,
        "last_rotated_date": last_rotated_date,
        "days_since_rotation": days_since_rotation,
        "kms_key_id": kms_key_id,
        "tags": tags,
    }
