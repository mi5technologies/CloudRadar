"""IAM users and roles discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> dict[str, list[dict[str, Any]]]:
    users: list[dict] = []
    roles: list[dict] = []
    try:
        iam = get_client("iam", region)
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            for u in page.get("Users", []):
                users.append({
                    "id": u.get("UserName"),
                    "arn": u.get("Arn"),
                    "type": "iam_user",
                    "region": region,
                    "create_date": u.get("CreateDate").isoformat() if u.get("CreateDate") else None,
                })
        paginator = iam.get_paginator("list_roles")
        for page in paginator.paginate():
            for r in page.get("Roles", []):
                roles.append({
                    "id": r.get("RoleName"),
                    "arn": r.get("Arn"),
                    "type": "iam_role",
                    "region": region,
                })
    except Exception:
        pass
    return {"users": users, "roles": roles}
