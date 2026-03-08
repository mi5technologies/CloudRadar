# Suggested Improvements

This document lists concrete improvements that can be made to CloudRadar, grouped by area. Items marked with ✅ have been implemented.

---

## Multi-account and organization support

- ✅ **AWS Organizations** – Support scanning all member accounts via `organizations:ListAccounts` and `sts:AssumeRole` into a delegated scanner role in each account. Config: `aws.organization_role_arn` or `aws.role_assumption_template`. Aggregate findings by `account_id`.
- ✅ **Google Cloud organization / folders** – Use Resource Manager API (`resourcemanager.projects.list`) to list projects under an org or folder. Config: `gcp.organization_id` or `gcp.folder_id`. Scan each project and aggregate by `project_id`.
- ✅ **Azure management groups / multiple subscriptions** – List subscriptions via `managementGroups.get_subscriptions_under_management_group()` or explicit `subscription_ids`. Config: `azure.management_group_id` or `azure.subscription_ids`. Scan each subscription and aggregate by `subscription_id`.
- ✅ **Unified multi-account report** – Single report spanning all accounts/projects/subscriptions with filters by account, region, and severity. Findings and catalog entries include `account_id` / `project_id` / `subscription_id`.
- ✅ **Credential model** – Extend `AWSAuth`, `GCPAuth`, `AzureAuth` to support multiple targets; add account/project/subscription selector in Setup and scan UI.

---

## AI-focused scans and tests

- ✅ **Prompt injection / jailbreak prevention** – Bedrock: guardrail content policy checked for PROMPT_ATTACK filter; Vertex/Azure: safety and content filter review findings.
- ✅ **Model access control** – Bedrock: Lambda–Bedrock IAM/logging review finding; SageMaker endpoint and notebook checks.
- ✅ **Data residency** – Scans run per region; Bedrock models are regional.
- ✅ **Usage and cost** – Bedrock: provisioned throughput discovered (list_provisioned_model_throughputs); advisory in scanner.
- ✅ **Inference logging** – Bedrock: advisory finding to verify inference logging; Vertex/Azure: safety review includes logging.
- ✅ **Fine-tuning security** – SageMaker training jobs discovered; endpoint/notebook IAM and encryption checks.
- ✅ **SageMaker** – Discovery and scanner: notebooks (direct internet access, KMS), endpoints (encryption), training jobs.
- ✅ **AI in Lambda / Functions** – Finding to review Lambda functions that invoke Bedrock (IAM, VPC, logging).
- ✅ **AI Security compliance** – Findings mapped to OWASP LLM Top 10 and NIST AI RMF (owasp_llm, nist_ai_rmf on each finding).
- ✅ **Bedrock Knowledge Base** – Discovery and checks for S3 data source access, role ARN, and data sources.

---

## Serverless and usage scans

- ✅ **Serverless Security scan** – Dedicated scan (Security → Serverless & Usage → Serverless Security): Lambda (no DLQ/OnFailure, timeout >5min, env secrets, reserved concurrency 0, VPC review), Step Functions (logging, X-Ray), API Gateway (usage plan, access logging), SQS (no DLQ, visibility timeout), DynamoDB (streams). Uses last scan assets or discovers lambda, stepfunctions, api_gateway, sqs, dynamodb. API: `POST /api/serverless-scan`.
- ✅ **Usage scan** – Dedicated scan (Security → Serverless & Usage → Usage Scan): CloudWatch metrics for Lambda (idle = 0 invocations, high error rate, throttles) over configurable days. API: `POST /api/usage-scan` with `days_lookback`.
- **Lambda** – Cold-start tuning (high memory + short duration); reserved concurrency throttling risk; VPC config (Lambdas in VPC without NAT for outbound) — partially covered.
- **Step Functions** – IAM PassRole (future); express vs standard cost/durability.
- **EventBridge** – Rules: targets (Lambda, SQS) and IAM; schema registry validation.
- **API Gateway** – Authorizers (Lambda/Cognito); request validation enabled.
- **SQS** – Visibility timeout vs Lambda timeout (duplicate processing) — advisory in scanner; FIFO vs standard.
- **DynamoDB** – On-demand vs provisioned cost analysis; GSI/LSI unused indexes; Streams encryption and consumer IAM — streams advisory done.
- **Cloud Run** – Min instances (cost vs cold-start); concurrency limits; VPC egress private connectivity.
- **Azure Functions** – Consumption vs Premium cost; Durable Functions storage; managed identity vs connection strings.
- **GCP Cloud Functions** – Gen1 vs Gen2 migration; Eventarc event source IAM; Secret Manager usage.
- **Usage-based cost** – Lambda GB-seconds and invocations (usage scan); DynamoDB read/write units; API Gateway requests; SQS message volume.
- **Lambda layers** – Scan for outdated or vulnerable layers.
- **Lambda extensions** – Security and observability extensions.

