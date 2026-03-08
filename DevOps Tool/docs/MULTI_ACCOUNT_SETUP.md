# Multi-Account and Multi-Cloud Setup Guide

This guide explains how CloudRadar handles **multi-account** scanning (one cloud, many accounts/projects/subscriptions) and **multi-cloud** setup (AWS, GCP, and Azure in the same deployment). You can scan a single account per cloud or an entire organization per cloud, and run scans across all three clouds in parallel.

---

## Multi-cloud vs multi-account

| Term | Meaning |
|------|--------|
| **Multi-cloud** | Using more than one cloud provider (AWS, GCP, Azure). CloudRadar supports all three; you configure credentials for each in **Setup** and can run a **single-cloud scan** (one cloud at a time) or a **parallel multi-cloud scan** (all configured clouds at once) from the Security Scan page. |
| **Multi-account** | Within one cloud, scanning **multiple accounts** (AWS), **multiple projects** (GCP), or **multiple subscriptions** (Azure). You configure org/folder/management-group or role-assumption settings; one scan then discovers and scans every account/project/subscription and merges results with `account_id` / `project_id` / `subscription_id` on findings and assets. |

You can combine both: e.g. multi-account AWS + multi-project GCP + multi-subscription Azure, and run a parallel scan that runs all of them.

---

## Multi-cloud setup (AWS + GCP + Azure)

### 1. Configure each cloud in Setup

- Open **Setup** in the CloudRadar UI.
- Configure **AWS**: access keys or profile, region. Optionally set **Role assumption template** for [multi-account AWS](#aws-multi-account-organizations).
- Configure **GCP**: project ID, optional credentials path. Optionally set **Organization ID** or **Folder ID** for [multi-project GCP](#gcp-multi-project-organization-or-folder).
- Configure **Azure**: subscription ID, tenant ID, client ID, client secret. Optionally set **Management group ID** or **Subscription IDs** for [multi-subscription Azure](#azure-multi-subscription-management-group-or-explicit-list).
- Save each section (with “Save to server config” if you want to persist to `config.yaml`).

### 2. Run scans

- **Single cloud**: On **Security Scan**, leave “Single cloud scan” selected, choose the cloud (AWS, GCP, or Azure), set region/project/subscription if needed, and click **Run scan**.
- **Parallel multi-cloud**: On **Security Scan**, select **“Scan all clouds in parallel”**, select the clouds you want (e.g. all three), then click **Run … cloud scans in parallel**. Each cloud runs in its own job; you see progress per cloud. Results are per-cloud (findings and reports include `cloud` and, when applicable, `account_id` / `project_id` / `subscription_id`).

### 3. Reports and findings

- Security scan results, compliance, and governance reports are **per scan**. For parallel multi-cloud you get one result set per cloud.
- Findings and the asset catalog include **cloud** and, in multi-account mode, **account_id** / **project_id** / **subscription_id** so you can filter by cloud and by account.

---

## How multi-account works (per cloud)

### Single vs multi-account

| Mode | What you configure | What CloudRadar does |
|------|--------------------|----------------------|
| **Single account** | One set of credentials (one AWS account, one GCP project, one Azure subscription) | Uses those credentials to discover and scan that one scope. |
| **Multi-account** | Credentials in the **management/organization root** plus a **role (or scope)** in each member | Lists all accounts/projects/subscriptions, then assumes a role (or switches context) in each and runs the same discovery/scan, merging results with `account_id` / `project_id` / `subscription_id` on every finding and asset. |

### Where the ARN comes from (AWS)

The role ARN template (e.g. `arn:aws:iam::{account_id}:role/CloudRadarScanner`) is **not** something you “get” from AWS. You **define** it:

- **`{account_id}`** – Replaced by CloudRadar with each account ID returned by `organizations:ListAccounts`.
- **Role name** (e.g. `CloudRadarScanner`) – A role **you create in each member account** (and optionally in the management account). Same name in every account makes the template simple.

So the ARN is “from” **every account you scan**: the same role name exists in each of those accounts. The **credentials you put in CloudRadar** are from the **management (root) account** (or a delegated admin account) that is allowed to call `organizations:ListAccounts` and `sts:AssumeRole` into that role in each member.

---

## AWS: Multi-Account (Organizations)

### Overview

1. You run CloudRadar with **management account** credentials (or a role/user that can list org accounts and assume roles).
2. CloudRadar calls `organizations:ListAccounts` to get all active accounts.
3. For each account, it assumes the role `arn:aws:iam::{account_id}:role/CloudRadarScanner` (or the name you chose).
4. With that role’s credentials it runs discovery and scanning in that account, then moves to the next.

### Step-by-step

#### 1. Management account: identity that runs CloudRadar

In the **management account** (or a dedicated “auditor” account), create an IAM **user** or **role** that will be used to run CloudRadar (e.g. access keys or profile). Attach a policy that allows:

- **Organizations** – List accounts.
- **STS** – Assume the scanner role in each member account.

Use the provided policy file:

- **[docs/iam-policies/aws-management-account-policy.json](iam-policies/aws-management-account-policy.json)**

Replace `MANAGEMENT_ACCOUNT_ID` in the policy with your management account ID (12 digits). Attach this policy to the IAM user or role that runs CloudRadar.

#### 2. Each member account (and optionally management): scanner role

In **every account** you want to scan (including the management account if you scan it):

**a) Create an IAM role** (e.g. name: `CloudRadarScanner`).

**b) Set the trust policy** so the management account (or the account that runs CloudRadar) can assume this role. Use:

- **[docs/iam-policies/aws-member-account-trust-policy.json](iam-policies/aws-member-account-trust-policy.json)**

Replace `MANAGEMENT_ACCOUNT_ID` with the 12-digit ID of the account that has the identity used in step 1. The example uses `root` so any IAM user or role in that account can assume the role; for production you can restrict `Principal.AWS` to a specific ARN (e.g. `arn:aws:iam::MANAGEMENT_ACCOUNT_ID:role/CloudRadarAuditor`).

**c) Attach permissions** so the role can perform read-only discovery and scanning. Use:

