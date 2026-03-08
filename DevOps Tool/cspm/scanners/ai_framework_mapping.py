"""OWASP LLM Top 10 and NIST AI RMF mappings for AI security findings."""
from __future__ import annotations

# Rule ID -> (OWASP LLM category, NIST AI RMF control)
AI_FRAMEWORK_MAPPING: dict[str, tuple[str, str]] = {
    "ai.bedrock.no_guardrails": ("LLM01: Prompt Injection", "GOVERN 1.1, 3.1; MAP 1.1; MANAGE 2.1"),
    "ai.bedrock.guardrail_not_ready": ("LLM01: Prompt Injection", "MANAGE 2.1"),
    "ai.bedrock.guardrail_no_prompt_attack": ("LLM01: Prompt Injection", "GOVERN 3.1; MAP 1.1; MANAGE 2.1"),
    "ai.bedrock.guardrail_no_pii": ("LLM02: Insecure Output; LLM07: Insufficient Access Control", "MAP 1.2; MANAGE 2.2"),
    "ai.bedrock.inference_logging": ("LLM09: Overreliance on LLMs", "GOVERN 2.2; MAP 4.1; MANAGE 3.2"),
    "ai.bedrock.knowledge_base_s3_iam": ("LLM07: Insufficient Access Control", "MAP 2.1; MANAGE 2.2"),
    "ai.lambda_bedrock_review": ("LLM07: Insufficient Access Control; LLM09", "MANAGE 2.1, 3.2"),
    "ai.sagemaker_notebook_public": ("LLM07: Insufficient Access Control", "MAP 2.1; MANAGE 2.2"),
    "ai.sagemaker_endpoint_encryption": ("LLM07: Insufficient Access Control", "MANAGE 2.2"),
    "ai.sagemaker_notebook_encryption": ("LLM07: Insufficient Access Control", "MANAGE 2.2"),
    "ai.vertex.safety_review": ("LLM01: Prompt Injection", "GOVERN 3.1; MANAGE 2.1"),
    "ai.vertex.safety_in_code": ("LLM01: Prompt Injection", "GOVERN 3.1; MANAGE 2.1"),
    "ai.vertex.logging_review": ("LLM09: Overreliance on LLMs", "GOVERN 2.2; MAP 4.1; MANAGE 3.2"),
    "ai.vertex.iam_review": ("LLM07: Insufficient Access Control", "MAP 2.1; MANAGE 2.2"),
    "ai.vertex.network_review": ("LLM07: Insufficient Access Control", "MAP 2.1; MANAGE 2.2"),
    "ai.gcp.unavailable": ("N/A", "N/A"),
    "ai.gcp.sdk_missing": ("N/A", "N/A"),
    "ai.azure.content_filter_review": ("LLM01: Prompt Injection", "GOVERN 3.1; MANAGE 2.1"),
    "ai.azure.public_network": ("LLM07: Insufficient Access Control", "MAP 2.1; MANAGE 2.2"),
    "ai.azure.encryption_review": ("LLM07: Insufficient Access Control", "MANAGE 2.2"),
    "ai.azure.diagnostics_review": ("LLM09: Overreliance on LLMs", "GOVERN 2.2; MAP 4.1; MANAGE 3.2"),
    "ai.azure.managed_identity_review": ("LLM07: Insufficient Access Control", "MANAGE 2.2"),
    "ai.azure.unavailable": ("N/A", "N/A"),
    "ai.azure.sdk_missing": ("N/A", "N/A"),
}


def get_framework_mapping(rule_id: str) -> dict[str, str]:
    owasp, nist = AI_FRAMEWORK_MAPPING.get(rule_id, ("N/A", "N/A"))
    return {"owasp_llm": owasp, "nist_ai_rmf": nist}
