"""CloudTrail trail discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        ct = get_client("cloudtrail", region)
        resp = ct.describe_trails(includeShadowTrails=False)
        for trail in resp.get("trailList", []):
            trail_name = trail.get("Name")
            logging_enabled = False
            try:
                status = ct.get_trail_status(Name=trail_name)
                logging_enabled = status.get("IsLogging", False)
            except Exception:
                pass
            assets.append({
                "id": trail.get("TrailARN") or trail_name,
                "name": trail_name,
                "type": "cloudtrail",
                "region": region,
                "is_multi_region": trail.get("IsMultiRegionTrail", False),
                "log_file_validation_enabled": trail.get("LogFileValidationEnabled", False),
                "include_global_service_events": trail.get("IncludeGlobalServiceEvents", False),
                "s3_bucket": trail.get("S3BucketName"),
                "cloud_watch_logs_log_group_arn": trail.get("CloudWatchLogsLogGroupArn"),
                "logging_enabled": logging_enabled,
                "kms_key_id": trail.get("KMSKeyId"),
                "cloudwatch_integrated": bool(trail.get("CloudWatchLogsLogGroupArn")),
            })
    except Exception:
        pass
    return assets
