"""GCP provider: real discovery for GCS, GCE, Firewalls, and IAM bindings."""
from typing import Any, Callable, Optional

from cspm.providers.base_provider import BaseProvider


def _list_projects_under_parent(parent: str) -> list[dict]:
    """List projects under organization or folder. parent = organizations/123 or folders/456."""
    try:
        from google.cloud.resourcemanager_v3.services.projects import ProjectsClient
        client = ProjectsClient()
        projects = []
        for p in client.list_projects(parent=parent):
            if p.state == "ACTIVE":
                projects.append({"id": p.project_id, "name": p.display_name or p.project_id})
        return projects
    except Exception:
        return []


class GCPProvider(BaseProvider):
    def __init__(
        self,
        project_id: str | None = None,
        organization_id: str | None = None,
        folder_id: str | None = None,
    ):
        self.project_id = (project_id or "").strip() or None
        self.organization_id = (organization_id or "").strip() or None
        self.folder_id = (folder_id or "").strip() or None

    def _is_multi_project(self) -> bool:
        return bool(self.organization_id or self.folder_id)

    def authenticate(self) -> bool:
        try:
            from google.cloud import resourcemanager
            client = resourcemanager.ProjectServiceClient()
            list(client.list_projects())
            return True
        except Exception:
            return False

    def get_account_id(self) -> str:
        return self.project_id or "unknown"

    def get_project_ids(self) -> list[str]:
        """Return list of project IDs to scan (multi-project or single)."""
        if self._is_multi_project():
            parent = f"organizations/{self.organization_id}" if self.organization_id else f"folders/{self.folder_id}"
            projects = _list_projects_under_parent(parent)
            return [p["id"] for p in projects]
        return [self.project_id] if self.project_id else []

    def get_regions(self) -> list[str]:
        return ["us-central1", "us-east1"]

    def discover_assets(
        self,
        asset_types: list[str] | None = None,
        on_progress: Optional[Callable[[str, str, Optional[str]], None]] = None,
    ) -> dict[str, list[dict[str, Any]]]:
        def report(step: str, status: str = "running", detail: str | None = None):
            if on_progress:
                on_progress(step, status, detail)

        if self._is_multi_project():
            return self._discover_multi_project(asset_types, on_progress)

        return self._discover_single_project(asset_types, on_progress)

    def _discover_multi_project(
        self, asset_types: list[str] | None, on_progress: Optional[Callable[[str, str, Optional[str]], None]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Discover assets across all projects under org or folder."""
        parent = f"organizations/{self.organization_id}" if self.organization_id else f"folders/{self.folder_id}"
        projects = _list_projects_under_parent(parent)
        if not projects:
            if on_progress:
                on_progress("No projects found under org/folder", "error", parent)
            return {}

        merged: dict[str, list[dict[str, Any]]] = {}
        orig_project = self.project_id
        try:
            for proj in projects:
                proj_id = proj["id"]
                self.project_id = proj_id
                raw = self._discover_single_project(asset_types, on_progress)
                for rtype, items in raw.items():
                    for item in items:
                        item["account_id"] = proj_id
                        item["project_id"] = proj_id
                    merged.setdefault(rtype, []).extend(items)
        finally:
            self.project_id = orig_project
        return merged

    def _discover_single_project(
        self, asset_types: list[str] | None, on_progress: Optional[Callable[[str, str, Optional[str]], None]]
    ) -> dict[str, list[dict[str, Any]]]:
        def report(step: str, status: str = "running", detail: str | None = None):
            if on_progress:
                on_progress(step, status, detail)

        all_types = {"gcs_bucket", "gce_instance", "gcp_firewall", "gcp_iam_binding"}
        types = set(asset_types) if asset_types else all_types
        result: dict[str, list[dict[str, Any]]] = {}
        project = self.project_id or ""

        if "gcs_bucket" in types:
            report("Discovering GCS buckets", "running")
            result["gcs_bucket"] = self._discover_gcs()
            report("Discovering GCS buckets", "success")

        if "gce_instance" in types:
            report("Discovering GCE instances", "running")
            result["gce_instance"] = self._discover_gce()
            report("Discovering GCE instances", "success")

        if "gcp_firewall" in types:
            report("Discovering GCP firewalls", "running")
            result["gcp_firewall"] = self._discover_firewalls()
            report("Discovering GCP firewalls", "success")

        if "gcp_iam_binding" in types:
            report("Discovering GCP IAM bindings", "running")
            result["gcp_iam_binding"] = self._discover_iam_bindings()
            report("Discovering GCP IAM bindings", "success")

        return result

    def _discover_gcs(self) -> list[dict[str, Any]]:
        try:
            from google.cloud import storage
            client = storage.Client(project=self.project_id)
            buckets = []
            for bucket in client.list_buckets():
                try:
                    bucket.reload()
                    iam_config = bucket.iam_configuration
                    uniform_access = bool(
                        iam_config.uniform_bucket_level_access_enabled
                        if iam_config else False
                    )
                    public_access_prevention = getattr(
                        iam_config, "public_access_prevention", "inherited"
                    ) if iam_config else "inherited"
                    is_public = public_access_prevention not in ("enforced",)
                    buckets.append({
                        "id": bucket.id or bucket.name,
                        "name": bucket.name,
                        "type": "gcs_bucket",
                        "region": bucket.location or "unknown",
                        "uniform_bucket_access": uniform_access,
                        "public_access_prevention": public_access_prevention,
                        "is_public": is_public,
                    })
                except Exception:
                    buckets.append({
                        "id": bucket.name,
                        "name": bucket.name,
                        "type": "gcs_bucket",
                        "region": "unknown",
                        "uniform_bucket_access": False,
                        "public_access_prevention": "unknown",
                        "is_public": False,
                    })
            return buckets
        except Exception:
            return []

    def _discover_gce(self) -> list[dict[str, Any]]:
        try:
            from google.cloud import compute_v1
            instances_client = compute_v1.InstancesClient()
            zones_client = compute_v1.ZonesClient()
            project = self.project_id or ""
            result = []
            try:
                zones = [z.name for z in zones_client.list(project=project)]
            except Exception:
                zones = []
            for zone in zones:
                try:
                    for instance in instances_client.list(project=project, zone=zone):
                        has_public_ip = False
                        for iface in (instance.network_interfaces or []):
                            for ac in (iface.access_configs or []):
                                if ac.nat_i_p:
                                    has_public_ip = True
                                    break
                        result.append({
                            "id": str(instance.id),
                            "name": instance.name,
                            "type": "gce_instance",
                            "region": zone,
                            "status": instance.status,
                            "has_public_ip": has_public_ip,
                        })
                except Exception:
                    continue
            return result
        except Exception:
            return []

    def _discover_firewalls(self) -> list[dict[str, Any]]:
        try:
            from google.cloud import compute_v1
            client = compute_v1.FirewallsClient()
            project = self.project_id or ""
            result = []
            for fw in client.list(project=project):
                allows_all_ingress = (
                    fw.direction == "INGRESS"
                    and "0.0.0.0/0" in list(fw.source_ranges or [])
                )
                result.append({
                    "id": str(fw.id),
                    "name": fw.name,
                    "type": "gcp_firewall",
                    "region": "global",
                    "direction": fw.direction,
                    "source_ranges": list(fw.source_ranges or []),
                    "allows_all_ingress": allows_all_ingress,
                })
            return result
        except Exception:
            return []

    def _discover_iam_bindings(self) -> list[dict[str, Any]]:
        try:
            from google.cloud import resourcemanager_v3
            client = resourcemanager_v3.ProjectsClient()
            project = self.project_id or ""
            policy = client.get_iam_policy(resource=f"projects/{project}")
            result = []
            for binding in policy.bindings:
                result.append({
                    "id": f"{project}/{binding.role}",
                    "name": binding.role,
                    "type": "gcp_iam_binding",
                    "region": "global",
                    "role": binding.role,
                    "members": list(binding.members),
                    "has_allUsers": "allUsers" in binding.members or "allAuthenticatedUsers" in binding.members,
                })
            return result
        except Exception:
            return []
