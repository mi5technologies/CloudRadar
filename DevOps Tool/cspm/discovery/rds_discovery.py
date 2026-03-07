"""RDS instance discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        rds = get_client("rds", region)
        paginator = rds.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            for db in page.get("DBInstances", []):
                assets.append({
                    "id": db.get("DBInstanceIdentifier"),
                    "type": "rds",
                    "region": region,
                    "engine": db.get("Engine"),
                    "publicly_accessible": db.get("PubliclyAccessible", False),
                    "storage_encrypted": db.get("StorageEncrypted", False),
                    "tags": _tags_from_list(db.get("TagList", [])),
                })
    except Exception:
        pass
    return assets


def _tags_from_list(tag_list: list) -> dict:
    return {t["Key"]: t["Value"] for t in tag_list}
