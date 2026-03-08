"""EKS cluster discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> list[dict[str, Any]]:
    assets = []
    try:
        eks = get_client("eks", region)
        paginator = eks.get_paginator("list_clusters")
        for page in paginator.paginate():
            for cluster_name in page.get("clusters", []):
                try:
                    resp = eks.describe_cluster(name=cluster_name)
                    cluster = resp.get("cluster", {})
                    resources_vpc = cluster.get("resourcesVpcConfig", {})
                    logging_config = cluster.get("logging", {}).get("clusterLogging", [])
                    api_server_public = resources_vpc.get("endpointPublicAccess", True)
                    api_server_private = resources_vpc.get("endpointPrivateAccess", False)
                    public_access_cidrs = resources_vpc.get("publicAccessCidrs", [])
                    log_types_enabled = [
                        lt
                        for entry in logging_config
                        for lt in entry.get("types", [])
                        if entry.get("enabled")
                    ]
                    assets.append({
                        "id": cluster.get("arn") or cluster_name,
                        "name": cluster_name,
                        "type": "eks",
                        "region": region,
                        "version": cluster.get("version"),
                        "status": cluster.get("status"),
                        "endpoint_public_access": api_server_public,
                        "endpoint_private_access": api_server_private,
                        "public_access_cidrs": public_access_cidrs,
                        "public_access_open": api_server_public and ("0.0.0.0/0" in public_access_cidrs or not public_access_cidrs),
                        "logging_enabled": len(log_types_enabled) > 0,
                        "log_types": log_types_enabled,
                        "secrets_encryption": bool(cluster.get("encryptionConfig")),
                        "tags": cluster.get("tags", {}),
                    })
                except Exception:
                    pass
    except Exception:
        pass
    return assets
