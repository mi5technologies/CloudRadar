"""DynamoDB table discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        ddb = get_client("dynamodb", region)
        paginator = ddb.get_paginator("list_tables")
        for page in paginator.paginate():
            for table_name in page.get("TableNames", []):
                try:
                    resp = ddb.describe_table(TableName=table_name)
                    table = resp.get("Table", {})
                    sse = table.get("SSEDescription", {})
                    pitr = False
                    try:
                        pitr_resp = ddb.describe_continuous_backups(TableName=table_name)
                        pitr_spec = pitr_resp.get("ContinuousBackupsDescription", {})
                        pitr = pitr_spec.get("PointInTimeRecoveryDescription", {}).get("PointInTimeRecoveryStatus") == "ENABLED"
                    except Exception:
                        pass
                    stream_spec = table.get("StreamSpecification") or {}
                    assets.append({
                        "id": table.get("TableArn") or table_name,
                        "name": table_name,
                        "type": "dynamodb",
                        "region": region,
                        "status": table.get("TableStatus"),
                        "encryption_enabled": sse.get("Status") in ("ENABLED", "UPDATING"),
                        "pitr_enabled": pitr,
                        "stream_enabled": stream_spec.get("StreamEnabled") is True,
                        "billing_mode": table.get("BillingModeSummary", {}).get("BillingMode", "PROVISIONED"),
                        "item_count": table.get("ItemCount", 0),
                    })
                except Exception:
                    pass
    except Exception:
        pass
    return assets
