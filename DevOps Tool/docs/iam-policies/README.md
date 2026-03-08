# IAM / RBAC policy files for multi-account scanning

Use these JSON files to create roles and policies for CloudRadar multi-account setup.

## AWS

| File | Use when |
|------|----------|
| **aws-management-account-policy.json** | Attach to the IAM user or role in the **management account** that runs CloudRadar. Allows listing org accounts and assuming the scanner role in each member. No placeholders. |
| **aws-member-account-trust-policy.json** | Use as the **trust policy** for the role `CloudRadarScanner` in **each member account**. Replace `MANAGEMENT_ACCOUNT_ID` with your 12-digit management account ID. Optionally restrict `Principal.AWS` to a specific role/user ARN instead of root. |
| **aws-member-account-scanner-policy.json** | Attach as a **permissions policy** to the role `CloudRadarScanner` in each member account. Read-only actions required for CloudRadar discovery and scanning. No placeholders. |

## GCP

| File | Use when |
|------|----------|
| **gcp-required-roles.json** | Reference for which roles (and optional custom role actions) to grant to the service account at org/folder and at each project. |

## Azure

| File | Use when |
|------|----------|
| **azure-custom-role-definition.json** | Use to create a custom RBAC role (e.g. via `New-AzRoleDefinition` or ARM) and assign it to the service principal at management group or subscription scope. Replace `SUBSCRIPTION_ID` or scope as needed. |
