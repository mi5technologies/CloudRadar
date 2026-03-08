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

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
