# Suggested Improvements

This document lists concrete improvements that can be made to CloudRadar, grouped by area.

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

- **Runbooks** – Short runbooks for “first scan”, “fix critical findings”, “add new rule”.
- **Video or guided tour** – Short walkthrough of Setup → Scan → Reports.
- **API OpenAPI/Swagger** – Serve `/docs` (FastAPI default) in development and optionally in production behind auth.
- **Changelog** – Keep a CHANGELOG.md for releases and breaking changes.

## Testing and quality

- **Integration tests** – Tests that run a minimal scan (e.g. mock or test account) and assert on report shape.
- **Frontend tests** – Unit or E2E tests for critical flows (setup, start scan, view progress).
- **CI pipeline** – GitHub Actions / GitLab CI to run lint, tests, and build frontend on push.

Prioritizing **scheduled scans**, **dashboard metrics**, **encrypt credentials**, and **GCP/Azure discovery** will have the highest impact for most users.
