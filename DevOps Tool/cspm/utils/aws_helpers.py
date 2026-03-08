"""AWS-specific helpers."""
import boto3
from contextvars import ContextVar
from typing import Any, Optional

# Context-local credentials for multi-account assume-role (per-thread safe)
_assumed_credentials: ContextVar[Optional[dict]] = ContextVar("assumed_credentials", default=None)


def get_client(service: str, region: Optional[str] = None) -> Any:
    """Return boto3 client. Uses assumed-role credentials if set (multi-account)."""
    creds = _assumed_credentials.get()
    if creds:
        return boto3.client(
            service,
            region_name=region,
            aws_access_key_id=creds.get("AccessKeyId"),
            aws_secret_access_key=creds.get("SecretAccessKey"),
            aws_session_token=creds.get("SessionToken"),
        )
    return boto3.client(service, region_name=region)


def get_caller_identity(region: Optional[str] = None) -> dict:
    sts = get_client("sts", region)
    return sts.get_caller_identity()


def assume_role(role_arn: str, session_name: str = "CloudRadarScan") -> Optional[dict]:
    """Assume role and return temporary credentials. Returns None on failure."""
    try:
        sts = boto3.client("sts")
        resp = sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
        creds = resp.get("Credentials")
        if creds:
            return {
                "AccessKeyId": creds["AccessKeyId"],
                "SecretAccessKey": creds["SecretAccessKey"],
                "SessionToken": creds["SessionToken"],
            }
    except Exception:
        pass
    return None


def set_assumed_credentials(creds: Optional[dict]) -> None:
    """Set credentials for get_client (multi-account). Clear with None."""
    _assumed_credentials.set(creds)


def list_organization_accounts() -> list[dict]:
    """List all accounts in AWS Organizations. Requires management account access."""
    try:
        org = boto3.client("organizations")
        accounts = []
        paginator = org.get_paginator("list_accounts")
        for page in paginator.paginate():
            for acct in page.get("Accounts", []):
                if acct.get("Status") == "ACTIVE":
                    accounts.append({
                        "id": acct["Id"],
                        "name": acct.get("Name", ""),
                    })
        return accounts
    except Exception:
        return []
