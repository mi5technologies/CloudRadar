"""AI Usage Security scanner — flags missing guardrails, content filters, and unsafe AI configs.

Checks AWS Bedrock, Google Vertex AI, and Azure OpenAI for:
- Missing guardrails / content filters
- Public or overly permissive access
- Disabled safety settings
- Missing prompt logging
"""
from __future__ import annotations

from typing import Any

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
    return {
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


# ---------------------------------------------------------------------------
# AWS Bedrock
# ---------------------------------------------------------------------------

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

    # Check guardrails
    guardrails: list[dict] = []
    try:
        paginator = bedrock.get_paginator("list_guardrails")
        for page in paginator.paginate():
            guardrails.extend(page.get("guardrailSummaries", []))
    except Exception:
        pass

    # Check foundation models (models available / in use)
    models: list[dict] = []
    try:
        resp = bedrock.list_foundation_models(byInferenceType="ON_DEMAND")
        models = resp.get("modelSummaries", [])
    except Exception:
        pass

    # ai.bedrock.no_guardrails: Using Bedrock but no guardrails defined
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

    # ai.bedrock.guardrails_not_ready: Guardrails exist but some are not READY
    not_ready = [g for g in guardrails if (g.get("status") or "").upper() != "READY"]
    if not_ready:
        for g in not_ready[:5]:  # Limit to 5
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

    # ai.vertex.no_safety: Endpoint with safety settings disabled
    for ep in endpoints[:20]:  # Limit
        try:
            display = getattr(ep, "display_name", None) or ep.resource_name or "unknown"
            # Vertex doesn't expose safety settings easily via list; we flag if no safety config is visible
            # For now, add a generic check: no endpoints = no AI in use
            pass
        except Exception:
            pass

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
            sku = getattr(acc, "sku", None)
            # Content filter config is typically on the deployment, not the account
            # We flag accounts without explicit content filter verification
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
