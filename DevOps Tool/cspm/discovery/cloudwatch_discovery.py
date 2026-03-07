"""CloudWatch: check for critical CIS security metric filters."""
from typing import Any

from cspm.utils.aws_helpers import get_client

# Key CIS-required monitoring checks (by keyword in filter pattern)
_REQUIRED_CHECKS = [
    {"id": "cw_root_usage", "keyword": "Root", "title": "Root account usage alarm"},
    {"id": "cw_iam_policy_change", "keyword": "DeleteGroupPolicy", "title": "IAM policy changes alarm"},
    {"id": "cw_cloudtrail_change", "keyword": "StopLogging", "title": "CloudTrail config changes alarm"},
    {"id": "cw_sg_change", "keyword": "AuthorizeSecurityGroupIngress", "title": "Security group changes alarm"},
    {"id": "cw_nacl_change", "keyword": "CreateNetworkAcl", "title": "NACL changes alarm"},
    {"id": "cw_vpc_change", "keyword": "CreateVpc", "title": "VPC changes alarm"},
    {"id": "cw_kms_disable", "keyword": "DisableKey", "title": "KMS key disablement alarm"},
    {"id": "cw_s3_bucket_policy", "keyword": "PutBucketPolicy", "title": "S3 bucket policy changes alarm"},
    {"id": "cw_config_change", "keyword": "StopConfigurationRecorder", "title": "AWS Config changes alarm"},
]


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        logs = get_client("logs", region)
        existing_patterns: list[str] = []
        paginator = logs.get_paginator("describe_metric_filters")
        for page in paginator.paginate():
            for f in page.get("metricFilters", []):
                existing_patterns.append(f.get("filterPattern", ""))

        for check in _REQUIRED_CHECKS:
            keyword = check["keyword"]
            found = any(keyword in p for p in existing_patterns)
            assets.append({
                "id": f"{check['id']}-{region}",
                "type": "cloudwatch_alarm",
                "region": region,
                "check_id": check["id"],
                "title": check["title"],
                "filter_exists": found,
            })
    except Exception:
        pass
    return assets