- **[docs/iam-policies/aws-member-account-scanner-policy.json](iam-policies/aws-member-account-scanner-policy.json)**

This gives the role the least-privilege actions needed for EC2, S3, RDS, Lambda, IAM, WAF, CloudTrail, VPC, EKS, ECS, KMS, API Gateway, SQS, DynamoDB, GuardDuty, CloudWatch, Secrets Manager, SNS, CloudFront, Step Functions, ECR, and related read-only APIs.

#### 3. Configure CloudRadar

- In the UI **Setup → AWS**, enter the **management account** credentials (access key + secret, or profile).
- In **Role assumption template**, enter:  
  `arn:aws:iam::{account_id}:role/CloudRadarScanner`  
  (or the role name you used in step 2).
- Save. When you run an AWS scan, CloudRadar will list org accounts and assume this role in each.

### Permissions summary (AWS)

| Where | Policy / role | Purpose |
|-------|----------------|---------|
| Management account | [aws-management-account-policy.json](iam-policies/aws-management-account-policy.json) | Allow `organizations:ListAccounts` and `sts:AssumeRole` into each member role. |
| Each member account | [aws-member-account-trust-policy.json](iam-policies/aws-member-account-trust-policy.json) | Trust the management account identity to assume the scanner role. |
| Each member account | [aws-member-account-scanner-policy.json](iam-policies/aws-member-account-scanner-policy.json) | Read-only permissions for CloudRadar discovery and scanning. |

---

## GCP: Multi-Project (Organization or Folder)

### Overview

1. You configure a **service account** (or user) with access at the **organization** or **folder** level.
2. CloudRadar uses the Resource Manager API to **list projects** under that org or folder.
3. For each project, it uses the same credentials (with project scope) to run discovery and scanning, and tags results with `project_id`.

### Step-by-step

#### 1. Create a service account (org or folder level)

- In **Google Cloud Console**, use an organization or folder that contains the projects you want to scan.
- Create a **service account** (e.g. `cloudradar-scanner@your-project.iam.gserviceaccount.com`).
- Grant it the roles listed in **[docs/iam-policies/gcp-required-roles.json](iam-policies/gcp-required-roles.json)** (or the equivalent in the Console):
  - **Resource Manager** – List projects under the org/folder.
  - **Per-project roles** – So the same service account can read resources in each project (e.g. Viewer, Security Reviewer, Cloud Asset Viewer, or a custom role that matches the actions in the JSON).

Apply the org/folder-level role at the **organization** or **folder**; apply the project-level roles at **each project** (or use a custom role and grant it on each project).

#### 2. Enable APIs

- Enable **Resource Manager API** (and any other APIs your scan needs, e.g. Compute, Storage, IAM) for the org or the projects you scan.

#### 3. Configure CloudRadar

- In **Setup → GCP**, set **Project ID** to any project where the service account exists (used for auth).
- Set **Organization ID** (numeric, e.g. `123456789012`) to scan all projects under the org, **or** set **Folder ID** to scan all projects under a folder.
- Point **Service account JSON path** to the key file for the service account.
- Save. When you run a GCP scan, CloudRadar will list projects under the org/folder and scan each.

### Permissions summary (GCP)

