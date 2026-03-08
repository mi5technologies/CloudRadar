# AI-Focused Scans and Tests

CloudRadar includes an **AI Usage Security** scan that checks AWS Bedrock, Google Vertex AI, and Azure OpenAI (and related AI resources) for guardrails, content filters, safety settings, and secure configuration. Findings are mapped to **OWASP LLM Top 10** and **NIST AI RMF** where applicable.

---

## Overview

The AI scan runs separately from the main security scan. You trigger it from the UI (**Security → AI Usage Security**) or via the API (`POST /api/ai-scan`). It supports **all three clouds**:

- **AWS**: Checks Bedrock guardrails (prompt attack prevention, PII), foundation models, Knowledge Bases (S3/data source IAM), inference logging advisory, Lambda–Bedrock review, and SageMaker (notebooks, endpoints, training jobs).
- **GCP (Google Cloud)**: Checks Vertex AI endpoints: safety settings in code, manual safety review, request logging, IAM least-privilege, and network exposure. Multiple advisories when endpoints exist.
- **Azure**: Lists Azure OpenAI / Cognitive Services accounts; checks content filters, public network access, encryption (CMK), Diagnostic Settings, and managed identity. Per-account and one-time advisories.

Results include **findings** (with severity, detail, remediation) and a **summary** (counts by severity). Each finding can include **owasp_llm** and **nist_ai_rmf** for compliance mapping.

---

## How to run the AI scan

### From the UI

1. Go to **Security → AI Usage Security**.
2. Select the cloud (AWS, GCP, or Azure).
3. Optionally expand **Configure checks** and enable/disable specific rule IDs (e.g. skip low-severity or SDK-missing rules).
4. Click **Run AI scan**.
5. View findings in the table; click a row to see detail, remediation, and OWASP/NIST mapping. Use **Export CSV** to download.

### From the API

```http
POST /api/ai-scan
Content-Type: application/json

{
  "cloud": "aws",
  "region": "us-east-1",
  "project_id": null,
  "subscription_id": null,
  "skip_rules": ["ai.bedrock.inference_logging"]
}
```

- **cloud**: `"aws"` | `"gcp"` | `"azure"`.
- **region**: AWS or GCP region (e.g. `us-east-1`, `us-central1`). Optional; defaults apply.
- **project_id**: GCP project ID (required for GCP if not in config).
- **subscription_id**: Azure subscription ID (required for Azure if not in config).
- **skip_rules**: List of rule IDs to exclude from results.

Response:

```json
{
  "findings": [
    {
      "rule_id": "ai.bedrock.no_guardrails",
      "resource_type": "bedrock",
      "resource_id": "account",
      "resource_name": "Bedrock Account",
      "title": "No Bedrock Guardrails configured",
      "severity": "high",
      "detail": "...",
      "remediation": "...",
      "region": "us-east-1",
      "cloud": "aws",
      "owasp_llm": "LLM01: Prompt Injection",
      "nist_ai_rmf": "GOVERN 1.1, 3.1; MAP 1.1; MANAGE 2.1"
    }
  ],
  "summary": {
    "total_findings": 1,
    "critical": 0,
    "high": 1,
    "medium": 0,
    "low": 0,
    "cloud": "aws",
    "region": "us-east-1",
    "skipped_rules": ["ai.bedrock.inference_logging"]
  }
}
```

---

## AWS: Checks performed

| Rule ID | Severity | What it checks |
|--------|----------|----------------|
| `ai.bedrock.no_guardrails` | high | Foundation models are available but no Bedrock Guardrails are defined. |
| `ai.bedrock.guardrail_not_ready` | medium | A guardrail exists but its status is not READY. |
| `ai.bedrock.guardrail_no_prompt_attack` | high | Guardrail content policy does not have PROMPT_ATTACK filter (jailbreak/prompt injection prevention). |
| `ai.bedrock.guardrail_no_pii` | medium | Guardrail has a sensitive information policy but no PII entities with BLOCK or ANONYMIZE. |
| `ai.bedrock.inference_logging` | low | Advisory: verify that inference (prompts/completions) logging is enabled for audit. |
| `ai.bedrock.knowledge_base_s3_iam` | medium/low | Knowledge Base missing service role or data sources; ensure S3/data source access and IAM are least-privilege. |
| `ai.lambda_bedrock_review` | low | Advisory: review Lambda functions that invoke Bedrock (IAM, VPC, CloudWatch logging). |
| `ai.sagemaker_notebook_public` | medium | SageMaker notebook instance has direct internet access enabled. |
| `ai.sagemaker_notebook_encryption` | low | SageMaker notebook not encrypted with a customer-managed KMS key. |
| `ai.sagemaker_endpoint_encryption` | low | SageMaker endpoint config does not use a KMS key for encryption. |
| `ai.aws.unavailable` | low | Bedrock API could not be reached (credentials or permissions). |

