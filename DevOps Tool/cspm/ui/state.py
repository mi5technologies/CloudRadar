"""UI state: credentials and downloadable outputs.

This UI is intended for single-user/self-hosted usage. Credentials can be
persisted to `config.yaml` if the user opts in.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Optional
import os
import time
import uuid

import yaml


CONFIG_PATH_DEFAULT = Path("config.yaml")


@dataclass
class AWSAuth:
    mode: str = "none"  # none|keys|profile
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    profile_name: Optional[str] = None
    region: str = "us-east-1"
    organization_role_arn: Optional[str] = None  # arn:aws:iam::{account_id}:role/CloudRadarScanner
    role_assumption_template: Optional[str] = None  # alternative to organization_role_arn
    updated_at: float = 0.0

    def masked(self) -> dict[str, Any]:
        def mask(v: Optional[str]) -> Optional[str]:
            if not v:
                return None
            if len(v) <= 6:
                return "***"
            return v[:3] + "***" + v[-3:]

        return {
            "mode": self.mode,
            "access_key_id": mask(self.access_key_id),
            "secret_access_key": "***" if self.secret_access_key else None,
            "session_token": "***" if self.session_token else None,
            "profile_name": self.profile_name,
            "region": self.region,
            "organization_role_arn": self.organization_role_arn,
            "role_assumption_template": self.role_assumption_template,
            "updated_at": self.updated_at,
        }


@dataclass
class GCPAuth:
    mode: str = "none"  # none | project | credentials
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None  # path to service account JSON
    organization_id: Optional[str] = None  # list projects under org
    folder_id: Optional[str] = None  # list projects under folder
    updated_at: float = 0.0

    def masked(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "project_id": self.project_id,
            "credentials_path": "***" if self.credentials_path else None,
            "organization_id": self.organization_id,
            "folder_id": self.folder_id,
            "updated_at": self.updated_at,
        }


@dataclass
class AzureAuth:
    mode: str = "none"  # none | sp (service principal)
    subscription_id: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    management_group_id: Optional[str] = None  # list subscriptions under mgmt group
    subscription_ids: list[str] | None = None  # explicit list of subscription IDs
    updated_at: float = 0.0

    def masked(self) -> dict[str, Any]:
        def mask(v: Optional[str]) -> Optional[str]:
            if not v:
                return None
            if len(v) <= 6:
                return "***"
            return v[:3] + "***" + v[-3:]

        return {
            "mode": self.mode,
            "subscription_id": mask(self.subscription_id),
            "tenant_id": mask(self.tenant_id),
            "client_id": mask(self.client_id),
            "client_secret": "***" if self.client_secret else None,
            "management_group_id": self.management_group_id,
            "subscription_ids": self.subscription_ids,
            "updated_at": self.updated_at,
        }


class OutputStore:
    """In-memory store of generated outputs (JSON/HTML/CSV) for download."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._store: dict[str, dict[str, Any]] = {}

    def put(self, content: str, media_type: str, filename: str) -> str:
        token = uuid.uuid4().hex
        with self._lock:
            self._store[token] = {
                "content": content,
                "media_type": media_type,
                "filename": filename,
                "created_at": time.time(),
            }
        return token

    def get(self, token: str) -> Optional[dict[str, Any]]:
        with self._lock:
            return self._store.get(token)


