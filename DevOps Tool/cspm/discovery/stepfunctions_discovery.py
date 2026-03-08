"""Step Functions state machine discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        sf = get_client("stepfunctions", region)
        paginator = sf.get_paginator("list_state_machines")
        for page in paginator.paginate():
            for sm in page.get("stateMachines", []):
                arn = sm.get("stateMachineArn", "")
                name = sm.get("name", "")
                assets.append({
                    "id": arn.split(":")[-1] if arn else name,
                    "arn": arn,
                    "name": name,
                    "type": "stepfunctions",
                    "region": region,
                    "status": sm.get("status"),
                    "creation_date": str(sm.get("creationDate", "")),
                })
    except Exception:
        pass
    return assets
