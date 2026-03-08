"""Usage and utilisation scanner — CloudWatch (and equivalent) metrics for serverless/resources.

Flags: idle Lambdas (zero invocations), high error rate, throttles, and optional cost drivers.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

_DAYS_LOOKBACK = 14
_ERROR_RATIO_THRESHOLD = 0.05  # 5% error rate
_MIN_INVOCATIONS_FOR_ERROR_RATIO = 10


def _finding(
    rule_id: str,
    resource_type: str,
    resource_id: str,
    resource_name: str,
    title: str,
    severity: str,
    detail: str,
    remediation: str,
    region: str = "global",
    cloud: str = "aws",
    metric_value: float | None = None,
) -> dict[str, Any]:
    f = {
        "rule_id": rule_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": resource_name or resource_id,
        "title": title,
        "severity": severity,
        "detail": detail,
        "remediation": remediation,
        "region": region,
        "cloud": cloud,
        "passed": False,
    }
    if metric_value is not None:
        f["metric_value"] = metric_value
    return f


def _get_metric_sum(
    cw,
    namespace: str,
    metric_name: str,
    dimension_name: str,
    dimension_value: str,
    region: str,
    days: int = _DAYS_LOOKBACK,
) -> float:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    try:
        resp = cw.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
            StartTime=start,
            EndTime=end,
            Period=86400,
            Statistics=["Sum"],
        )
        points = resp.get("Datapoints", [])
        return sum(p.get("Sum", 0) or 0 for p in points)
    except Exception:
        return 0.0


def scan_usage(
    assets: dict[str, list[dict[str, Any]]],
    region: str = "us-east-1",
    cloud: str = "aws",
    days_lookback: int = _DAYS_LOOKBACK,
) -> list[dict[str, Any]]:
    """Run usage-based checks from CloudWatch metrics. AWS Lambda only for now."""
    findings: list[dict[str, Any]] = []
    if cloud != "aws":
        return findings

    try:
        from cspm.utils.aws_helpers import get_client
        cw = get_client("cloudwatch", region)
    except Exception:
        return findings

    lambdas = assets.get("lambda", [])
    if not lambdas:
        return findings

    for fn in lambdas[:100]:
        fid = fn.get("id") or fn.get("FunctionName") or ""
        name = fn.get("name") or fid
        if not fid:
            continue

        invocations = _get_metric_sum(
            cw, "AWS/Lambda", "Invocations", "FunctionName", fid, region, days_lookback
        )
        errors = _get_metric_sum(
            cw, "AWS/Lambda", "Errors", "FunctionName", fid, region, days_lookback
        )
        throttles = _get_metric_sum(
            cw, "AWS/Lambda", "Throttles", "FunctionName", fid, region, days_lookback
        )
        duration_avg = 0.0
        try:
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days_lookback)
            resp = cw.get_metric_statistics(
                Namespace="AWS/Lambda",
                MetricName="Duration",
                Dimensions=[{"Name": "FunctionName", "Value": fid}],
                StartTime=start,
                EndTime=end,
                Period=86400,
                Statistics=["Average", "Maximum"],
            )
            points = resp.get("Datapoints", [])
            if points:
                duration_avg = sum(p.get("Average", 0) or 0 for p in points) / len(points)
        except Exception:
            pass

        if invocations == 0:
            findings.append(_finding(
                "usage.lambda_idle", "lambda", fid, name,
                "Lambda has no invocations in the last {} days".format(days_lookback),
                SEVERITY_LOW,
                "Function appears unused. Consider removing or archiving if no longer needed.",
                "Delete the function if obsolete, or verify triggers and IAM permissions.",
                region=region, cloud="aws", metric_value=0,
            ))
        elif invocations >= _MIN_INVOCATIONS_FOR_ERROR_RATIO and errors > 0:
            ratio = errors / invocations
            if ratio >= _ERROR_RATIO_THRESHOLD:
                findings.append(_finding(
                    "usage.lambda_errors_high", "lambda", fid, name,
                    "Lambda error rate is high ({}% over {} days)".format(
                        round(ratio * 100, 1), days_lookback
                    ),
                    SEVERITY_MEDIUM,
                    "{} errors out of {} invocations. Check CloudWatch Logs and alarms.".format(
                        int(errors), int(invocations)
                    ),
                    "Review Lambda logs and metrics; fix code or input issues; add DLQ for async.",
                    region=region, cloud="aws", metric_value=ratio,
                ))
        if throttles > 0:
            findings.append(_finding(
                "usage.lambda_throttles", "lambda", fid, name,
                "Lambda has throttled invocations",
                SEVERITY_LOW,
                "{} throttles in the last {} days. May cause dropped events or retries.".format(
                    int(throttles), days_lookback
                ),
                "Increase reserved concurrency or account concurrency; optimize duration and memory.",
                region=region, cloud="aws", metric_value=throttles,
            ))

    return findings