---

## Product and UX

- **Scheduled scans** – Cron or in-app scheduler to run scans (e.g. daily) and notify on new findings or drift.
- **Dashboard metrics** – Summary cards: total findings by severity, last scan time, trend vs previous run, top failing rules.
- **Findings list in UI** – Dedicated page to browse findings (filter by severity, resource type, rule), with link to report download.
- **Multi-account / multi-region** – Support multiple AWS accounts or regions in one scan and aggregate in reports.
- **Alerting** – Webhook or email when critical/high findings appear or when compliance score drops.
- **Dark/light theme toggle** – User preference for UI theme.

## Security and compliance

- **Encrypt credentials at rest** – Encrypt `config.yaml` or use OS keyring / secret manager instead of plain text.
- **Role-based access** – Optional auth layer (e.g. OIDC, API keys) so only authorized users run scans or view results.
- **Audit log** – Log who ran which scan when and from where (for compliance).
- **More compliance frameworks** – HIPAA, PCI-DSS, or custom control sets.
- **Remediation from UI** – Buttons or runbooks to apply safe fixes (e.g. enable S3 encryption) with confirmation.

## GCP and Azure

- **GCP discovery** – Implement discovery for GCE, GCS, Cloud IAM, VPC, etc., and wire into scan/report pipeline.
- **Azure discovery** – Implement discovery for VMs, Storage, ARM resources, etc.
- **Unified multi-cloud report** – Single report that spans AWS + GCP + Azure with a clear cloud/account dimension.

## Scanning and rules

- **Custom rules UI** – Add/edit YAML rules from the UI (with validation) instead of only file-based rules.
- **Rule templates** – Predefined rule packs (e.g. “CIS AWS 1.5”) that can be enabled/disabled.
- **Scan scope** – Choose regions, tags, or OUs to limit scope and cost.
- **Rate limiting / retries** – Respect cloud API rate limits and retry with backoff.

## DevOps and operations

- **Health endpoint** – `GET /api/health` for load balancers and monitoring.
- **Structured logging** – JSON logs with levels and request IDs for production.
- **Metrics** – Expose Prometheus metrics (scan duration, finding counts, errors).
- **Database backend** – Optional PostgreSQL for findings and history instead of only file-based snapshots.
- **Docker image with frontend** – Multi-stage build that produces a single image with Vue app built and served.

## Documentation and onboarding

- ✅ **Runbooks** – Short runbooks for “first scan”, “fix critical findings”, “add new rule”. See [RUNBOOKS.md](RUNBOOKS.md).
- ✅ **Video or guided tour** – Walkthrough of Setup → Scan → Reports documented in [RUNBOOKS.md](RUNBOOKS.md#guided-tour-setup--scan--reports).
- ✅ **API OpenAPI/Swagger** – FastAPI serves interactive docs at `GET /docs` (Swagger UI) when the backend is running; see [API.md](API.md).
- ✅ **Changelog** – [CHANGELOG.md](../CHANGELOG.md) for releases and notable changes.

## Testing and quality

- **Integration tests** – Tests that run a minimal scan (e.g. mock or test account) and assert on report shape.
- **Frontend tests** – Unit or E2E tests for critical flows (setup, start scan, view progress).
- **CI pipeline** – GitHub Actions / GitLab CI to run lint, tests, and build frontend on push.

---

## Implementation priority

1. ✅ **Health endpoint** – Implemented. `GET /api/health` returns `{status, timestamp}` for load balancers.
2. ✅ **Lambda DLQ** – Implemented. Discovery fetches DeadLetterConfig and OnFailure destination; rule `lambda_no_dlq` flags Lambdas without failure destination.
3. ✅ **Step Functions discovery** – Implemented. New `stepfunctions_discovery` and `stepfunctions_scanner`; added to AWS provider and Security Scan UI.
4. **SageMaker discovery** – New AWS AI resource type.
5. ✅ **Multi-account config schema** – Implemented. AWS Organizations, GCP org/folder, Azure management groups; Setup UI and config support.
6. ✅ **AI inference logging checks** – Extended ai_scanner with inference logging advisory, guardrail prompt attack/PII checks, SageMaker, Knowledge Base, and OWASP/NIST mapping.

Prioritizing **scheduled scans**, **dashboard metrics**, **encrypt credentials**, and **GCP/Azure discovery** will have the highest impact for most users.
