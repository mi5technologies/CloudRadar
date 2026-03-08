# CloudRadar – Architecture

This document describes the high-level architecture, data flow, and main components of CloudRadar (multi-cloud Security Posture Management).

## Overview

CloudRadar is a multi-cloud security platform that:

1. **Discovers** cloud resources (EC2, S3, RDS, Lambda, IAM, VPC, EBS, EKS, ECS, CloudTrail, KMS, API Gateway, SQS, DynamoDB, GuardDuty, CloudWatch, WAF, ALB, Step Functions; GCP: GCS, GCE, Firewalls, IAM, Cloud Run, Cloud Functions; Azure: VMs, Storage, NSGs, Function Apps) via provider APIs.
2. **Scans** them against configurable rules to produce security findings.
3. **Tracks** changes over time via snapshots and diff reports.
4. **Reports** on compliance (CIS, SOC2), governance (tags, policies), and basic pentest (exposed services, secrets, exploit mapping).
5. Exposes a **CLI** and a **Web UI** (Vue 3 + FastAPI) for running scans and viewing results.

## High-Level Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  AWS / GCP /    │────▶│  Discovery       │────▶│  Asset          │
│  Azure APIs     │     │  (per resource   │     │  Collector      │
│                 │     │   type)          │     │  (enrich/scan)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Reports        │◀────│  Rule Engine     │◀────│  Assets +       │
│  (JSON/HTML/    │     │  (YAML rules)     │     │  Catalog         │
│   CSV, etc.)    │     │  Risk Engine     │     │                  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                          │
        │                          ▼
        │                 ┌──────────────────┐
        │                 │  Snapshots       │
        │                 │  Change Detector │
        │                 └──────────────────┘
        ▼
