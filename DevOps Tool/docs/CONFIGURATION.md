# Configuration

This document describes all configuration options for CloudRadar: config file, environment variables, and cloud-specific credentials.

## Config file: `config.yaml`

Optional. By default the tool looks for `config.yaml` in the current working directory when the UI loads or when `Config` is instantiated.

### Structure

```yaml
aws:
  access_key_id: "AKIA..."
  secret_access_key: "..."
  session_token: null
  profile_name: null
  region: "us-east-1"
  # Multi-account: scan all org accounts via assume-role
  role_assumption_template: "arn:aws:iam::{account_id}:role/CloudRadarScanner"
  organization_role_arn: null  # alternative: fixed ARN

gcp:
  project_id: "my-gcp-project"
  credentials_path: "/path/to/service-account.json"
  # Multi-project: list projects under org or folder
  organization_id: null
  folder_id: null

azure:
  subscription_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  client_secret: "..."
  # Multi-subscription: list subscriptions under management group or explicit list
  management_group_id: null
  subscription_ids: []
```

- **AWS** – Either `access_key_id` + `secret_access_key` (and optional `session_token`) or `profile_name`. `region` is used when not overridden by CLI/UI. For **multi-account**: set `role_assumption_template` (e.g. `arn:aws:iam::{account_id}:role/CloudRadarScanner`) to scan all organization accounts via `organizations:ListAccounts` and `sts:AssumeRole`. See [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md) and [iam-policies/](iam-policies/) for IAM roles and JSON policies.
- **GCP** – `project_id` is required for single project. `credentials_path` is optional. For **multi-project**: set `organization_id` or `folder_id` to list projects via Resource Manager API. See [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md).
- **Azure** – Service principal: `subscription_id`, `tenant_id`, `client_id`, `client_secret`. For **multi-subscription**: set `management_group_id` or `subscription_ids` to scan multiple subscriptions. See [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md) and [iam-policies/](iam-policies/) for RBAC role JSON.

**Security:** Storing credentials in `config.yaml` is plain text. Restrict file permissions and never commit this file.

For **multi-cloud** (AWS + GCP + Azure in one deployment) and **multi-account** (org/folder/subscriptions per cloud), see [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md). The **AI Usage Security** scan uses the same cloud credentials; see [AI Scans](AI_SCANS.md) for rule IDs and permissions.

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_DEFAULT_REGION` | AWS region for scans | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key (if not in config) | — |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | — |
| `AWS_SESSION_TOKEN` | AWS session token (optional) | — |
| `AWS_PROFILE` | AWS profile name | — |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | — |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | — |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | — |
| `AZURE_TENANT_ID` | Azure tenant ID | — |
| `AZURE_CLIENT_ID` | Azure app (client) ID | — |
| `AZURE_CLIENT_SECRET` | Azure client secret | — |
| `CSPM_SNAPSHOTS_DIR` | Directory for snapshot files | `snapshots` |
| `CSPM_RULES_DIR` | Directory for YAML rules | `cspm/rules` |
| `CSPM_DB_URL` | Database URL (if used) | `sqlite:///cspm.db` |

The Web UI **Setup** page writes AWS/GCP/Azure credentials into `config.yaml` (if “Save to config” is checked) and applies them to the process environment so subsequent scans use them.

## Cloud-specific setup

### AWS

- **Keys:** Access Key ID + Secret Access Key (optional Session Token), plus Region.
- **Profile:** Alternatively set `AWS_PROFILE` and Region (e.g. via env or config `profile_name`).
- **IAM:** Use a dedicated scanning user/role with read-only permissions. See [README](../README.md#aws-iam-permissions-least-privilege-for-scanning) for a sample policy.

### GCP

- **Project ID:** Required. Set in Setup or via `GOOGLE_CLOUD_PROJECT`.
- **Credentials:** Either provide a path to a service account JSON file, or use Application Default Credentials (`gcloud auth application-default login`).

### Azure

- **Service principal:** Subscription ID, Tenant ID, Client (application) ID, Client secret. Set in Setup or via `AZURE_*` env vars.
- **Permissions:** The app registration used for the service principal needs read-only access to the subscription resources you want to scan.

## Config path

- **Default:** `config.yaml` in the current working directory.
- **Code:** `Config(config_path=...)` and UI state use `CONFIG_PATH_DEFAULT` (see `cspm/ui/state.py`). The UI reports the config path on the status/setup views.
