"""SOC2 control definitions (simplified mapping)."""
from typing import Any

SOC2_MAP = {
    "s3_public_block": "CC6.1",
    "s3_encryption": "CC6.1",
    "iam_admin_policy": "CC6.1",
    "rds_public": "CC6.1",
    "rds_encryption": "CC6.1",
    "waf_required": "CC6.6",
}


def get_soc2_checks() -> list[dict[str, Any]]:
    return [
        {"id": "CC6.1", "title": "Logical access security", "category": "CC"},
        {"id": "CC6.6", "title": "Protection of network boundaries", "category": "CC"},
    ]
