"""SNS discovery: list topics with encryption and policy details."""
import json
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    try:
        client = get_client("sns", region)
        paginator = client.get_paginator("list_topics")
        topics = []
        for page in paginator.paginate():
            for t in page.get("Topics", []):
                arn = t.get("TopicArn", "")
                topic = _enrich(client, arn, region)
                topics.append(topic)
        return topics
    except Exception:
        return []


def _enrich(client, arn: str, region: str) -> dict[str, Any]:
    name = arn.split(":")[-1] if arn else ""
    has_kms = False
    public_policy = False

    try:
        attrs = client.get_topic_attributes(TopicArn=arn).get("Attributes", {})
        has_kms = bool(attrs.get("KmsMasterKeyId"))
        policy_str = attrs.get("Policy")
        if policy_str:
            public_policy = _is_public_policy(policy_str)
    except Exception:
        pass

    return {
        "id": arn,
        "name": name,
        "type": "sns",
        "region": region,
        "has_kms": has_kms,
        "public_policy": public_policy,
    }


def _is_public_policy(policy_str: str) -> bool:
    try:
        policy = json.loads(policy_str)
        for stmt in policy.get("Statement", []):
            if stmt.get("Effect") != "Allow":
                continue
            principal = stmt.get("Principal")
            if principal == "*":
                return True
            if isinstance(principal, dict):
                aws = principal.get("AWS", [])
                if aws == "*" or (isinstance(aws, list) and "*" in aws):
                    return True
    except Exception:
        pass
    return False
