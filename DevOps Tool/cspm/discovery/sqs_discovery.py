"""SQS queue discovery."""
from typing import Any
import json

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        sqs = get_client("sqs", region)
        paginator = sqs.get_paginator("list_queues")
        for page in paginator.paginate():
            for url in page.get("QueueUrls", []):
                try:
                    attrs_resp = sqs.get_queue_attributes(
                        QueueUrl=url,
                        AttributeNames=[
                            "QueueArn", "SqsManagedSseEnabled", "KmsMasterKeyId", "Policy",
                            "RedrivePolicy", "VisibilityTimeout",
                        ],
                    )
                    attrs = attrs_resp.get("Attributes", {})
                    encrypted = bool(attrs.get("KmsMasterKeyId")) or attrs.get("SqsManagedSseEnabled") == "true"
                    public_policy = _is_public_policy(attrs.get("Policy"))
                    name = url.split("/")[-1]
                    redrive = attrs.get("RedrivePolicy")
                    try:
                        redrive_parsed = json.loads(redrive) if isinstance(redrive, str) and redrive else {}
                    except Exception:
                        redrive_parsed = {}
                    assets.append({
                        "id": attrs.get("QueueArn") or url,
                        "name": name,
                        "type": "sqs",
                        "region": region,
                        "url": url,
                        "encrypted": encrypted,
                        "kms_key_id": attrs.get("KmsMasterKeyId"),
                        "public_policy": public_policy,
                        "is_fifo": name.endswith(".fifo"),
                        "redrive_policy": redrive_parsed,
                        "visibility_timeout_sec": int(attrs.get("VisibilityTimeout", 0) or 0),
                    })
                except Exception:
                    pass
    except Exception:
        pass
    return assets


def _is_public_policy(policy_str) -> bool:
    if not policy_str:
        return False
    try:
        doc = json.loads(policy_str)
        for stmt in doc.get("Statement", []):
            principal = stmt.get("Principal")
            if principal == "*":
                return stmt.get("Effect", "") == "Allow"
            if isinstance(principal, dict) and principal.get("AWS") == "*":
                return stmt.get("Effect", "") == "Allow"
    except Exception:
        pass
    return False
