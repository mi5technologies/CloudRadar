"""CIS benchmark control definitions (simplified mapping)."""
from typing import Any

# Map rule_id / category to CIS control IDs
CIS_MAP = {
    "s3_public_block": "1.20",
    "s3_encryption": "1.21",
    "iam_admin_policy": "1.16",
    "iam_wildcard_action": "1.22",
    "security_group_open_world": "4.1",
    "rds_public": "4.3",
    "rds_encryption": "4.4",
    "waf_required": "4.5",
}


def get_cis_checks() -> list[dict[str, Any]]:
    return [
        {"id": "1.20", "title": "S3 block public access", "category": "STORAGE"},
        {"id": "1.21", "title": "S3 bucket encryption", "category": "STORAGE"},
        {"id": "1.16", "title": "IAM no root/admin", "category": "IDENTITY"},
        {"id": "4.1", "title": "Security group restrict SSH/RDP", "category": "NETWORK"},
        {"id": "4.3", "title": "RDS not public", "category": "DATABASE"},
        {"id": "4.4", "title": "RDS encryption", "category": "DATABASE"},
        {"id": "4.5", "title": "WAF on public endpoints", "category": "WAF"},
    ]
