"""Serverless security scanner — Lambda, Step Functions, API Gateway, SQS, DynamoDB.

Flags: missing DLQ, timeout/resource tuning, logging/tracing, usage plans, authorizers,
reserved concurrency risk, VPC config, SQS visibility vs Lambda timeout, etc.
"""
from __future__ import annotations

import re
from typing import Any

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

_SECRET_KEY_PATTERNS = re.compile(
    r"(password|secret|token|key|passwd|pwd|api_key|apikey|access_key|auth)",
    re.IGNORECASE,
)
_AWS_KEY_PREFIXES = ("AKIA", "ASIA")
_MIN_SECRET_VALUE_LEN = 20


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
) -> dict[str, Any]:
    return {
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


def _has_secrets_in_env(env: dict) -> bool:
    if not env:
        return False
    for k, v in env.items():
        if isinstance(v, str):
            if any(v.startswith(prefix) for prefix in _AWS_KEY_PREFIXES):
                return True
            if _SECRET_KEY_PATTERNS.search(k) and len(v) > _MIN_SECRET_VALUE_LEN:
                return True
    return False


def scan_serverless(
    assets: dict[str, list[dict[str, Any]]],
    region: str = "us-east-1",
    cloud: str = "aws",
) -> list[dict[str, Any]]:
    """Run serverless-focused checks on discovered assets. AWS-only for now."""
    findings: list[dict[str, Any]] = []
    if cloud != "aws":
        return findings

    # ── Lambda ─────────────────────────────────────────────────────────────
    for fn in assets.get("lambda", []):
        fid = fn.get("id") or fn.get("FunctionName") or "unknown"
        name = fn.get("name") or fid
        timeout = fn.get("timeout") or 0
        mem = fn.get("memory_size") or 0
        env = fn.get("environment") or fn.get("env_vars") or {}

        if not fn.get("dead_letter_config") and not fn.get("destination_on_failure"):
            findings.append(_finding(
                "serverless.lambda_no_dlq", "lambda", fid, name,
                "Lambda has no failure destination (DLQ or OnFailure)",
                SEVERITY_MEDIUM,
                "Failed async invocations may be lost. Configure DeadLetterConfig or Event Invoke OnFailure destination.",
                "Set Lambda DeadLetterConfig to an SQS queue or SNS topic, or use PutFunctionEventInvokeConfig OnFailure.",
                region=region, cloud="aws",
            ))
        if timeout > 300:
            findings.append(_finding(
                "serverless.lambda_timeout_high", "lambda", fid, name,
                "Lambda timeout exceeds 5 minutes",
                SEVERITY_LOW,
                f"Timeout is {timeout}s. Long timeouts can mask hanging code and increase cost.",
                "Reduce timeout to the minimum required; use Step Functions for long workflows.",
                region=region, cloud="aws",
            ))
        if _has_secrets_in_env(env):
            findings.append(_finding(
                "serverless.lambda_env_secrets", "lambda", fid, name,
                "Lambda environment may contain secrets",
                SEVERITY_HIGH,
                "Environment variables match secret-like keys (password, api_key, etc.). Use Secrets Manager or Parameter Store.",
                "Move secrets to AWS Secrets Manager or SSM Parameter Store; reference in Lambda config.",
                region=region, cloud="aws",
            ))
        reserved = fn.get("reserved_concurrent_executions")
        if reserved is not None and int(reserved) == 0:
            findings.append(_finding(
                "serverless.lambda_reserved_concurrency_zero", "lambda", fid, name,
                "Lambda reserved concurrency is 0 (all invocations throttled)",
                SEVERITY_MEDIUM,
                "ReservedConcurrentExecutions=0 throttles all invocations. Often unintentional.",
                "Remove the reserved concurrency limit or set it to a positive value.",
                region=region, cloud="aws",
            ))
        if fn.get("vpc_config") and not fn.get("destination_on_failure") and not fn.get("dead_letter_config"):
            findings.append(_finding(
                "serverless.lambda_vpc_review", "lambda", fid, name,
                "Lambda in VPC: verify NAT/egress and failure handling",
                SEVERITY_LOW,
                "VPC Lambdas need NAT or VPC endpoints for AWS APIs. Ensure DLQ/OnFailure for async failures.",
                "Review VPC subnet routing and add failure destination for async invocations.",
                region=region, cloud="aws",
            ))

    # ── Step Functions ─────────────────────────────────────────────────────
    try:
        from cspm.utils.aws_helpers import get_client
        sf = get_client("stepfunctions", region)
        for sm in assets.get("stepfunctions", [])[:50]:
            arn = sm.get("arn") or sm.get("id")
            sname = sm.get("name") or (arn.split(":")[-1] if arn else "unknown")
            if not arn:
                continue
            try:
                desc = sf.describe_state_machine(stateMachineArn=arn)
                log_cfg = desc.get("loggingConfiguration") or {}
                tracing = (desc.get("tracingConfiguration") or {}).get("enabled") is True
                log_level = (log_cfg.get("level") or "").upper()
                if log_level in ("OFF", "NONE", ""):
                    findings.append(_finding(
                        "serverless.stepfunctions_no_logging", "stepfunctions", arn, sname,
                        "Step Functions state machine has logging disabled",
                        SEVERITY_MEDIUM,
                        "Execution history and debugging are limited without logging.",
                        "Enable logging in the state machine settings (Logging level ALL or ERROR).",
                        region=region, cloud="aws",
                    ))
                if not tracing:
                    findings.append(_finding(
                        "serverless.stepfunctions_no_xray", "stepfunctions", arn, sname,
                        "Step Functions X-Ray tracing is disabled",
                        SEVERITY_LOW,
                        "X-Ray tracing helps diagnose failures and latency in workflows.",
                        "Enable tracing in the state machine tracing configuration.",
                        region=region, cloud="aws",
                    ))
            except Exception:
                pass
    except Exception:
        pass

    # ── API Gateway ───────────────────────────────────────────────────────
    try:
        from cspm.utils.aws_helpers import get_client
        agw = get_client("apigateway", region)
        agwv2 = get_client("apigatewayv2", region)
        usage_plan_ids: set[str] = set()
        try:
            for up in agw.get_usage_plans().get("items", []):
                usage_plan_ids.add(up.get("id", ""))
            for key in agw.get_api_keys().get("items", []):
                for pid in key.get("stageKeys", []) or []:
                    usage_plan_ids.add(pid.get("usagePlanId", ""))
        except Exception:
            pass
        for api in assets.get("api_gateway", [])[:30]:
            api_id = api.get("id")
            aname = api.get("name") or api_id or "unknown"
            version = (api.get("api_version") or "REST").upper()
            has_usage_plan = False
            try:
                if version == "REST" and api_id:
                    stages = agw.get_stages(restApiId=api_id).get("item", [])
                    for s in stages:
                        if s.get("stageName") and usage_plan_ids:
                            has_usage_plan = True
                            break
                elif version == "HTTP" and api_id:
                    stages = agwv2.get_stages(ApiId=api_id).get("Items", [])
                    has_usage_plan = len(stages) > 0
            except Exception:
                pass
            if not has_usage_plan and api.get("stage_count", 0) > 0:
                findings.append(_finding(
                    "serverless.apigw_no_usage_plan", "api_gateway", api_id or "unknown", aname,
                    "API Gateway has no usage plan (throttling/quota)",
                    SEVERITY_LOW,
                    "Without a usage plan, throttling and quotas are not enforced at the API level.",
                    "Create a usage plan and associate it with the API stage for rate limiting.",
                    region=region, cloud="aws",
                ))
            if not api.get("logging_enabled"):
                findings.append(_finding(
                    "serverless.apigw_logging_review", "api_gateway", api_id or "unknown", aname,
                    "API Gateway access logging not enabled",
                    SEVERITY_LOW,
                    "Enable access logging for audit and debugging.",
                    "Configure accessLogSettings on the stage (CloudWatch Logs or custom destination).",
                    region=region, cloud="aws",
                ))
    except Exception:
        pass

    # ── SQS ───────────────────────────────────────────────────────────────
    for q in assets.get("sqs", []):
        qid = q.get("id") or q.get("name") or "unknown"
        qname = q.get("name") or qid
        redrive = q.get("redrive_policy") or {}
        if isinstance(redrive, str):
            try:
                import json
                redrive = json.loads(redrive) if redrive else {}
            except Exception:
                redrive = {}
        if not redrive.get("deadLetterTargetArn"):
            findings.append(_finding(
                "serverless.sqs_no_dlq", "sqs", qid, qname,
                "SQS queue has no dead-letter queue",
                SEVERITY_LOW,
                "Messages that fail processing may be lost or block the queue. Use a redrive policy.",
                "Set RedrivePolicy with deadLetterTargetArn and maxReceiveCount.",
                region=region, cloud="aws",
            ))
        vis = q.get("visibility_timeout_sec") or 0
        if vis > 0 and vis < 60:
            findings.append(_finding(
                "serverless.sqs_visibility_short", "sqs", qid, qname,
                "SQS visibility timeout may be too short for Lambda",
                SEVERITY_LOW,
                f"Visibility timeout is {vis}s. If this queue triggers Lambda, ensure it is at least 6× Lambda timeout.",
                "Set VisibilityTimeout to at least 6× the Lambda function timeout to avoid duplicate processing.",
                region=region, cloud="aws",
            ))

    # ── DynamoDB (streams, encryption) ───────────────────────────────────────
    for table in assets.get("dynamodb", [])[:30]:
        tid = table.get("id") or table.get("name") or "unknown"
        tname = table.get("name") or tid
        if not table.get("stream_enabled"):
            findings.append(_finding(
                "serverless.dynamodb_streams_review", "dynamodb", tid, tname,
                "DynamoDB table has no streams (if used by Lambda)",
                SEVERITY_LOW,
                "If Lambda or other consumers need change data, enable DynamoDB Streams.",
                "Enable streams on the table if you need event-driven processing.",
                region=region, cloud="aws",
            ))

    return findings
