"""AWS Bedrock discovery: guardrails, foundation models, knowledge bases."""
from __future__ import annotations

from typing import Any

from cspm.utils.aws_helpers import get_client


def discover(region: str) -> dict[str, Any]:
    """Discover Bedrock guardrails, foundation models, and knowledge bases in the region.

    Returns dict with keys: guardrails, guardrail_details, foundation_models,
    knowledge_bases, knowledge_base_details, provisioned_throughput.
    """
    out: dict[str, Any] = {
        "guardrails": [],
        "guardrail_details": [],
        "foundation_models": [],
        "knowledge_bases": [],
        "knowledge_base_details": [],
        "provisioned_throughput": [],
    }
    try:
        bedrock = get_client("bedrock", region)
    except Exception:
        return out

    # Guardrails
    try:
        paginator = bedrock.get_paginator("list_guardrails")
        for page in paginator.paginate():
            out["guardrails"].extend(page.get("guardrailSummaries", []))
    except Exception:
        pass

    # Guardrail details (content policy, prompt attack, PII) - limit to avoid many API calls
    for g in out["guardrails"][:20]:
        gid = g.get("id") or g.get("guardrailArn")
        if not gid:
            continue
        try:
            detail = bedrock.get_guardrail(guardrailIdentifier=gid)
            out["guardrail_details"].append({
                "id": gid,
                "name": detail.get("name"),
                "status": detail.get("status"),
                "contentPolicy": detail.get("contentPolicy") or {},
                "sensitiveInformationPolicy": detail.get("sensitiveInformationPolicy") or {},
                "wordPolicy": detail.get("wordPolicy"),
                "topicPolicy": detail.get("topicPolicy"),
            })
        except Exception:
            pass

    # Foundation models
    try:
        resp = bedrock.list_foundation_models(byInferenceType="ON_DEMAND")
        out["foundation_models"] = resp.get("modelSummaries", [])
    except Exception:
        pass
    try:
        resp = bedrock.list_foundation_models(byInferenceType="PROVISIONED")
        out["foundation_models"].extend(resp.get("modelSummaries", []))
    except Exception:
        pass

    # Provisioned model throughput (usage/cost)
    try:
        paginator = bedrock.get_paginator("list_provisioned_model_throughputs")
        for page in paginator.paginate():
            out["provisioned_throughput"].extend(page.get("provisionedModelSummaries", []))
    except Exception:
        pass

    # Knowledge bases (bedrock-agent client)
    try:
        agent = get_client("bedrock-agent", region)
        paginator = agent.get_paginator("list_knowledge_bases")
        for page in paginator.paginate():
            out["knowledge_bases"].extend(page.get("knowledgeBaseSummaries", []))
    except Exception:
        pass

    for kb in out["knowledge_bases"][:15]:
        kbid = kb.get("knowledgeBaseId")
        if not kbid:
            continue
        try:
            agent = get_client("bedrock-agent", region)
            detail = agent.get_knowledge_base(knowledgeBaseId=kbid)
            config = detail.get("knowledgeBaseConfiguration", {}) or {}
            data_sources = []
            try:
                ds_paginator = agent.get_paginator("list_data_sources")
                for ds_page in ds_paginator.paginate(knowledgeBaseId=kbid):
                    data_sources.extend(ds_page.get("knowledgeBaseDataSourceSummaries", []))
            except Exception:
                pass
            out["knowledge_base_details"].append({
                "knowledgeBaseId": kbid,
                "name": detail.get("name"),
                "roleArn": detail.get("roleArn"),
                "knowledgeBaseConfiguration": config,
                "dataSourceSummaries": data_sources,
            })
        except Exception:
            pass

    return out
