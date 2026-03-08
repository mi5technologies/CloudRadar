"""Network: security groups and ALBs discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> dict[str, list[dict[str, Any]]]:
    security_groups: list[dict] = []
    albs: list[dict] = []
    try:
        ec2 = get_client("ec2", region)
        paginator = ec2.get_paginator("describe_security_groups")
        for page in paginator.paginate():
            for sg in page.get("SecurityGroups", []):
                rules_in = []
                for perm in sg.get("IpPermissions", []):
                    from_port = perm.get("FromPort")
                    to_port = perm.get("ToPort")
                    for ip in perm.get("IpRanges", []) + perm.get("Ipv6Ranges", []):
                        cidr = ip.get("CidrIp") or ip.get("CidrIpv6")
                        rules_in.append({"from_port": from_port, "to_port": to_port, "cidr": cidr})
                security_groups.append({
                    "id": sg.get("GroupId"),
                    "name": sg.get("GroupName"),
                    "type": "security_group",
                    "region": region,
                    "vpc_id": sg.get("VpcId"),
                    "ip_permissions": rules_in,
                })
        elbv2 = get_client("elbv2", region)
        paginator = elbv2.get_paginator("describe_load_balancers")
        for page in paginator.paginate():
            for lb in page.get("LoadBalancers", []):
                scheme = lb.get("Scheme", "")
                albs.append({
                    "id": lb.get("LoadBalancerArn"),
                    "name": lb.get("LoadBalancerName"),
                    "type": "alb",
                    "region": region,
                    "scheme": scheme,
                    "public": scheme == "internet-facing",
                })
    except Exception:
        pass
    return {"security_groups": security_groups, "albs": albs}
