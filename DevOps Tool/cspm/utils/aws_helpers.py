"""AWS-specific helpers."""
import boto3
from typing import Any, Optional


def get_client(service: str, region: Optional[str] = None) -> Any:
    return boto3.client(service, region_name=region)


def get_caller_identity(region: Optional[str] = None) -> dict:
    sts = get_client("sts", region)
    return sts.get_caller_identity()
