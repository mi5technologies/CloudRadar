"""AWS SageMaker discovery: notebook instances, endpoints, training jobs."""
from __future__ import annotations

from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> dict[str, Any]:
    """Discover SageMaker notebook instances, endpoints, and training jobs.

    Returns dict with keys: notebook_instances, endpoints, endpoint_configs,
    training_jobs (summary list).
    """
    out: dict[str, Any] = {
        "notebook_instances": [],
        "endpoints": [],
        "endpoint_configs": [],
        "training_jobs": [],
    }
    try:
        sm = get_client("sagemaker", region)
    except Exception:
        return out

    # Notebook instances
    try:
        paginator = sm.get_paginator("list_notebook_instances")
        for page in paginator.paginate():
            for ni in page.get("NotebookInstances", []):
                out["notebook_instances"].append({
                    "id": ni.get("NotebookInstanceArn"),
                    "name": ni.get("NotebookInstanceName"),
                    "type": "sagemaker_notebook",
                    "region": region,
                    "status": ni.get("NotebookInstanceStatus"),
                    "instance_type": ni.get("InstanceType"),
                    "direct_internet_access": ni.get("DirectInternetAccess", "Disabled") == "Enabled",
                    "subnet_id": ni.get("SubnetId"),
                    "kms_key_id": ni.get("KmsKeyId"),
                    "root_access": ni.get("RootAccess", "Enabled"),
                })
    except Exception:
        pass

    # Endpoints
    try:
        paginator = sm.get_paginator("list_endpoints")
        for page in paginator.paginate():
            for ep in page.get("Endpoints", []):
                out["endpoints"].append({
                    "id": ep.get("EndpointArn"),
                    "name": ep.get("EndpointName"),
                    "type": "sagemaker_endpoint",
                    "region": region,
                    "status": ep.get("EndpointStatus"),
                    "endpoint_config_name": ep.get("EndpointConfigName"),
                    "creation_time": ep.get("CreationTime"),
                })
    except Exception:
        pass

    # Endpoint configs
    try:
        paginator = sm.get_paginator("list_endpoint_configs")
        for page in paginator.paginate(MaxResults=50):
            for ec in page.get("EndpointConfigs", []):
                out["endpoint_configs"].append({
                    "name": ec.get("EndpointConfigName"),
                    "arn": ec.get("EndpointConfigArn"),
                    "kms_key_id": ec.get("KmsKeyId"),
                })
    except Exception:
        pass

    # Training jobs (recent)
    try:
        paginator = sm.get_paginator("list_training_jobs")
        for page in paginator.paginate(MaxResults=50):
            for tj in page.get("TrainingJobSummaries", []):
                out["training_jobs"].append({
                    "id": tj.get("TrainingJobArn"),
                    "name": tj.get("TrainingJobName"),
                    "type": "sagemaker_training_job",
                    "region": region,
                    "status": tj.get("TrainingJobStatus"),
                    "creation_time": tj.get("CreationTime"),
                })
    except Exception:
        pass

    return out
