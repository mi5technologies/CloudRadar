"""EC2 instance discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        ec2 = get_client("ec2", region)
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for res in page.get("Reservations", []):
                for inst in res.get("Instances", []):
                    assets.append({
                        "id": inst.get("InstanceId"),
                        "type": "ec2",
                        "region": region,
                        "state": inst.get("State", {}).get("Name"),
                        "instance_type": inst.get("InstanceType"),
                        "image_id": inst.get("ImageId"),
                        "tags": {t["Key"]: t["Value"] for t in inst.get("Tags", [])},
                        "public_ip": inst.get("PublicIpAddress"),
                        "security_groups": [sg["GroupId"] for sg in inst.get("SecurityGroups", [])],
                    })
    except Exception:
        pass
    return assets