┌─────────────────┐     ┌──────────────────┐
│  Compliance     │     │  Governance      │
│  (CIS, SOC2)   │     │  (tags, policy)  │
└─────────────────┘     └──────────────────┘
```

## Components

### Core (`cspm/core/`)

- **ScanController** – Orchestrates a full scan: get provider → authenticate → discover assets → collect/enrich → run rule engine → compute risk → build catalog → optionally save snapshot.
- **Asset collector** – Takes raw discovered assets and runs per-resource scanners (S3, EC2, RDS, Lambda, IAM, network, WAF, CloudTrail, VPC, EBS, EKS, ECS, KMS, API Gateway, SQS, DynamoDB, GuardDuty, CloudWatch).
- **Asset catalog** – Builds a flat catalog from enriched assets for audit export and governance.

### Providers (`cspm/providers/`)

- **AWS** – Full discovery for 20+ resource types (EC2, S3, RDS, Lambda, IAM Users/Roles, Security Groups, ALBs, WAF, CloudTrail, VPC, EBS, EKS, ECS Clusters/Task Defs, KMS, API Gateway, SQS, DynamoDB, GuardDuty, CloudWatch alarms, Step Functions) with optional progress callbacks. Supports **multi-account** via Organizations and role-assumption template (see [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md)).
- **GCP** – Discovery for GCS, GCE, Firewalls, IAM bindings, **Cloud Run**, and **Cloud Functions (Gen2)**. Multi-project via organization/folder ID (see [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md)).
- **Azure** – Discovery for VMs, Storage Accounts, NSGs, and **Azure Function Apps**. Multi-subscription via management group or subscription list (see [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md)).

### Discovery (`cspm/discovery/`)

Per–resource-type modules that call cloud APIs and return lists of raw resources:

| Module | Service | What it discovers |
|---|---|---|
| `ec2_discovery` | EC2 | Instances (type, state, public IP, tags, security groups) |
| `s3_discovery` | S3 | Buckets |
| `rds_discovery` | RDS | DB instances (engine, public accessibility, encryption) |
| `lambda_discovery` | Lambda | Functions (runtime, timeout, environment, tags) |
| `iam_discovery` | IAM | Users and roles |
| `network_discovery` | VPC / ELBv2 | Security groups (ingress rules) and ALBs (scheme, public) |
| `waf_discovery` | WAF | WAFv2 Web ACLs and resource associations |
| `cloudtrail_discovery` | CloudTrail | Trails (logging, multi-region, log validation, CloudWatch integration) |
| `vpc_discovery` | VPC + EBS | VPCs (default VPC, flow logs) and EBS volumes (encryption) |
| `eks_discovery` | EKS | Clusters (public endpoint, CIDR restrictions, logging, secrets encryption) |
| `ecs_discovery` | ECS | Clusters (Container Insights) and task definitions (privileged, logging, root user) |
| `kms_discovery` | KMS | Customer-managed keys (rotation, state) |
| `apigateway_discovery` | API Gateway | REST and HTTP APIs (logging, WAF attached) |
| `sqs_discovery` | SQS | Queues (encryption, public policy) |
| `dynamodb_discovery` | DynamoDB | Tables (encryption, point-in-time recovery) |
| `guardduty_discovery` | GuardDuty | Detector status per region (enabled / not configured) |
| `cloudwatch_discovery` | CloudWatch | CIS metric filter checks (root usage, IAM/CloudTrail/VPC/KMS/S3 changes) |

### Scanners (`cspm/scanners/`)

- Enrich raw assets with security-relevant attributes (e.g. S3 encryption, IAM wildcards, WAF associations, EBS encryption, EKS endpoint exposure, DynamoDB PITR, SQS public policy).
- **AI scanner** – Separate scan path for AI resources: AWS Bedrock (guardrails, prompt-attack/PII filters, inference logging, Knowledge Base S3/IAM), Lambda–Bedrock review, SageMaker (notebook internet/encryption, endpoint encryption), plus Vertex AI and Azure OpenAI safety checks. Findings are mapped to OWASP LLM Top 10 and NIST AI RMF. See [AI Scans](AI_SCANS.md).

### Rule engine (`cspm/rule_engine/`)

- Loads YAML rules from `cspm/rules/`, evaluates them against enriched assets, and produces findings (severity, rule_id, resource_id).

### Risk engine (`cspm/risk_engine/`)

- Aggregates findings into a risk score and by-severity counts.

### Change detection (`cspm/change_detection/`)

- **SnapshotManager** – Saves/loads scan results as snapshots (e.g. under `snapshots/`).
- **ChangeDetector** – Compares current state to last snapshot or diffs two snapshots (added/removed/modified).

### Reporting (`cspm/reporting/`)

- **JSON/HTML report** – Scan summary and findings.
- **Audit export** – Catalog as CSV or JSON.
- **Change report** – Diff as JSON or HTML.

### Compliance (`cspm/compliance/`)

- Maps findings to CIS and SOC2 controls and produces pass/fail reports.

### Governance (`cspm/governance/`)

- **Tag policy engine** – Required tags, compliance counts.
- **Resource policy engine** – Forbidden instance types, regions, etc.
- **Governance report** – Combined output (JSON/HTML).

### Pentest (`cspm/pentest/`)

- **Exposed services** – Resources with 0.0.0.0/0 on sensitive ports.
- **Secrets scan** – Uses detect-secrets (optional).
- **Exploit mapping** – Maps findings to potential exploit scenarios.

### Vulnerability (`cspm/vulnerability/`)

- **ECR scanner** – Image scan findings.
- **AMI check** – Extensible AMI checks.
- **Vulnerability scanner** – Orchestrates ECR/AMI and returns a unified list.

### UI (`cspm/ui/`)

- **FastAPI app** – Serves `/api` (status, setup, jobs/scan, SSE progress, audit, compliance, governance, pentest, download). Serves Vue SPA from `frontend/dist`.
- **State** – In-memory AWS/GCP/Azure credentials and apply to env; optional persist to `config.yaml`.
- **Jobs** – Background scan jobs with step progress pushed via SSE; polling fallback via `GET /api/jobs/{id}`.

### Frontend (`frontend/`)

- **Vue 3 + Vite** – SPA with cloud selection (AWS/GCP/Azure), Setup (per-cloud credentials), Dashboard, Security Scan (with step-by-step progress), Audit, Compliance, Governance, Pentest.
- **API client** – Calls `/api`, subscribes to scan progress via EventSource, optional polling.

## Configuration and Credentials

- **Config** – `config.yaml` (optional), env vars (`AWS_DEFAULT_REGION`, `CSPM_SNAPSHOTS_DIR`, `CSPM_RULES_DIR`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS`, `AZURE_*`).
- **Credentials** – Set via Web UI Setup (persisted to `config.yaml` if chosen) or environment; applied to process env before each scan so boto3/SDKs use them. The same credentials are used for the **AI scan** (Bedrock, SageMaker, Vertex, Azure OpenAI); see [AI Scans](AI_SCANS.md). For **multi-cloud** and **multi-account** setup, see [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md).

## Extensibility

- **Rules** – Add or edit YAML under `cspm/rules/` to change security checks.
- **Discovery** – Implement or extend discovery modules per cloud/resource type.
- **Scanners** – Add new scanners and wire them in the asset collector.
- **Providers** – GCP/Azure discovery can be filled in following the AWS pattern (discover → collect → rules → reports).
