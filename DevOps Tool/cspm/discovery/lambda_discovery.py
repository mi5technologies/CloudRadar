"""Lambda function discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client

_MAX_FUNCTIONS_FOR_CONFIG = 100  # Limit extra API calls for DLQ/destination config


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        lam = get_client("lambda", region)
        paginator = lam.get_paginator("list_functions")
        for page in paginator.paginate():
            for fn in page.get("Functions", []):
                assets.append({
                    "id": fn.get("FunctionName"),
                    "type": "lambda",
                    "region": region,
                    "runtime": fn.get("Runtime"),
                    "timeout": fn.get("Timeout"),
                    "memory_size": fn.get("MemorySize"),
                    "environment": fn.get("Environment", {}).get("Variables") or {},
                    "tags": fn.get("Tags") or {},
                })

        # Enrich with DLQ and async destination config (limited to avoid many API calls)
        for i, a in enumerate(assets):
            if i >= _MAX_FUNCTIONS_FOR_CONFIG:
                break
            _enrich_lambda_config(lam, a)
    except Exception:
        pass

    return assets


def _enrich_lambda_config(lam, asset: dict[str, Any]) -> None:
    """Fetch DeadLetterConfig, OnFailure destination, concurrency, and VPC for a Lambda."""
    fn_name = asset.get("id") or asset.get("FunctionName")
    if not fn_name:
        return
    try:
        resp = lam.get_function(FunctionName=fn_name)
        cfg = resp.get("Configuration") or {}
        dlq = cfg.get("DeadLetterConfig") or {}
        asset["dead_letter_config"] = dlq.get("TargetArn") if dlq else None
        asset["reserved_concurrent_executions"] = cfg.get("ReservedConcurrentExecutions")
        vpc = cfg.get("VpcConfig") or {}
        asset["vpc_config"] = vpc if vpc.get("VpcId") else None
        asset["layers"] = [lay.get("Arn") for lay in (cfg.get("Layers") or []) if lay.get("Arn")]
    except Exception:
        asset["dead_letter_config"] = None
        asset["reserved_concurrent_executions"] = None
        asset["vpc_config"] = None
        asset["layers"] = []

    try:
        resp = lam.get_function_event_invoke_config(FunctionName=fn_name, Qualifier="$LATEST")
        dest = (resp.get("DestinationConfig") or {}).get("OnFailure") or {}
        asset["destination_on_failure"] = dest.get("Destination") if dest else None
    except Exception:
        asset["destination_on_failure"] = None