| Scope | What to grant | Purpose |
|-------|----------------|---------|
| Organization or folder | `resourcemanager.projects.list` (e.g. **Resource Manager → Project Lister** or **Browser**) | List projects. |
| Each project | Roles in [gcp-required-roles.json](iam-policies/gcp-required-roles.json): Viewer, Security Reviewer, Cloud Asset Viewer, Storage Object Viewer, etc. | Read-only discovery and scanning. |

The JSON file lists the **role names** and optional **custom role** actions; use it as a checklist when granting IAM in the Console or via Terraform.

---

## Azure: Multi-Subscription (Management Group or Explicit List)

### Overview

1. You configure a **service principal** (app registration) with access to the **management group** (or to each subscription).
2. CloudRadar uses the **Management Groups API** to **list subscriptions** under that management group (or you provide an explicit list of subscription IDs).
3. For each subscription, it uses the same credentials to run discovery and scanning, and tags results with `subscription_id`.

### Step-by-step

#### 1. App registration and service principal

- In **Azure AD** → **App registrations**, create an app (e.g. `cloudradar-scanner`).
- Create a **client secret** and note **Application (client) ID**, **Directory (tenant) ID**.
- Use this app as a **service principal** and assign it a role at the **management group** that contains the subscriptions you want to scan (e.g. **Reader** at the management group), **or** assign **Reader** (and **Security Reader** if needed) on each subscription.

For least-privilege, you can use a **custom role** instead of **Reader**:

- **[docs/iam-policies/azure-custom-role-definition.json](iam-policies/azure-custom-role-definition.json)**

Replace `YOUR_MANAGEMENT_GROUP_ID` and `YOUR_SUBSCRIPTION_ID` in `AssignableScopes` with your IDs, then create the role (e.g. via `New-AzRoleDefinition` or the Azure portal). Assign this custom role to the service principal at the management group (or on each subscription).

#### 2. Grant access to list subscriptions (management group)

- The service principal needs **Reader** (or equivalent) on the **management group** so it can call `Microsoft.Management/managementGroups/.../subscriptions/read` (list subscriptions under the group).
- If you only use an explicit list of subscription IDs, the principal only needs read access on those subscriptions.

#### 3. Configure CloudRadar

- In **Setup → Azure**, enter **Tenant ID**, **Client ID**, **Client secret**.
- Set **Management group ID** (e.g. `myMgmtGroup`) to scan all subscriptions under that group, **or** set **Subscription IDs** (comma-separated) to scan only those subscriptions.
- **Subscription ID** can be left blank when using management group or subscription list.
- Save. When you run an Azure scan, CloudRadar will list subscriptions (or use your list) and scan each.

### Permissions summary (Azure)

| Scope | What to grant | Purpose |
|-------|----------------|---------|
| Management group | Reader (or custom role from [azure-custom-role-definition.json](iam-policies/azure-custom-role-definition.json)) | List subscriptions and read resources. |
| Or each subscription | Reader + Security Reader (or custom role) | Read-only discovery and scanning. |

---

## Summary Table

| Cloud | Single scope | Multi scope | Config key(s) | Policy / role files |
|-------|--------------|-------------|---------------|----------------------|
| **AWS** | One account (keys/profile) | Organizations: assume role per account | `role_assumption_template` | [aws-management-account-policy.json](iam-policies/aws-management-account-policy.json), [aws-member-account-trust-policy.json](iam-policies/aws-member-account-trust-policy.json), [aws-member-account-scanner-policy.json](iam-policies/aws-member-account-scanner-policy.json) |
| **GCP** | One project | Org or folder: list projects, scan each | `organization_id` or `folder_id` | [gcp-required-roles.json](iam-policies/gcp-required-roles.json) |
| **Azure** | One subscription | Management group or list of subscriptions | `management_group_id` or `subscription_ids` | [azure-custom-role-definition.json](iam-policies/azure-custom-role-definition.json) |

---

## Troubleshooting

- **AWS: “No organization accounts found”** – The identity running CloudRadar needs `organizations:ListAccounts` in the management account and the organization must be enabled.
- **AWS: “Assume role failed”** – Check the trust policy on the role in the member account: it must allow the management account (and the exact IAM user or role ARN) to assume it. Ensure the role name in the template matches the role you created.
- **GCP: “No projects found”** – Ensure the service account has `resourcemanager.projects.list` on the org/folder and the Resource Manager API is enabled.
- **Azure: “No subscriptions found”** – Ensure the service principal has Reader (or equivalent) on the management group so it can list subscriptions, and that the management group ID is correct.

For more on config file and environment variables, see [Configuration](CONFIGURATION.md).
