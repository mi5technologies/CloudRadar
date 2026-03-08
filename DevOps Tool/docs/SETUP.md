# CloudRadar Setup Guide

This guide covers installing and running CloudRadar locally, on a server, and the permissions required for each cloud provider.

---

## Run locally

### 1. Install dependencies

From the **project root**:

```bash
pip install -r requirements.txt
# Or editable install so the cspm package is importable:
pip install -e .

cd frontend && npm install && npm run build
```

### 2. Start the application

The backend serves both the API and the built Vue frontend:

```bash
python -m cspm.cli ui --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in your browser.

### 3. Development (frontend hot-reload)

Run the backend and frontend separately so the Vue app hot-reloads:

- **Terminal 1:** `python -m cspm.cli ui --host 127.0.0.1 --port 8000`
- **Terminal 2:** `cd frontend && npm run dev`

Open **http://127.0.0.1:5173**. Vite proxies `/api` to the backend.

### Windows

From PowerShell you can use:

```powershell
.\scripts\run_ui.ps1
```

---

## Run on a server (production)

### 1. Install and build

Same as local: `pip install -e .` and build the frontend.

### 2. Bind and reverse proxy

Bind to all interfaces and run behind Nginx (or Caddy/Traefik) with HTTPS:

```bash
python -m cspm.cli ui --host 0.0.0.0 --port 8000
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for Nginx configuration (including SSE for scan progress) and security notes.

### 3. Docker

Build and run (ensure `frontend/dist` exists or use a multi-stage build that runs `npm run build` inside the image):

```bash
docker build -t cloudradar .
docker run -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/snapshots:/app/snapshots \
  cloudradar
```

Do not bake credentials into the image; use environment variables or a mounted config.

### 4. Process management

Use systemd, supervisord, or a container orchestrator to keep the process running and restart on failure.

---

## Commands quick reference

| Command | Description |
|--------|-------------|
| `python -m cspm.cli ui --host 127.0.0.1 --port 8000` | Start Web UI (local) |
| `python -m cspm.cli ui --host 0.0.0.0 --port 8000` | Start Web UI (server) |
| `python -m cspm.cli scan aws [--save-snapshot] [--only ec2,s3]` | Run CLI scan; optional snapshot |
| `python -m cspm.cli assets list [--cloud aws] [--type ec2] [--output csv\|json]` | List assets (audit) |
| `python -m cspm.cli assets diff <snapshot_before> <snapshot_after>` | Diff two snapshots |
| `python -m cspm.cli compliance [--framework cis\|soc2] [--output json\|html]` | Compliance report |
| `python -m cspm.cli governance [--output json\|html]` | Governance report |
| `python -m cspm.cli pentest [--exposed] [--secrets] [--exploit-map]` | Pentest scan |
| `cd frontend && npm run build` | Build Vue frontend |
| `cd frontend && npm run dev` | Frontend dev server (hot-reload) |

---

## Cloud provider permissions

### AWS — IAM policy (JSON)

Attach a policy like the one below to the IAM user or role used for scanning. For **multi-account** (AWS Organizations), use:

- **Management account:** [docs/iam-policies/aws-management-account-policy.json](iam-policies/aws-management-account-policy.json)
- **Member accounts:** [docs/iam-policies/aws-member-account-scanner-policy.json](iam-policies/aws-member-account-scanner-policy.json) and [aws-member-account-trust-policy.json](iam-policies/aws-member-account-trust-policy.json)

Single-account / minimal policy (see [README.md](../README.md) and [iam-policies/aws-member-account-scanner-policy.json](iam-policies/aws-member-account-scanner-policy.json) for the full list):

- `sts:GetCallerIdentity`
- EC2, S3, RDS, Lambda, IAM (list/get), WAFv2, ECR, CloudTrail, EKS, ECS, KMS, API Gateway, SQS, DynamoDB, GuardDuty, CloudWatch (metric filters), Secrets Manager, SNS, CloudFront, Step Functions
- For **Serverless & Usage** scans: Lambda `GetFunction`, `GetFunctionEventInvokeConfig`; CloudWatch Logs for usage metrics

### Google Cloud — roles

Grant these roles to the service account used by CloudRadar:

- **Per project:** `roles/viewer`, `roles/securityreviewer`, `roles/cloudasset.viewer`, `roles/storage.objectViewer`, `roles/compute.viewer`, `roles/iam.securityReviewer`
- **Org/folder (multi-project):** `roles/resourcemanager.projectViewer`, `roles/resourcemanager.folderViewer`
- **Cloud Run & Cloud Functions (Serverless scan):** Ensure the service account can call `run.services.list` and `cloudfunctions.functions.list` (e.g. Cloud Run Admin read-only or a custom role with those permissions)

See [docs/iam-policies/gcp-required-roles.json](iam-policies/gcp-required-roles.json) for the full reference.

### Azure — RBAC custom role

Create a custom role with read actions for:

- Management groups and subscriptions
- Compute, Storage, Network (NSGs, VNets), Authorization

Assign the role to the app registration at subscription or management group scope. Replace `YOUR_SUBSCRIPTION_ID` or management group ID in `AssignableScopes`.

See [docs/iam-policies/azure-custom-role-definition.json](iam-policies/azure-custom-role-definition.json) for the full JSON. For **Azure Function Apps** (Serverless scan), ensure the principal has read access to Microsoft.Web/sites (e.g. `Microsoft.Web/sites/read`).
