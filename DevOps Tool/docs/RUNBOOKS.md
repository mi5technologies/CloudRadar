# CloudRadar Runbooks

Short, step-by-step runbooks for common operations.

---

## Runbook: First scan

1. **Start the app** (from project root):
   ```bash
   python -m cspm.cli ui --host 127.0.0.1 --port 8000
   ```
2. Open **http://127.0.0.1:8000**.
3. Go to **Welcome** or **Setup** and select your cloud (AWS, Google Cloud, or Azure).
4. Enter credentials:
   - **AWS:** Region, Access Key ID, Secret Access Key (or use profile / IAM role on server).
   - **GCP:** Project ID and optional path to service account JSON.
   - **Azure:** Subscription ID, Tenant ID, Client ID, Client secret.
5. Optionally enable **Save to config** to persist credentials to `config.yaml` (restrict file permissions).
6. Go to **Security → Security Scan**, choose the same cloud and region (or project/subscription).
7. Leave all services selected (or narrow to a subset), then click **Run security scan**.
8. Watch the step-by-step progress; when done, review the **Post-scan summary** and go to **Findings** to see details and remediation.

**CLI alternative:**  
`python -m cspm.cli scan aws --save-snapshot` (then open the UI to view findings and reports).

---

## Runbook: Fix critical findings

1. Go to **Findings** in the sidebar.
2. Filter by **Severity → Critical** (and optionally by resource type or rule).
3. For each finding:
   - Click the row to open the slide-over panel.
   - Read **Detail** and **Remediation**.
   - Apply the change in your cloud console (or via IaC). Examples:
     - **S3 bucket not encrypted:** Enable default encryption on the bucket.
     - **Lambda has no DLQ:** Set DeadLetterConfig or OnFailure destination.
     - **IAM policy allows `*` on sensitive action:** Restrict the policy to least privilege.
4. (Optional) Use **Remediation** in the UI for supported findings: click **Apply fix** (dry-run first).
5. Re-run a **Security Scan** to confirm findings are resolved; check **Findings** again.

---

## Runbook: Add a new rule

1. **Create a YAML file** under `cspm/rules/` (e.g. `cspm/rules/my_checks.yaml`).
2. **Define the rule** in the same format as existing rules, for example:
   ```yaml
   - id: my_custom_check
     resource_type: s3
     condition:
       operator: equals
       field: encryption_enabled
       value: false
     severity: high
     title: "S3 bucket has no encryption"
     detail: "Enable default encryption."
     remediation: "Set default encryption (SSE-S3 or SSE-KMS) in bucket properties."
   ```
3. **Use standard fields** that your discovery/scanner already populate on assets (e.g. for S3: `encryption_enabled`, `public_access_block`, etc.). See existing rules in `cspm/rules/` for field names.
4. **Restart the app** (or run a new scan) so the rule engine loads the new file.
5. Run a **Security Scan** and check **Findings** for the new `rule_id`.

**Reference:** [Architecture](ARCHITECTURE.md) (Rule engine), existing files in `cspm/rules/`.

---

## Guided tour (Setup → Scan → Reports)

1. **Setup** — Configure credentials for one or more clouds (Welcome or Setup page). Save to config if you want persistence.
2. **Scan** — Security → Security Scan: pick cloud, region/project/subscription, run scan. Optionally use Serverless & Usage or AI Usage Security for targeted scans.
3. **Reports** — After the scan: Dashboard (KPIs and charts), Findings (filter and remediate), Audit (asset list CSV/JSON), Compliance, Governance, Attack Paths. Use the download links in the post-scan card for JSON/HTML reports.

For **API documentation** (OpenAPI/Swagger), open **http://&lt;host&gt;:8000/docs** when the backend is running (development or production, optionally behind auth).
