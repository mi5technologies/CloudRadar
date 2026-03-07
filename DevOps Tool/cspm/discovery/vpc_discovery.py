"""VPC and EBS volume discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> dict[str, list[dict[str, Any]]]:
    vpcs: list[dict] = []
    ebs_volumes: list[dict] = []
    try:
        ec2 = get_client("ec2", region)

        paginator = ec2.get_paginator("describe_vpcs")
        for page in paginator.paginate():
            for vpc in page.get("Vpcs", []):
                vpc_id = vpc.get("VpcId")
                flow_logs_enabled = _has_flow_logs(ec2, vpc_id)
                vpcs.append({
                    "id": vpc_id,
                    "type": "vpc",
                    "region": region,
                    "is_default": vpc.get("IsDefault", False),
                    "cidr_block": vpc.get("CidrBlock"),
                    "state": vpc.get("State"),
                    "flow_logs_enabled": flow_logs_enabled,
                    "tags": {t["Key"]: t["Value"] for t in vpc.get("Tags", [])},
                })

        paginator = ec2.get_paginator("describe_volumes")
        for page in paginator.paginate():
            for vol in page.get("Volumes", []):
                ebs_volumes.append({
                    "id": vol.get("VolumeId"),
                    "type": "ebs",
                    "region": region,
                    "encrypted": vol.get("Encrypted", False),
                    "state": vol.get("State"),
                    "size": vol.get("Size"),
                    "volume_type": vol.get("VolumeType"),
                    "kms_key_id": vol.get("KmsKeyId"),
                    "attachments": [a.get("InstanceId") for a in vol.get("Attachments", [])],
                    "tags": {t["Key"]: t["Value"] for t in vol.get("Tags", [])},
                })
    except Exception:
        pass
    return {"vpc": vpcs, "ebs": ebs_volumes}


def _has_flow_logs(ec2_client, vpc_id: str) -> bool:
    try:
        resp = ec2_client.describe_flow_logs(
            Filters=[{"Name": "resource-id", "Values": [vpc_id]}]
        )
        return len(resp.get("FlowLogs", [])) > 0
    except Exception:
        return False
