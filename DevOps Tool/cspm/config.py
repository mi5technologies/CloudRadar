"""Load and validate configuration from env and config files."""
import os
from pathlib import Path
from typing import Any, Optional

import yaml


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Config:
    """CSPM configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.yaml")
        self._data = load_yaml(self.config_path)
        self.snapshots_dir = Path(get_env("CSPM_SNAPSHOTS_DIR", "snapshots"))
        self.rules_dir = Path(get_env("CSPM_RULES_DIR", "cspm/rules"))
        self.db_url = get_env("CSPM_DB_URL", "sqlite:///cspm.db")
        self.aws_region = get_env("AWS_DEFAULT_REGION", "us-east-1")
        self.azure_subscription_id = get_env("AZURE_SUBSCRIPTION_ID")
        self.gcp_project = get_env("GOOGLE_CLOUD_PROJECT")
        # Override from config file when present
        aws_cfg = self._data.get("aws") or {}
        gcp_cfg = self._data.get("gcp") or {}
        azure_cfg = self._data.get("azure") or {}
        if aws_cfg.get("region"):
            self.aws_region = str(aws_cfg["region"])
        if gcp_cfg.get("project_id"):
            self.gcp_project = self.gcp_project or str(gcp_cfg["project_id"])
        if azure_cfg.get("subscription_id"):
            self.azure_subscription_id = self.azure_subscription_id or str(azure_cfg["subscription_id"])

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    # --- Multi-account ---
    @property
    def aws_organization_role_arn(self) -> Optional[str]:
        """ARN of role to assume in each member account (e.g. arn:aws:iam::{account_id}:role/CloudRadarScanner)."""
        aws = self._data.get("aws") or {}
        return (aws.get("organization_role_arn") or "").strip() or None

    @property
    def aws_role_assumption_template(self) -> Optional[str]:
        """Template with {account_id} placeholder (e.g. arn:aws:iam::{account_id}:role/CloudRadarScanner)."""
        aws = self._data.get("aws") or {}
        return (aws.get("role_assumption_template") or "").strip() or None

    @property
    def gcp_organization_id(self) -> Optional[str]:
        """GCP organization ID to list projects under."""
        gcp = self._data.get("gcp") or {}
        return (gcp.get("organization_id") or "").strip() or None

    @property
    def gcp_folder_id(self) -> Optional[str]:
        """GCP folder ID to list projects under (alternative to organization_id)."""
        gcp = self._data.get("gcp") or {}
        return (gcp.get("folder_id") or "").strip() or None

    @property
    def azure_management_group_id(self) -> Optional[str]:
        """Azure management group ID to list subscriptions under."""
        azure = self._data.get("azure") or {}
        return (azure.get("management_group_id") or "").strip() or None

    @property
    def azure_subscription_ids(self) -> list[str]:
        """Explicit list of Azure subscription IDs to scan."""
        azure = self._data.get("azure") or {}
        ids = azure.get("subscription_ids")
        if isinstance(ids, list):
            return [str(x).strip() for x in ids if str(x).strip()]
        return []
