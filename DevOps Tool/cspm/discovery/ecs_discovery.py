"""ECS cluster and task definition discovery."""
from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> dict[str, list[dict[str, Any]]]:
    clusters: list[dict] = []
    task_defs: list[dict] = []
    try:
        ecs = get_client("ecs", region)

        paginator = ecs.get_paginator("list_clusters")
        cluster_arns: list[str] = []
        for page in paginator.paginate():
            cluster_arns.extend(page.get("clusterArns", []))

        if cluster_arns:
            for i in range(0, len(cluster_arns), 100):
                batch = cluster_arns[i: i + 100]
                resp = ecs.describe_clusters(clusters=batch, include=["SETTINGS"])
                for c in resp.get("clusters", []):
                    container_insights = any(
                        s.get("name") == "containerInsights" and s.get("value") == "enabled"
                        for s in c.get("settings", [])
                    )
                    clusters.append({
                        "id": c.get("clusterArn"),
                        "name": c.get("clusterName"),
                        "type": "ecs_cluster",
                        "region": region,
                        "status": c.get("status"),
                        "container_insights_enabled": container_insights,
                        "tags": {t["key"]: t["value"] for t in c.get("tags", [])},
                    })

        paginator = ecs.get_paginator("list_task_definition_families")
        for page in paginator.paginate(status="ACTIVE"):
            for family in page.get("families", []):
                try:
                    td_resp = ecs.describe_task_definition(taskDefinition=family)
                    td = td_resp.get("taskDefinition", {})
                    containers = td.get("containerDefinitions", [])
                    privileged = any(c.get("privileged") for c in containers)
                    has_logging = all(
                        c.get("logConfiguration") is not None for c in containers
                    ) if containers else False
                    root_user = any(
                        c.get("user") in (None, "root", "0") for c in containers
                    )
                    task_defs.append({
                        "id": td.get("taskDefinitionArn"),
                        "name": family,
                        "type": "ecs_task_def",
                        "region": region,
                        "network_mode": td.get("networkMode"),
                        "privileged_containers": privileged,
                        "logging_enabled": has_logging,
                        "root_user": root_user,
                        "requires_compatibilities": td.get("requiresCompatibilities", []),
                    })
                except Exception:
                    pass
    except Exception:
        pass
    return {"ecs_cluster": clusters, "ecs_task_def": task_defs}
