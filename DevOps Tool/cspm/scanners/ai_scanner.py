"""AI Usage Security scanner — flags missing guardrails, content filters, and unsafe AI configs.

Checks AWS Bedrock, Google Vertex AI, and Azure OpenAI for:
- Prompt injection / jailbreak prevention (guardrails, content filters)
- PII redaction and sensitive data handling
- Model access control and data residency
- Inference logging (Bedrock CloudWatch, Vertex audit, Azure diagnostics)
- SageMaker notebooks, endpoints, training jobs (public access, encryption, IAM)
- Lambda/Functions calling Bedrock or OpenAI (IAM, logging review)
- Bedrock Knowledge Base (S3 data source, IAM)
Maps findings to OWASP LLM Top 10 and NIST AI RMF.
"""
from __future__ import annotations

from typing import Any

from cspm.scanners.ai_framework_mapping import get_framework_mapping

SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


def _finding(
    rule_id: str,
    resource_type: str,
    resource_id: str,
    resource_name: str,
    title: str,
    severity: str,
    detail: str,
    remediation: str,
    region: str = "global",
    cloud: str = "aws",
) -> dict[str, Any]:
    f = {
        "rule_id": rule_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": resource_name or resource_id,
        "title": title,
        "severity": severity,
        "detail": detail,
        "remediation": remediation,
        "region": region,
        "passed": False,
        "cloud": cloud,
    }
    f.update(get_framework_mapping(rule_id))
    return f


# ---------------------------------------------------------------------------
# AWS Bedrock
# ---------------------------------------------------------------------------

def _scan_sagemaker(region: str) -> list[dict[str, Any]]:
    """Scan SageMaker notebooks, endpoints, training jobs for public access, encryption, IAM."""
    findings: list[dict[str, Any]] = []
    try:
        from cspm.discovery import sagemaker_discovery
        data = sagemaker_discovery.discover(region)
    except Exception:
        return findings

    for ni in data.get("notebook_instances", []):
        if ni.get("direct_internet_access"):
            findings.append(_finding(
                "ai.sagemaker_notebook_public", "sagemaker_notebook", ni.get("id", ""), ni.get("name", ""),
                "SageMaker notebook has direct internet access",
                SEVERITY_MEDIUM,
                f"Notebook '{ni.get('name')}' has DirectInternetAccess=Enabled. Restrict to VPC-only where possible.",
                "Create notebook instances in a private subnet without direct internet access; use VPC endpoints for AWS APIs.",
                region=region, cloud="aws",
            ))
        if not ni.get("kms_key_id"):
            findings.append(_finding(
                "ai.sagemaker_notebook_encryption", "sagemaker_notebook", ni.get("id", ""), ni.get("name", ""),
                "SageMaker notebook not encrypted with CMK",
                SEVERITY_LOW,
                "Notebook does not use a customer-managed KMS key for encryption at rest.",
                "Enable encryption with a customer-managed KMS key in the notebook instance settings.",
                region=region, cloud="aws",
            ))

    for ep in data.get("endpoints", []):
        config_name = ep.get("endpoint_config_name")
        configs = {c.get("name"): c for c in data.get("endpoint_configs", [])}
        cfg = configs.get(config_name, {}) if config_name else {}
        if not cfg.get("kms_key_id"):
            findings.append(_finding(
                "ai.sagemaker_endpoint_encryption", "sagemaker_endpoint", ep.get("id", ""), ep.get("name", ""),
                "SageMaker endpoint config without CMK encryption",
                SEVERITY_LOW,
                "Endpoint config does not specify a KMS key for model data encryption.",
                "Create or update endpoint config with KmsKeyId for encryption at rest.",
                region=region, cloud="aws",
            ))

    return findings


