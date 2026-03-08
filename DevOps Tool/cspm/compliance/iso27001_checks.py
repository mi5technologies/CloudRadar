"""ISO/IEC 27001:2022 compliance control mapping."""
from typing import Any

# ISO 27001:2022 Annex A controls relevant to cloud security
# Format: rule_id -> ISO control ID
ISO27001_MAP: dict[str, str] = {
    # A.5 – Organisational controls
    "iam_admin_policy":                    "A.5.15",   # Access control
    "iam_wildcard_action":                 "A.5.15",   # Access control
    "kms_rotation_disabled":               "A.5.33",   # Protection of records (encryption key lifecycle)
    "secretsmanager_rotation_disabled":    "A.5.33",
    "secretsmanager_not_rotated_90d":      "A.5.33",

    # A.6 – People controls (credentials exposure)
    "lambda_env_secrets":                  "A.6.3",    # Information security awareness

    # A.8 – Technological controls
    "s3_public_block":                     "A.8.3",    # Information access restriction
    "s3_encryption":                       "A.8.24",   # Use of cryptography
    "rds_encryption":                      "A.8.24",
    "rds_public":                          "A.8.3",
    "ebs_volume_not_encrypted":            "A.8.24",
    "dynamodb_not_encrypted":              "A.8.24",
    "dynamodb_pitr_disabled":              "A.8.13",   # Information backup

    "security_group_open_world":           "A.8.20",   # Networks security
    "vpc_flow_logs_disabled":              "A.8.16",   # Monitoring activities
    "vpc_default_in_use":                  "A.8.20",

    "cloudtrail_logging_disabled":         "A.8.15",   # Logging
    "cloudtrail_not_multi_region":         "A.8.15",
    "cloudtrail_log_validation_disabled":  "A.8.15",
    "cloudtrail_no_cloudwatch":            "A.8.16",   # Monitoring

    "guardduty_not_enabled":               "A.8.16",   # Monitoring / intrusion detection
    "cloudwatch_alarm":                    "A.8.16",

    "eks_public_api_endpoint":             "A.8.20",   # Networks security
    "eks_logging_disabled":                "A.8.15",
    "eks_secrets_not_encrypted":           "A.8.24",

    "ecs_privileged_container":            "A.8.9",    # Configuration management
    "ecs_root_user":                       "A.8.9",
    "ecs_no_logging":                      "A.8.15",

    "apigw_no_waf":                        "A.8.22",   # Web filtering / application security
    "waf_required":                        "A.8.22",

    "sqs_not_encrypted":                   "A.8.24",
    "sqs_public_policy":                   "A.8.3",

    "sns_not_encrypted":                   "A.8.24",
    "sns_public_policy":                   "A.8.3",

    "ec2_public":                          "A.8.20",
    "lambda_timeout":                      "A.8.6",    # Capacity management (availability)
}

# Human-readable ISO 27001:2022 Annex A control titles
ISO27001_CONTROLS: dict[str, str] = {
    "A.5.15": "Access control",
    "A.5.33": "Protection of records",
    "A.6.3":  "Information security awareness, education and training",
    "A.8.3":  "Information access restriction",
    "A.8.6":  "Capacity management",
    "A.8.9":  "Configuration management",
    "A.8.13": "Information backup",
    "A.8.15": "Logging",
    "A.8.16": "Monitoring activities",
    "A.8.20": "Networks security",
    "A.8.22": "Web filtering",
    "A.8.24": "Use of cryptography",
}


def get_iso27001_checks() -> list[dict[str, Any]]:
    """Return a deduplicated list of ISO 27001:2022 controls used in the mapping."""
    seen: set[str] = set()
    checks: list[dict[str, Any]] = []
    for ctrl_id, title in ISO27001_CONTROLS.items():
        if ctrl_id not in seen:
            seen.add(ctrl_id)
            checks.append({"id": ctrl_id, "title": title, "category": "ISO27001"})
    return checks
