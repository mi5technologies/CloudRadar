"""HIPAA compliance control definitions."""
from typing import Any

HIPAA_CONTROLS = {
    "164.312(a)(1)": "Access Control",
    "164.312(a)(2)(iv)": "Encryption and Decryption",
    "164.312(b)": "Audit Controls",
    "164.312(c)(1)": "Integrity",
    "164.312(e)(2)(i)": "Transmission Security",
}

HIPAA_MAP: dict[str, str] = {
    "s3_encryption": "164.312(a)(2)(iv)",
    "rds_encryption": "164.312(a)(2)(iv)",
    "ebs_volume_not_encrypted": "164.312(a)(2)(iv)",
    "dynamodb_not_encrypted": "164.312(a)(2)(iv)",
    "cloudtrail_logging_disabled": "164.312(b)",
    "cloudtrail_log_validation_disabled": "164.312(b)",
    "cloudwatch_alarm": "164.312(b)",
    "iam_admin_policy": "164.312(a)(1)",
    "iam_wildcard_action": "164.312(a)(1)",
    "security_group_open_world": "164.312(e)(2)(i)",
    "vpc_flow_logs_disabled": "164.312(b)",
    "guardduty_not_enabled": "164.312(b)",
    "secretsmanager_rotation_disabled": "164.312(a)(2)(iv)",
    "kms_rotation_disabled": "164.312(a)(2)(iv)",
}


def get_hipaa_checks() -> list[dict[str, Any]]:
    """Return list of unique HIPAA controls referenced by the rule map."""
    seen: set[str] = set()
    checks: list[dict[str, Any]] = []
    for control_id in HIPAA_MAP.values():
        if control_id not in seen:
            seen.add(control_id)
            checks.append({
                "id": control_id,
                "title": HIPAA_CONTROLS.get(control_id, control_id),
                "category": "HIPAA",
            })
    return checks
