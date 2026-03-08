# Changelog

All notable changes to CloudRadar are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- **Serverless & Usage (multi-cloud):** Serverless Security scan for AWS (Lambda, Step Functions, API Gateway, SQS, DynamoDB), GCP (Cloud Run, Cloud Functions), and Azure (Function Apps). Configurable checks per cloud; Lambda layers and extensions review.
- **Usage scan:** AWS-only CloudWatch-based usage findings (idle Lambdas, high errors, throttles). UI shows AWS-only message when GCP/Azure is selected.
- **Documentation:** Setup tab in Documentation (local/server setup, commands, AWS/GCP/Azure permission JSON). [SETUP.md](docs/SETUP.md), [RUNBOOKS.md](docs/RUNBOOKS.md), and this CHANGELOG.
- **Runbooks:** First scan, fix critical findings, add a new rule; guided tour (Setup → Scan → Reports). See [RUNBOOKS.md](docs/RUNBOOKS.md).
- **API docs:** FastAPI serves OpenAPI at `/docs` (Swagger UI) when the backend is running; see [API.md](docs/API.md).

### Changed

- **Documentation UI:** Setup section added below Overview with Run locally, Run on server, Commands reference, and cloud permission snippets.
- **Serverless & Usage UI:** Configure checks and empty-state messages are cloud-aware (AWS vs GCP vs Azure). Single “Run serverless scan” / “Run usage scan” button per tab.
- **IMPROVEMENTS.md:** Documentation and onboarding section updated with runbooks, guided tour, API OpenAPI/Swagger, and changelog references.

### Fixed

- Duplicate “Run serverless scan” and “Run usage scan” buttons removed from empty-state cards.
- GCP/Azure Serverless & Usage no longer shows AWS-only check names or usage text when Google Cloud or Azure is selected.

---

## [Earlier]

- Multi-cloud (AWS, GCP, Azure) support; multi-account (Organizations, org/folder, management groups).
- AI Usage Security scan (Bedrock, SageMaker, Vertex, Azure OpenAI); OWASP LLM / NIST AI RMF mapping.
- Security Scan with 30+ AWS services; GCP and Azure discovery (GCS, GCE, Firewalls, IAM; VMs, Storage, NSGs; Cloud Run, Cloud Functions, Azure Functions).
- Dashboard, Findings, Compliance, Governance, Attack Paths, Cost Optimisation, Pentest, Vulnerabilities.
- Scheduled scans, notifications, scan history, remediation tracking.
- Health endpoint `GET /api/health`; SSE scan progress; config and deployment docs.