class AppState:
    def __init__(self) -> None:
        self._lock = RLock()
        self.aws = AWSAuth()
        self.gcp = GCPAuth()
        self.azure = AzureAuth()
        self.outputs = OutputStore()
        self.notifications: dict[str, Any] = {}

    def load_from_config(self, path: Path = CONFIG_PATH_DEFAULT) -> None:
        if not path.exists():
            return
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            return
        aws = data.get("aws") or {}
        with self._lock:
            if aws.get("access_key_id") and aws.get("secret_access_key"):
                self.aws.mode = "keys"
                self.aws.access_key_id = str(aws.get("access_key_id"))
                self.aws.secret_access_key = str(aws.get("secret_access_key"))
                self.aws.session_token = aws.get("session_token") or None
                self.aws.profile_name = None
            elif aws.get("profile_name"):
                self.aws.mode = "profile"
                self.aws.profile_name = str(aws.get("profile_name"))
                self.aws.access_key_id = None
                self.aws.secret_access_key = None
                self.aws.session_token = None
            if aws.get("region"):
                self.aws.region = str(aws.get("region"))
            self.aws.organization_role_arn = (aws.get("organization_role_arn") or "").strip() or None
            self.aws.role_assumption_template = (aws.get("role_assumption_template") or "").strip() or None
            self.aws.updated_at = time.time()

        gcp = data.get("gcp") or {}
        with self._lock:
            if gcp.get("project_id") or gcp.get("organization_id") or gcp.get("folder_id"):
                self.gcp.mode = "credentials" if gcp.get("credentials_path") else "project"
                self.gcp.project_id = str(gcp.get("project_id", "") or "")
                self.gcp.credentials_path = gcp.get("credentials_path") or None
                self.gcp.organization_id = (gcp.get("organization_id") or "").strip() or None
                self.gcp.folder_id = (gcp.get("folder_id") or "").strip() or None
                self.gcp.updated_at = time.time()

        azure = data.get("azure") or {}
        with self._lock:
            has_azure = (
                (azure.get("subscription_id") or azure.get("management_group_id") or azure.get("subscription_ids"))
                and azure.get("client_id")
                and azure.get("client_secret")
            )
            if has_azure:
                self.azure.mode = "sp"
                self.azure.subscription_id = str(azure.get("subscription_id", "") or "")
                self.azure.tenant_id = str(azure.get("tenant_id", "")) or None
                self.azure.client_id = str(azure.get("client_id"))
                self.azure.client_secret = str(azure.get("client_secret"))
                self.azure.management_group_id = (azure.get("management_group_id") or "").strip() or None
                sub_ids = azure.get("subscription_ids")
                self.azure.subscription_ids = [str(x).strip() for x in sub_ids] if isinstance(sub_ids, list) else None
                self.azure.updated_at = time.time()

        notifications = data.get("notifications") or {}
        with self._lock:
            if notifications:
                self.notifications = dict(notifications)

        self.apply_env()

    def persist_to_config(self, path: Path = CONFIG_PATH_DEFAULT) -> None:
        """Persist current auth into config.yaml (plain text)."""
        with self._lock:
            aws = self.aws
            current = {}
            if path.exists():
                try:
                    current = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                except Exception:
                    current = {}
            current.setdefault("aws", {})
            if aws.mode == "keys":
                current["aws"].update(
                    {
                        "access_key_id": aws.access_key_id,
                        "secret_access_key": aws.secret_access_key,
                        "session_token": aws.session_token,
                        "profile_name": None,
                        "region": aws.region,
                    }
                )
            elif aws.mode == "profile":
                current["aws"].update(
                    {
                        "access_key_id": None,
                        "secret_access_key": None,
                        "session_token": None,
                        "profile_name": aws.profile_name,
                        "region": aws.region,
                    }
                )
            else:
                current["aws"].update(
                    {
                        "access_key_id": None,
                        "secret_access_key": None,
                        "session_token": None,
                        "profile_name": None,
                        "region": aws.region,
                    }
                )
            current["aws"]["organization_role_arn"] = aws.organization_role_arn
            current["aws"]["role_assumption_template"] = aws.role_assumption_template
            current.setdefault("gcp", {})
            current["gcp"].update({
                "project_id": self.gcp.project_id,
                "credentials_path": self.gcp.credentials_path,
                "organization_id": self.gcp.organization_id,
                "folder_id": self.gcp.folder_id,
            })
            current.setdefault("azure", {})
            current["azure"].update({
                "subscription_id": self.azure.subscription_id,
                "tenant_id": self.azure.tenant_id,
                "client_id": self.azure.client_id,
                "client_secret": self.azure.client_secret,
                "management_group_id": self.azure.management_group_id,
                "subscription_ids": self.azure.subscription_ids,
            })
            if self.notifications:
                current["notifications"] = dict(self.notifications)
            path.write_text(yaml.safe_dump(current, sort_keys=False), encoding="utf-8")

    def set_notifications(self, config: dict[str, Any], persist: bool = True) -> None:
        """Update notification configuration and optionally persist to config.yaml."""
        with self._lock:
            self.notifications = dict(config)
        if persist:
            self.persist_to_config(CONFIG_PATH_DEFAULT)

    def get_notifications_masked(self) -> dict[str, Any]:
        """Return notification config with secrets masked."""
        with self._lock:
            cfg = dict(self.notifications)
        masked_keys = {"slack_webhook_url", "smtp_password"}
        result: dict[str, Any] = {}
        for k, v in cfg.items():
            if k in masked_keys and v:
                result[k] = "***"
            else:
                result[k] = v
        return result

    def set_gcp(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        organization_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        persist: bool = True,
    ) -> None:
        with self._lock:
            self.gcp.mode = "credentials" if credentials_path else "project"
            self.gcp.project_id = (project_id or "").strip() or None
            self.gcp.credentials_path = (credentials_path or "").strip() or None
            if organization_id is not None:
                self.gcp.organization_id = (organization_id or "").strip() or None
            if folder_id is not None:
                self.gcp.folder_id = (folder_id or "").strip() or None
            self.gcp.updated_at = time.time()
        self._apply_gcp_env()
        if persist:
            self._persist_gcp_azure(CONFIG_PATH_DEFAULT)

    def set_azure(
        self,
        subscription_id: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        management_group_id: Optional[str] = None,
        subscription_ids: Optional[list[str]] = None,
        persist: bool = True,
    ) -> None:
        with self._lock:
            self.azure.mode = "sp"
            self.azure.subscription_id = (subscription_id or "").strip() or None
            self.azure.tenant_id = (tenant_id or "").strip() or None
            self.azure.client_id = (client_id or "").strip() or None
            self.azure.client_secret = (client_secret or "").strip() or None
            if management_group_id is not None:
                self.azure.management_group_id = (management_group_id or "").strip() or None
            if subscription_ids is not None:
                self.azure.subscription_ids = [str(x).strip() for x in subscription_ids if str(x).strip()]
            self.azure.updated_at = time.time()
        self._apply_azure_env()
        if persist:
            self._persist_gcp_azure(CONFIG_PATH_DEFAULT)

    def _persist_gcp_azure(self, path: Path) -> None:
        current = {}
        if path.exists():
            try:
                current = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                current = {}
        current.setdefault("gcp", {})
        current["gcp"].update({
            "project_id": self.gcp.project_id,
            "credentials_path": self.gcp.credentials_path,
        })
        current.setdefault("azure", {})
        current["azure"].update({
            "subscription_id": self.azure.subscription_id,
            "tenant_id": self.azure.tenant_id,
            "client_id": self.azure.client_id,
            "client_secret": self.azure.client_secret,
        })
        path.write_text(yaml.safe_dump(current, sort_keys=False), encoding="utf-8")

    def _apply_gcp_env(self) -> None:
        os.environ["GOOGLE_CLOUD_PROJECT"] = self.gcp.project_id or ""
        if self.gcp.credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.gcp.credentials_path
        else:
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

    def _apply_azure_env(self) -> None:
        for key in ("AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"):
            os.environ.pop(key, None)
        if self.azure.mode == "sp" and self.azure.subscription_id:
            os.environ["AZURE_SUBSCRIPTION_ID"] = self.azure.subscription_id or ""
            os.environ["AZURE_TENANT_ID"] = self.azure.tenant_id or ""
            os.environ["AZURE_CLIENT_ID"] = self.azure.client_id or ""
            os.environ["AZURE_CLIENT_SECRET"] = self.azure.client_secret or ""

    def set_aws_keys(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_token: Optional[str],
        region: str,
        organization_role_arn: Optional[str] = None,
        role_assumption_template: Optional[str] = None,
    ) -> None:
        with self._lock:
            self.aws.mode = "keys"
            self.aws.access_key_id = access_key_id.strip()
            self.aws.secret_access_key = secret_access_key.strip()
            self.aws.session_token = (session_token or "").strip() or None
            self.aws.profile_name = None
            self.aws.region = region.strip() or "us-east-1"
            if organization_role_arn is not None:
                self.aws.organization_role_arn = (organization_role_arn or "").strip() or None
            if role_assumption_template is not None:
                self.aws.role_assumption_template = (role_assumption_template or "").strip() or None
            self.aws.updated_at = time.time()
        self.apply_env()

    def set_aws_profile(self, profile_name: str, region: str) -> None:
        with self._lock:
            self.aws.mode = "profile"
            self.aws.profile_name = profile_name.strip()
            self.aws.access_key_id = None
            self.aws.secret_access_key = None
            self.aws.session_token = None
            self.aws.region = region.strip() or "us-east-1"
            self.aws.updated_at = time.time()
        self.apply_env()

    def clear_aws(self) -> None:
        with self._lock:
            self.aws = AWSAuth(region=self.aws.region)
        self.apply_env(clear=True)

    def apply_env(self, clear: bool = False) -> None:
        """Apply auth to environment for boto3 and cloud SDKs."""
        keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"]
        if clear:
            for k in keys:
                os.environ.pop(k, None)
            if self.aws.region:
                os.environ["AWS_DEFAULT_REGION"] = self.aws.region
            return

        aws = self.aws
        os.environ["AWS_DEFAULT_REGION"] = aws.region or "us-east-1"
        if aws.mode == "keys":
            os.environ.pop("AWS_PROFILE", None)
            os.environ["AWS_ACCESS_KEY_ID"] = aws.access_key_id or ""
            os.environ["AWS_SECRET_ACCESS_KEY"] = aws.secret_access_key or ""
            if aws.session_token:
                os.environ["AWS_SESSION_TOKEN"] = aws.session_token
            else:
                os.environ.pop("AWS_SESSION_TOKEN", None)
        elif aws.mode == "profile":
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            os.environ.pop("AWS_SESSION_TOKEN", None)
            if aws.profile_name:
                os.environ["AWS_PROFILE"] = aws.profile_name
        else:
            for k in keys:
                os.environ.pop(k, None)
        self._apply_gcp_env()
        self._apply_azure_env()


app_state = AppState()

