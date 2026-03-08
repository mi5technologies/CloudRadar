"""Orchestrate scan: discover, enrich, rule engine, risk, snapshot."""
from pathlib import Path
from typing import Any, Callable, Optional

from cspm.config import Config
from cspm.providers import AWSProvider, AzureProvider, GCPProvider
from cspm.core.asset_collector import collect
from cspm.core.asset_catalog import build_catalog, filter_catalog
from cspm.rule_engine import load_rules, RuleEngine
from cspm.risk_engine.risk_engine import RiskEngine
from cspm.change_detection.snapshot_manager import SnapshotManager
from cspm.change_detection.change_detector import ChangeDetector


def _noop(*args: Any, **kwargs: Any) -> None:
    pass


class ScanController:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.rules = load_rules(self.config.rules_dir)
        self.rule_engine = RuleEngine(self.rules)
        self.risk_engine = RiskEngine()
        self.snapshot_manager = SnapshotManager(self.config.snapshots_dir)
        self.change_detector = ChangeDetector(self.snapshot_manager)

    def get_provider(self, cloud: str, **kwargs) -> Any:
        if cloud == "aws":
            return AWSProvider(
                region=kwargs.get("region") or self.config.aws_region,
                organization_role_arn=getattr(self.config, "aws_organization_role_arn", None) or kwargs.get("organization_role_arn"),
                role_assumption_template=getattr(self.config, "aws_role_assumption_template", None) or kwargs.get("role_assumption_template"),
            )
        if cloud == "azure":
            return AzureProvider(
                subscription_id=kwargs.get("subscription_id") or self.config.azure_subscription_id,
                management_group_id=getattr(self.config, "azure_management_group_id", None) or kwargs.get("management_group_id"),
                subscription_ids=getattr(self.config, "azure_subscription_ids", None) or kwargs.get("subscription_ids"),
            )
        if cloud == "gcp":
            return GCPProvider(
                project_id=kwargs.get("project_id") or self.config.gcp_project,
                organization_id=getattr(self.config, "gcp_organization_id", None) or kwargs.get("organization_id"),
                folder_id=getattr(self.config, "gcp_folder_id", None) or kwargs.get("folder_id"),
            )
        raise ValueError(f"Unknown cloud: {cloud}")

    def run_scan(
        self,
        cloud: str,
        save_snapshot: bool = False,
        only: list[str] | None = None,
        region: str | None = None,
        on_progress: Optional[Callable[[str, str, Optional[str]], None]] = None,
    ) -> dict[str, Any]:
        report = on_progress or _noop

        report("Authenticating", "running", None)
        provider = self.get_provider(cloud, region=region)
        if not provider.authenticate():
            return {"error": "Authentication failed", "findings": [], "assets": {}}
        report("Authenticating", "success", None)

        account_id = provider.get_account_id()
        regions = provider.get_regions()
        reg = region or (regions[0] if regions else "")

        report("Discovering assets", "running", None)
        raw = provider.discover_assets(
            asset_types=only if only else None,
            on_progress=on_progress,
        )
        report("Discovering assets", "success", None)

        report("Enriching and scanning assets", "running", None)
        wrap = lambda s, st: (on_progress(s, st, None) if on_progress else None)
        assets = collect(raw, reg, only_types=only, on_progress=wrap)
        # Ensure account_id on each asset (single-account fallback)
        for _rtype, items in assets.items():
            for a in items:
                if "account_id" not in a:
                    a["account_id"] = account_id
        report("Enriching and scanning assets", "success", None)

        report("Running rule engine", "running", None)
        findings = self.rule_engine.evaluate(assets)
        report("Running rule engine", "success", None)

        report("Computing risk score", "running", None)
        risk_score, by_severity = self.risk_engine.compute(findings)
        report("Computing risk score", "success", None)

        report("Building asset catalog", "running", None)
        catalog = build_catalog(assets, cloud, account_id, reg)
        report("Building asset catalog", "success", None)

        snapshot_id = None
        if save_snapshot:
            report("Saving snapshot", "running", None)
            snapshot_id = self.snapshot_manager.save(
                cloud=cloud,
                account_id=account_id,
                region=reg,
                assets=assets,
                findings=findings,
                catalog=catalog,
            )
            report("Saving snapshot", "success", None)

        report("Scan complete", "success", None)
        account_ids = []
        if cloud == "aws" and hasattr(provider, "get_account_ids"):
            account_ids = provider.get_account_ids()
        elif cloud == "gcp" and hasattr(provider, "get_project_ids"):
            account_ids = provider.get_project_ids()
        elif cloud == "azure" and hasattr(provider, "_get_subscription_ids"):
            account_ids = provider._get_subscription_ids()
        return {
            "cloud": cloud,
            "account_id": account_id,
            "account_ids": account_ids if len(account_ids) > 1 else None,
            "region": reg,
            "assets": assets,
            "catalog": catalog,
            "findings": findings,
            "risk_score": risk_score,
            "by_severity": by_severity,
            "snapshot_id": snapshot_id,
        }

    def get_catalog(
        self,
        cloud: str | None = None,
        resource_type: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[dict]:
        if snapshot_id:
            snap = self.snapshot_manager.load(snapshot_id)
            catalog = (snap or {}).get("catalog", [])
        else:
            catalog = []
        return filter_catalog(catalog, cloud=cloud, resource_type=resource_type)