Discovery uses **Bedrock** (guardrails, foundation models, provisioned throughput, guardrail details for content/PII) and **Bedrock Agent** (knowledge bases and data sources). **SageMaker** discovery lists notebook instances, endpoints, endpoint configs, and training jobs.

---

## GCP: Checks performed

| Rule ID | Severity | What it checks |
|--------|----------|----------------|
| `ai.vertex.safety_review` | low | Lists Vertex AI endpoints and recommends a manual review of safety settings (content filtering, blocked categories). |
| `ai.vertex.safety_in_code` | low | When endpoints exist: ensure SafetySetting is used in application code with BLOCK_MEDIUM_AND_ABOVE for generate_content. |
| `ai.vertex.logging_review` | low | Advisory: enable Cloud Logging for Vertex AI API calls for audit; avoid logging full prompt/completion in plain text. |
| `ai.vertex.iam_review` | low | Advisory: use least-privilege IAM (e.g. roles/aiplatform.user); review bindings on project and service account. |
| `ai.vertex.network_review` | low | Advisory: verify endpoints are not publicly exposed; use VPC-SC or private access where required. |
| `ai.gcp.unavailable` | low | Vertex AI API could not be initialized. |
| `ai.gcp.sdk_missing` | low | `google-cloud-aiplatform` is not installed. |

---

## Azure: Checks performed

| Rule ID | Severity | What it checks |
|--------|----------|----------------|
| `ai.azure.content_filter_review` | low | Azure OpenAI / Cognitive Services account found; recommends verifying content filters (hate, violence, sexual, self-harm) in the portal. |
| `ai.azure.public_network` | medium | Account has public network access enabled; recommends disabling and using private endpoints. |
| `ai.azure.encryption_review` | low | Account uses Microsoft-managed keys; recommends customer-managed keys (CMK) for compliance. |
| `ai.azure.diagnostics_review` | low | Advisory: enable Diagnostic Settings (logs/metrics) for Azure OpenAI resources (e.g. Log Analytics). |
| `ai.azure.managed_identity_review` | low | Advisory: use managed identity (DefaultAzureCredential / ManagedIdentityCredential) instead of API keys. |
| `ai.azure.unavailable` | low | Azure Cognitive Services API could not be reached. |
| `ai.azure.sdk_missing` | low | `azure-mgmt-cognitiveservices` is not installed. |

---

## OWASP LLM Top 10 and NIST AI RMF mapping

Each finding can include:

- **owasp_llm**: Category from [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) (e.g. LLM01: Prompt Injection, LLM07: Insufficient Access Control).
- **nist_ai_rmf**: Relevant controls from [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) (e.g. GOVERN, MAP, MANAGE).

These fields are set in the backend (`cspm/scanners/ai_framework_mapping.py`) and appear in the finding detail panel and in the CSV export.

---

## Permissions required

- **AWS**: For full AI scan, the scanning role needs (in addition to standard scan permissions) Bedrock and Bedrock Agent read APIs (e.g. `list_guardrails`, `get_guardrail`, `list_foundation_models`, `list_knowledge_bases`, `get_knowledge_base`, `list_data_sources`) and SageMaker list/describe (e.g. `list_notebook_instances`, `list_endpoints`, `list_training_jobs`). See [IAM policy files](iam-policies/README.md); the member-account scanner policy does not include Bedrock/SageMaker by default—add those actions if you run the AI scan in multi-account mode.
- **GCP**: Service account with Vertex AI / AI Platform access (e.g. `roles/aiplatform.user`).
- **Azure**: Service principal with Cognitive Services Reader (or similar) on the subscription or resource group.

---

## Related documentation

- [Configuration](CONFIGURATION.md) – `config.yaml` and environment variables for AWS, GCP, Azure.
- [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md) – Multi-account and multi-cloud setup.
- [Architecture](ARCHITECTURE.md) – High-level components (discovery, scanners, providers).
