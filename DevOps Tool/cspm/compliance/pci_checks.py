"""PCI-DSS compliance control definitions."""
from typing import Any

PCI_CONTROLS = {
    "PCI.1.2": "Restrict connections between untrusted networks",
    "PCI.3.4": "Render PAN unreadable anywhere it is stored",
    "PCI.3.6": "Key management procedures for cryptographic keys",
    "PCI.6.6": "Address new threats and vulnerabilities via WAF",
    "PCI.7.1": "Limit access to system components to only those individuals whose job requires such access",
    "PCI.8.6": "Manage use of interactive logins and authentication",
    "PCI.10.1": "Implement audit trails to link all access to system components",
    "PCI.10.2": "Implement automated audit trails for all system components",
    "PCI.10.5": "Secure audit trails from modification",
    "PCI.10.6": "Review logs for all system components at least daily",
    "PCI.11.4": "Use intrusion-detection and/or intrusion-prevention techniques",
}

PCI_MAP: dict[str, str] = {
    "s3_public_block": "PCI.7.1",
    "s3_encryption": "PCI.3.4",
    "rds_encryption": "PCI.3.4",
    "ebs_volume_not_encrypted": "PCI.3.4",
    "dynamodb_not_encrypted": "PCI.3.4",
    "iam_admin_policy": "PCI.7.1",
    "iam_wildcard_action": "PCI.7.1",
    "security_group_open_world": "PCI.1.2",
    "vpc_flow_logs_disabled": "PCI.10.2",
    "cloudtrail_logging_disabled": "PCI.10.1",
    "cloudtrail_log_validation_disabled": "PCI.10.5",
    "waf_required": "PCI.6.6",
    "apigw_no_waf": "PCI.6.6",
    "guardduty_not_enabled": "PCI.11.4",
    "kms_rotation_disabled": "PCI.3.6",
    "secretsmanager_rotation_disabled": "PCI.8.6",
    "cloudwatch_alarm": "PCI.10.6",
}


def get_pci_checks() -> list[dict[str, Any]]:
    """Return list of unique PCI-DSS controls referenced by the rule map."""
    seen: set[str] = set()
    checks: list[dict[str, Any]] = []
    for control_id in PCI_MAP.values():
        if control_id not in seen:
            seen.add(control_id)
            checks.append({
                "id": control_id,
                "title": PCI_CONTROLS.get(control_id, control_id),
                "category": "PCI-DSS",
            })
    return checks
