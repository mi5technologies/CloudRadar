"""Azure provider: real discovery for VMs, Storage Accounts, and NSGs."""
from typing import Any, Callable, Optional

from cspm.providers.base_provider import BaseProvider


def _list_subscriptions_under_management_group(group_id: str, credential) -> list[str]:
    """List subscription IDs under a management group."""
    try:
        from azure.mgmt.managementgroups import ManagementGroupsAPI
        client = ManagementGroupsAPI(credential=credential)
        subs = []
        for s in client.management_group_subscriptions.get_subscriptions_under_management_group(group_id):
            sub_id = getattr(s, "subscription_id", None) or getattr(s, "id", None)
            if not sub_id and getattr(s, "name", None):
                # name may be /providers/.../subscriptions/{id}
                parts = s.name.split("/")
                if "subscriptions" in parts:
                    idx = parts.index("subscriptions")
                    if idx + 1 < len(parts):
                        sub_id = parts[idx + 1]
            if sub_id:
                subs.append(str(sub_id))
        return subs
    except Exception:
        return []


class AzureProvider(BaseProvider):
    def __init__(
        self,
        subscription_id: str | None = None,
        management_group_id: str | None = None,
        subscription_ids: list[str] | None = None,
    ):
        self.subscription_id = (subscription_id or "").strip() or None
        self.management_group_id = (management_group_id or "").strip() or None
        self.subscription_ids = subscription_ids or []

    def _is_multi_subscription(self) -> bool:
        return bool(self.management_group_id or self.subscription_ids)

    def _get_subscription_ids(self) -> list[str]:
        """Return list of subscription IDs to scan."""
        if self.subscription_ids:
            return self.subscription_ids
        if self.management_group_id:
            cred = self._get_credential()
            if cred:
                return _list_subscriptions_under_management_group(self.management_group_id, cred)
        return [self.subscription_id] if self.subscription_id else []

    def authenticate(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            DefaultAzureCredential().get_token("https://management.azure.com/.default")
            return True
        except Exception:
            return False

    def get_account_id(self) -> str:
        return self.subscription_id or "unknown"

    def get_regions(self) -> list[str]:
        return ["eastus", "westus2"]

    def discover_assets(
        self,
        asset_types: list[str] | None = None,
        on_progress: Optional[Callable[[str, str, Optional[str]], None]] = None,
    ) -> dict[str, list[dict[str, Any]]]:
        def report(step: str, status: str = "running", detail: str | None = None):
            if on_progress:
                on_progress(step, status, detail)

        if self._is_multi_subscription():
            return self._discover_multi_subscription(asset_types, on_progress)

        return self._discover_single_subscription(asset_types, on_progress)

    def _discover_multi_subscription(
        self, asset_types: list[str] | None, on_progress: Optional[Callable[[str, str, Optional[str]], None]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Discover assets across all subscriptions."""
        sub_ids = self._get_subscription_ids()
        if not sub_ids:
            if on_progress:
                on_progress("No subscriptions found", "error", None)
            return {}

        merged: dict[str, list[dict[str, Any]]] = {}
        cred = self._get_credential()
        if not cred:
            return {}
        orig_sub = self.subscription_id
        try:
            for sub_id in sub_ids:
                self.subscription_id = sub_id
                raw = self._discover_single_subscription(asset_types, on_progress)
                for rtype, items in raw.items():
                    for item in items:
                        item["account_id"] = sub_id
                        item["subscription_id"] = sub_id
                    merged.setdefault(rtype, []).extend(items)
        finally:
            self.subscription_id = orig_sub
        return merged

    def _discover_single_subscription(
        self, asset_types: list[str] | None, on_progress: Optional[Callable[[str, str, Optional[str]], None]]
    ) -> dict[str, list[dict[str, Any]]]:
        def report(step: str, status: str = "running", detail: str | None = None):
            if on_progress:
                on_progress(step, status, detail)

        all_types = {"azure_vm", "azure_storage", "azure_nsg", "azure_functions"}
        types = set(asset_types) if asset_types else all_types
        result: dict[str, list[dict[str, Any]]] = {}

        credential = self._get_credential()
        sub = self.subscription_id or ""

        if "azure_vm" in types:
            report("Discovering Azure VMs", "running")
            result["azure_vm"] = self._discover_vms(credential, sub)
            report("Discovering Azure VMs", "success")

        if "azure_storage" in types:
            report("Discovering Azure Storage Accounts", "running")
            result["azure_storage"] = self._discover_storage(credential, sub)
            report("Discovering Azure Storage Accounts", "success")

        if "azure_nsg" in types:
            report("Discovering Azure NSGs", "running")
            result["azure_nsg"] = self._discover_nsgs(credential, sub)
            report("Discovering Azure NSGs", "success")

        if "azure_functions" in types:
            report("Discovering Azure Function Apps", "running")
            result["azure_functions"] = self._discover_azure_functions(credential, sub)
            report("Discovering Azure Function Apps", "success")

        return result

    def _get_credential(self) -> Any:
        try:
            from azure.identity import DefaultAzureCredential
            return DefaultAzureCredential()
        except Exception:
            return None

    def _discover_vms(self, credential, subscription_id: str) -> list[dict[str, Any]]:
        try:
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.network import NetworkManagementClient
            compute_client = ComputeManagementClient(credential, subscription_id)
            network_client = NetworkManagementClient(credential, subscription_id)
            result = []
            for vm in compute_client.virtual_machines.list_all():
                has_public_ip = False
                try:
                    for nic_ref in (vm.network_profile.network_interfaces or []):
                        nic_id = nic_ref.id or ""
                        parts = nic_id.split("/")
                        rg_idx = next((i for i, p in enumerate(parts) if p.lower() == "resourcegroups"), None)
                        nic_idx = next((i for i, p in enumerate(parts) if p.lower() == "networkinterfaces"), None)
                        if rg_idx and nic_idx:
                            rg = parts[rg_idx + 1]
                            nic_name = parts[nic_idx + 1]
                            nic = network_client.network_interfaces.get(rg, nic_name)
                            for ip_config in (nic.ip_configurations or []):
                                if ip_config.public_ip_address:
                                    has_public_ip = True
                                    break
                        if has_public_ip:
                            break
                except Exception:
                    pass

                rg_name = ""
                if vm.id:
                    vm_parts = vm.id.split("/")
                    rg_idx_vm = next((i for i, p in enumerate(vm_parts) if p.lower() == "resourcegroups"), None)
                    if rg_idx_vm is not None:
                        rg_name = vm_parts[rg_idx_vm + 1]

                result.append({
                    "id": vm.id or vm.name,
                    "name": vm.name,
                    "type": "azure_vm",
                    "region": vm.location or "unknown",
                    "resource_group": rg_name,
                    "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else None,
                    "has_public_ip": has_public_ip,
                })
            return result
        except Exception:
            return []

    def _discover_storage(self, credential, subscription_id: str) -> list[dict[str, Any]]:
        try:
            from azure.mgmt.storage import StorageManagementClient
            client = StorageManagementClient(credential, subscription_id)
            result = []
            for acct in client.storage_accounts.list():
                allow_blob_public = bool(
                    acct.allow_blob_public_access
                    if acct.allow_blob_public_access is not None
                    else True
                )
                https_only = bool(
                    acct.enable_https_traffic_only
                    if acct.enable_https_traffic_only is not None
                    else False
                )
                result.append({
                    "id": acct.id or acct.name,
                    "name": acct.name,
                    "type": "azure_storage",
                    "region": acct.location or "unknown",
                    "sku": acct.sku.name if acct.sku else None,
                    "allow_blob_public_access": allow_blob_public,
                    "https_only": https_only,
                })
            return result
        except Exception:
            return []

    def _discover_nsgs(self, credential, subscription_id: str) -> list[dict[str, Any]]:
        try:
            from azure.mgmt.network import NetworkManagementClient
            client = NetworkManagementClient(credential, subscription_id)
            result = []
            for nsg in client.network_security_groups.list_all():
                has_open_inbound = False
                for rule in (nsg.security_rules or []):
                    if (
                        rule.direction == "Inbound"
                        and rule.access == "Allow"
                        and rule.source_address_prefix in ("*", "Any", "Internet", "0.0.0.0/0")
                        and rule.destination_port_range in ("*", "Any")
                    ):
                        has_open_inbound = True
                        break

                result.append({
                    "id": nsg.id or nsg.name,
                    "name": nsg.name,
                    "type": "azure_nsg",
                    "region": nsg.location or "unknown",
                    "has_open_inbound": has_open_inbound,
                })
            return result
        except Exception:
            return []

    def _discover_azure_functions(self, credential, subscription_id: str) -> list[dict[str, Any]]:
        try:
            from azure.mgmt.web import WebSiteManagementClient
            client = WebSiteManagementClient(credential, subscription_id)
            result = []
            for app in client.web_apps.list():
                kind = (app.kind or "").lower()
                if "function" not in kind:
                    continue
                public_access = getattr(app, "public_network_access", "Enabled") or "Enabled"
                identity = getattr(app, "identity", None)
                managed_identity = identity and getattr(identity, "type", None) and "SystemAssigned" in str(identity.type)
                site_config = getattr(app, "site_config", None)
                app_settings = getattr(site_config, "app_settings", None) if site_config else None
                keys = []
                if isinstance(app_settings, list):
                    keys = [getattr(s, "name", s.get("name", "") or "").lower() for s in app_settings]
                elif isinstance(app_settings, dict):
                    keys = [k.lower() for k in app_settings]
                secret_like = any(
                    k for k in keys
                    if "secret" in k or "key" in k or "password" in k or "connection" in k
                )
                result.append({
                    "id": app.id or app.name,
                    "name": app.name,
                    "type": "azure_functions",
                    "region": app.location or "unknown",
                    "subscription_id": subscription_id,
                    "public_network_access": public_access,
                    "managed_identity": bool(managed_identity),
                    "app_settings_keys": keys,
                    "secret_like_settings": secret_like,
                })
            return result
        except Exception:
            return []