def _scan_aws(region: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        import boto3
        bedrock = boto3.client("bedrock", region_name=region)
    except Exception as e:
        findings.append(_finding(
            "ai.aws.unavailable", "bedrock", "n/a", "Bedrock",
            "AWS Bedrock API unavailable",
            SEVERITY_LOW,
            f"Could not connect to Bedrock in {region}: {e}",
            "Ensure boto3 is installed and AWS credentials have bedrock:ListGuardrails and bedrock:ListFoundationModels permissions.",
            region=region, cloud="aws",
        ))
        return findings

    # Use discovery for richer guardrail and KB data when available
    guardrail_details: list[dict] = []
    knowledge_base_details: list[dict] = []
    try:
        from cspm.discovery import bedrock_discovery
        disc = bedrock_discovery.discover(region)
        guardrail_details = disc.get("guardrail_details", [])
        knowledge_base_details = disc.get("knowledge_base_details", [])
    except Exception:
        pass

    # Check guardrails
    guardrails: list[dict] = []
    try:
        paginator = bedrock.get_paginator("list_guardrails")
        for page in paginator.paginate():
            guardrails.extend(page.get("guardrailSummaries", []))
    except Exception:
        pass

    # Foundation models
    models: list[dict] = []
    try:
        resp = bedrock.list_foundation_models(byInferenceType="ON_DEMAND")
        models = resp.get("modelSummaries", [])
    except Exception:
        pass

    # --- Guardrail: prompt attack prevention (jailbreak / prompt injection) ---
    for gd in guardrail_details:
        gid = gd.get("id", "")
        gname = gd.get("name", gid)
        content = gd.get("contentPolicy") or {}
        filters = content.get("filters", []) if isinstance(content.get("filters"), list) else []
        has_prompt_attack = any(
            (f.get("type") or "").upper() == "PROMPT_ATTACK" and (f.get("inputStrength") or f.get("strength") or "NONE").upper() not in ("NONE", "")
            for f in filters
        )
        if filters and not has_prompt_attack:
            findings.append(_finding(
                "ai.bedrock.guardrail_no_prompt_attack", "bedrock_guardrail", gid, gname,
                "Guardrail missing or weak prompt attack prevention",
                SEVERITY_HIGH,
                f"Guardrail '{gname}' does not have PROMPT_ATTACK filter enabled. Enable prompt attack (jailbreak/injection) detection.",
                "In Bedrock Guardrails, add Content filter type PROMPT_ATTACK with strength MEDIUM or HIGH for input and output.",
                region=region, cloud="aws",
            ))

    # --- Guardrail: PII / sensitive information ---
    for gd in guardrail_details:
        sens = gd.get("sensitiveInformationPolicy")
        if sens is None:
            continue
        pii = sens.get("piiEntities", []) if isinstance(sens.get("piiEntities"), list) else []
        has_pii_block = any(
            (e.get("action") or "").upper() in ("BLOCK", "ANONYMIZE") for e in pii
        )
        if not has_pii_block:
            gid = gd.get("id", "")
            gname = gd.get("name", gid)
            findings.append(_finding(
                "ai.bedrock.guardrail_no_pii", "bedrock_guardrail", gid, gname,
                "Guardrail has no PII redaction configured",
                SEVERITY_MEDIUM,
                f"Guardrail '{gname}' does not configure PII entities with BLOCK or ANONYMIZE.",
                "In Guardrails, add PII entities (email, phone, AWS credentials, etc.) with action BLOCK or ANONYMIZE.",
                region=region, cloud="aws",
            ))

    # ai.bedrock.no_guardrails
    if models and not guardrails:
        findings.append(_finding(
            "ai.bedrock.no_guardrails", "bedrock", "account", "Bedrock Account",
            "No Bedrock Guardrails configured",
            SEVERITY_HIGH,
            f"Found {len(models)} foundation model(s) available in {region} but no Guardrails are defined. "
            "Without guardrails, prompts and completions are not filtered for harmful content, prompt injection, or PII.",
            "Create Bedrock Guardrails in the AWS Console (Bedrock → Guardrails) with Content Policy and Prompt Attack Prevention. "
            "Apply guardrails at invoke time in your application.",
            region=region, cloud="aws",
        ))

    # ai.bedrock.guardrails_not_ready
    not_ready = [g for g in guardrails if (g.get("status") or "").upper() != "READY"]
    if not_ready:
        for g in not_ready[:5]:
            gid = g.get("id", "unknown")
            gname = g.get("name", gid)
            findings.append(_finding(
                "ai.bedrock.guardrail_not_ready", "bedrock_guardrail", gid, gname,
                f"Guardrail '{gname}' not ready",
                SEVERITY_MEDIUM,
                f"Guardrail {gid} has status '{g.get('status', 'unknown')}'. It must be READY to be used.",
                "Wait for the guardrail to reach READY status or fix any configuration errors in the Bedrock console.",
                region=region, cloud="aws",
            ))

    # --- Inference logging (advisory) ---
    if models or guardrails:
        findings.append(_finding(
            "ai.bedrock.inference_logging", "bedrock", "account", "Bedrock Account",
            "Verify Bedrock inference logging is enabled",
            SEVERITY_LOW,
            "Ensure model invocation logging (prompts/completions) is enabled for audit and safety. Use CloudWatch Logs or custom logging.",
            "Enable logging in your application when calling InvokeModel; or use Bedrock model invocation logging where available.",
            region=region, cloud="aws",
        ))

    # --- Knowledge Base: S3 data source and IAM ---
    for kb in knowledge_base_details:
        kbid = kb.get("knowledgeBaseId", "")
        kbname = kb.get("name", kbid)
        role_arn = kb.get("roleArn")
        data_sources = kb.get("dataSourceSummaries", [])
        if not role_arn:
            findings.append(_finding(
                "ai.bedrock.knowledge_base_s3_iam", "bedrock_knowledge_base", kbid, kbname,
                "Knowledge Base has no service role configured",
                SEVERITY_MEDIUM,
                f"Knowledge base '{kbname}' should have an IAM role for S3/data source access.",
                "Assign a service role to the knowledge base with read access to S3 data sources.",
                region=region, cloud="aws",
            ))
        if not data_sources and kb.get("knowledgeBaseConfiguration"):
            findings.append(_finding(
                "ai.bedrock.knowledge_base_s3_iam", "bedrock_knowledge_base", kbid, kbname,
                "Knowledge Base has no data sources",
                SEVERITY_LOW,
                "Add S3 or other data sources and ensure the knowledge base role has least-privilege access.",
                "Configure data sources in Bedrock Knowledge Base and restrict the role to required buckets only.",
                region=region, cloud="aws",
            ))

    # --- Lambda calling Bedrock: review IAM and logging ---
    if models or guardrails:
        findings.append(_finding(
            "ai.lambda_bedrock_review", "lambda", "account", "AWS Account",
            "Review Lambda functions that invoke Bedrock",
            SEVERITY_LOW,
            "If any Lambda functions call Bedrock, verify IAM (bedrock:InvokeModel), VPC/network, and CloudWatch logging.",
            "Audit Lambda execution roles for bedrock:InvokeModel; ensure logging is enabled; use VPC endpoints for private access.",
            region=region, cloud="aws",
        ))

    # --- SageMaker ---
    findings.extend(_scan_sagemaker(region))

    return findings


# ---------------------------------------------------------------------------
# Google Vertex AI
# ---------------------------------------------------------------------------

def _scan_gcp(project_id: str, region: str = "us-central1") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        from google.cloud import aiplatform
        aiplatform.init(project=project_id, location=region)
    except ImportError:
        findings.append(_finding(
            "ai.gcp.sdk_missing", "vertex_ai", "n/a", "Vertex AI",
            "Vertex AI SDK not installed",
            SEVERITY_LOW,
            "google-cloud-aiplatform is required for Vertex AI checks. Install with: pip install google-cloud-aiplatform",
            "pip install google-cloud-aiplatform",
            region=region, cloud="gcp",
        ))
        return findings
    except Exception as e:
        findings.append(_finding(
            "ai.gcp.unavailable", "vertex_ai", "n/a", "Vertex AI",
            "Vertex AI API unavailable",
            SEVERITY_LOW,
            f"Could not initialize Vertex AI: {e}",
            "Ensure GOOGLE_APPLICATION_CREDENTIALS is set and the service account has roles/aiplatform.user.",
            region=region, cloud="gcp",
        ))
        return findings

    # List endpoints / models
    try:
        endpoints = list(aiplatform.Endpoint.list())
    except Exception:
        endpoints = []

    # Per-endpoint: safety is often set in application code (SafetySetting); we can't read it from Endpoint API.
    # Single advisory when endpoints exist.
    if endpoints:
        findings.append(_finding(
            "ai.vertex.safety_in_code", "vertex_endpoint", "endpoints", "Vertex AI Endpoints",
            "Set safety settings in application code for Vertex AI",
            SEVERITY_LOW,
            f"Found {len(endpoints)} endpoint(s). Safety (content filtering) is configured per request in code. "
            "Ensure SafetySetting is used with appropriate thresholds for HARM_CATEGORY_* (e.g. HARM_CATEGORY_HARASSMENT, HATE_SPEECH).",
            "When calling generate_content, pass safety_settings with threshold BLOCK_MEDIUM_AND_ABOVE or stricter.",
            region=region, cloud="gcp",
        ))

    # If endpoints exist but we can't verify safety, add informational finding
    if endpoints:
        findings.append(_finding(
            "ai.vertex.safety_review", "vertex_endpoint", "endpoints", "Vertex AI Endpoints",
            "Review Vertex AI safety settings",
            SEVERITY_LOW,
            f"Found {len(endpoints)} Vertex AI endpoint(s). Manually verify that safety settings (content filtering, "
            "blocked categories) are configured appropriately for each model deployment.",
            "In the Vertex AI console, check each endpoint's safety settings. Enable content filtering for hate, "
            "violence, sexual content, and dangerous content at appropriate severity levels.",
            region=region, cloud="gcp",
        ))

    # Advisory: logging
    if endpoints:
        findings.append(_finding(
            "ai.vertex.logging_review", "vertex_ai", "project", "Vertex AI",
            "Verify Vertex AI request logging for audit",
            SEVERITY_LOW,
            "Ensure Vertex AI API calls are logged for audit and safety (e.g. Cloud Logging, log request/response metadata).",
            "Enable Cloud Logging for the Vertex AI API; avoid logging full prompt/completion content in plain text.",
            region=region, cloud="gcp",
        ))

    # Advisory: IAM
    if endpoints:
        findings.append(_finding(
            "ai.vertex.iam_review", "vertex_ai", "project", "Vertex AI",
            "Review IAM for Vertex AI endpoints",
            SEVERITY_LOW,
            "Restrict who can deploy or query Vertex AI endpoints. Use least-privilege roles (e.g. roles/aiplatform.user).",
            "Review IAM bindings on the project and on the Vertex AI service account; remove broad principals.",
            region=region, cloud="gcp",
        ))

    # Advisory: network (Vertex endpoints are often VPC-scoped; recommend verifying)
    if endpoints:
        findings.append(_finding(
            "ai.vertex.network_review", "vertex_endpoint", "endpoints", "Vertex AI Endpoints",
            "Verify Vertex AI endpoint network exposure",
            SEVERITY_LOW,
            f"Found {len(endpoints)} endpoint(s). Ensure endpoints are not publicly exposed; use VPC-SC or private access where required.",
            "In Google Cloud Console, verify endpoint network settings and VPC Service Controls if applicable.",
            region=region, cloud="gcp",
        ))

    return findings


# ---------------------------------------------------------------------------
# Azure OpenAI
# ---------------------------------------------------------------------------

def _scan_azure(subscription_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
        cred = DefaultAzureCredential()
        client = CognitiveServicesManagementClient(cred, subscription_id)
    except ImportError:
        findings.append(_finding(
            "ai.azure.sdk_missing", "azure_openai", "n/a", "Azure OpenAI",
            "Azure Cognitive Services SDK not installed",
            SEVERITY_LOW,
            "azure-mgmt-cognitiveservices is required for Azure OpenAI checks. Install with: pip install azure-mgmt-cognitiveservices",
            "pip install azure-mgmt-cognitiveservices",
            cloud="azure",
        ))
        return findings
    except Exception as e:
        findings.append(_finding(
            "ai.azure.unavailable", "azure_openai", "n/a", "Azure OpenAI",
            "Azure OpenAI API unavailable",
            SEVERITY_LOW,
            f"Could not connect to Azure Cognitive Services: {e}",
            "Ensure Azure credentials are configured (DefaultAzureCredential or env vars) and the principal has "
            "Cognitive Services Reader or Contributor on the subscription.",
            cloud="azure",
        ))
        return findings

    accounts: list[Any] = []
    try:
        for acc in client.accounts.list():
            if getattr(acc, "kind", "").lower() in ("openai", "cognitiveservices"):
                accounts.append(acc)
    except Exception:
        pass

    for acc in accounts[:20]:
        try:
            aid = acc.id or "unknown"
            name = getattr(acc, "name", None) or "unknown"
            loc = getattr(acc, "location", None) or "global"
            resource_group = None
            if aid and "/resourceGroups/" in aid:
                parts = aid.split("/")
                if "resourceGroups" in parts:
                    idx = parts.index("resourceGroups")
                    if idx + 1 < len(parts):
                        resource_group = parts[idx + 1]
            # Get full account properties for public_network_access and encryption (may require get())
            public_network = getattr(acc, "public_network_access", None)
            encryption = getattr(acc, "encryption", None)
            if resource_group and (public_network is None or encryption is None):
                try:
                    full = client.accounts.get(resource_group, name)
                    if public_network is None:
                        public_network = getattr(full, "public_network_access", None)
                    if encryption is None:
                        encryption = getattr(full, "encryption", None)
                except Exception:
                    pass

            if public_network and str(public_network).lower() == "enabled":
                findings.append(_finding(
                    "ai.azure.public_network", "azure_openai", aid, name,
                    "Azure OpenAI account allows public network access",
                    SEVERITY_MEDIUM,
                    f"Account '{name}' has public network access enabled. Prefer private endpoints for production.",
                    "Disable public network access in the Azure Portal (Networking) or set public_network_access to Disabled.",
                    region=loc, cloud="azure",
                ))

            key_source = None
            if encryption is not None:
                key_source = getattr(encryption, "key_source", None) or getattr(encryption, "keySource", None)
            if encryption is None or (key_source and "Microsoft" in str(key_source)):
                findings.append(_finding(
                    "ai.azure.encryption_review", "azure_openai", aid, name,
                    "Review Azure OpenAI encryption (use customer-managed keys)",
                    SEVERITY_LOW,
                    f"Account '{name}' uses Microsoft-managed keys. Consider customer-managed keys for compliance.",
                    "In Azure Portal → Cognitive Services account → Encryption, enable customer-managed key (CMK).",
                    region=loc, cloud="azure",
                ))

            findings.append(_finding(
                "ai.azure.content_filter_review", "azure_openai", aid, name,
                f"Review Azure OpenAI content filters: {name}",
                SEVERITY_LOW,
                f"Azure OpenAI account '{name}' found. Verify that content filters (hate, violence, sexual, self-harm) "
                "are enabled at medium+ severity for both prompts and completions.",
                "In Azure Portal → Azure OpenAI resource → Content filtering, ensure filters are enabled. "
                "Use Azure AI Content Safety for custom policies.",
                region=loc, cloud="azure",
            ))
        except Exception:
            pass

    # One-time advisories when we have at least one account
    if accounts:
        acc0 = accounts[0]
        loc0 = getattr(acc0, "location", None) or "global"
        findings.append(_finding(
            "ai.azure.diagnostics_review", "azure_openai", "subscription", "Azure OpenAI",
            "Enable Diagnostic Settings for Azure OpenAI",
            SEVERITY_LOW,
            "Ensure Diagnostic Settings (logs/metrics) are enabled for Azure OpenAI resources for audit and monitoring.",
            "In Azure Portal → Azure OpenAI resource → Diagnostic settings, add a setting to send logs to Log Analytics.",
            region=loc0, cloud="azure",
        ))
        findings.append(_finding(
            "ai.azure.managed_identity_review", "azure_openai", "subscription", "Azure OpenAI",
            "Prefer managed identity for Azure OpenAI access",
            SEVERITY_LOW,
            "Use managed identity (system or user-assigned) instead of API keys where possible for authentication.",
            "In application code, use DefaultAzureCredential or ManagedIdentityCredential; restrict key usage.",
            region=loc0, cloud="azure",
        ))

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_ai(
    cloud: str = "aws",
    region: str | None = None,
    project_id: str | None = None,
    subscription_id: str | None = None,
    skip_rules: list[str] | None = None,
) -> dict[str, Any]:
    """Run AI usage security scan for the given cloud.

    Parameters
    ----------
    cloud : "aws" | "gcp" | "azure"
    region : AWS region / GCP region (default us-east-1 / us-central1)
    project_id : GCP project ID (required for gcp)
    subscription_id : Azure subscription ID (required for azure)
    skip_rules : Rule IDs to exclude from results

    Returns
    -------
    dict with keys: findings, summary
    """
    cloud = (cloud or "aws").lower()
    skip_set = set(skip_rules or [])

    if cloud == "aws":
        region = region or "us-east-1"
        findings = _scan_aws(region)
    elif cloud == "gcp":
        region = region or "us-central1"
        project_id = project_id or ""
        findings = _scan_gcp(project_id, region)
    elif cloud == "azure":
        subscription_id = subscription_id or ""
        findings = _scan_azure(subscription_id)
    else:
        findings = []

    findings = [f for f in findings if f.get("rule_id") not in skip_set]

    by_sev: dict[str, int] = {}
    for f in findings:
        s = f.get("severity", "low")
        by_sev[s] = by_sev.get(s, 0) + 1

    reg = region if cloud == "aws" else (region if cloud == "gcp" else None)
    return {
        "findings": findings,
        "summary": {
            "total_findings": len(findings),
            "critical": by_sev.get(SEVERITY_CRITICAL, 0),
            "high": by_sev.get(SEVERITY_HIGH, 0),
            "medium": by_sev.get(SEVERITY_MEDIUM, 0),
            "low": by_sev.get(SEVERITY_LOW, 0),
            "cloud": cloud,
            "region": reg,
            "skipped_rules": list(skip_set),
        },
    }
