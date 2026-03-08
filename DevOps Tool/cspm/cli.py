"""Unified CLI: scan, assets, changes, compliance, governance, pentest, report."""
import argparse
import sys
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cspm.config import Config
from cspm.core.scan_controller import ScanController
from cspm.reporting import generate_json_report, export_audit_csv, export_audit_json, generate_change_report
from cspm.reporting.html_report import generate_html_report
from cspm.compliance.compliance_report import generate_compliance_report
from cspm.governance.governance_report import generate_governance_report
from cspm.pentest import find_exposed_services, scan_secrets, map_findings_to_exploits
from cspm.vulnerability import run_vulnerability_scan


def cmd_ui(args):
    import uvicorn

    uvicorn.run(
        "cspm.ui.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def cmd_scan(args):
    config = Config()
    ctrl = ScanController(config)
    only = args.only.split(",") if getattr(args, "only", None) else None
    result = ctrl.run_scan(
        cloud=args.cloud,
        save_snapshot=args.save_snapshot,
        only=only,
        region=getattr(args, "region", None),
    )
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        return 1
    if args.output == "json":
        print(generate_json_report(result))
    else:
        print(generate_html_report(result))
    return 0


def cmd_assets_list(args):
    config = Config()
    ctrl = ScanController(config)
    cloud = getattr(args, "cloud", None) or "aws"
    snapshot_id = getattr(args, "snapshot", None)
    resource_type = getattr(args, "type", None)
    catalog = ctrl.get_catalog(cloud=cloud, resource_type=resource_type, snapshot_id=snapshot_id)
    if not catalog and not snapshot_id:
        result = ctrl.run_scan(cloud=cloud)
        catalog = result.get("catalog", [])
    from cspm.core.asset_catalog import filter_catalog
    catalog = filter_catalog(catalog, cloud=cloud, resource_type=resource_type)
    if args.output == "csv":
        print(export_audit_csv(catalog))
    else:
        print(export_audit_json(catalog))
    return 0


def cmd_assets_diff(args):
    config = Config()
    ctrl = ScanController(config)
    diff = ctrl.change_detector.diff(args.snapshot_before, args.snapshot_after)
    if diff.get("error"):
        print(diff["error"], file=sys.stderr)
        return 1
    print(generate_change_report(diff, format="json"))
    return 0


def cmd_changes(args):
    config = Config()
    ctrl = ScanController(config)
    cloud = args.cloud or "aws"
    result = ctrl.run_scan(cloud=cloud)
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        return 1
    diff = ctrl.change_detector.changes_since_last(
        cloud=cloud,
        account_id=result["account_id"],
        region=result["region"],
        current_assets=result["assets"],
        current_findings=result["findings"],
        current_catalog=result["catalog"],
    )
    if diff is None:
        print("No previous snapshot found. Run scan with --save-snapshot first.")
        return 0
    print(generate_change_report(diff, format="html" if args.output == "html" else "json"))
    return 0


def cmd_compliance(args):
    config = Config()
    ctrl = ScanController(config)
    result = ctrl.run_scan(cloud=args.cloud or "aws")
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        return 1
    report = generate_compliance_report(
        result["findings"],
        framework=args.framework,
        output_format=args.output,
    )
    print(report)
    return 0


def cmd_governance(args):
    config = Config()
    ctrl = ScanController(config)
    result = ctrl.run_scan(cloud=args.cloud or "aws")
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        return 1
    catalog = result.get("catalog", [])
    report = generate_governance_report(
        catalog,
        output_format=args.output,
    )
    print(report)
    return 0


def cmd_pentest(args):
    config = Config()
    ctrl = ScanController(config)
    result = ctrl.run_scan(cloud=args.cloud or "aws")
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        return 1
    assets = result.get("assets", {})
    findings = result.get("findings", [])
    out = {}
    if args.exposed or not (args.exposed or args.secrets or args.exploit_map):
        out["exposed_services"] = find_exposed_services(assets)
    if args.secrets or not (args.exposed or args.secrets or args.exploit_map):
        out["secrets"] = scan_secrets(assets, repo_path=getattr(args, "repo_path", None))
    if args.exploit_map or not (args.exposed or args.secrets or args.exploit_map):
        out["exploit_scenarios"] = map_findings_to_exploits(findings)
    import json
    print(json.dumps(out, indent=2))
    return 0


def cmd_report(args):
    config = Config()
    ctrl = ScanController(config)
    if getattr(args, "snapshot", None):
        snap = ctrl.snapshot_manager.load(args.snapshot)
        if not snap:
            print("Snapshot not found", file=sys.stderr)
            return 1
        result = {
            "cloud": snap.get("cloud"),
            "account_id": snap.get("account_id"),
            "region": snap.get("region"),
            "findings": snap.get("findings", []),
            "risk_score": sum(
                -10 if f.get("severity") == "critical" else -7 if f.get("severity") == "high" else -4
                for f in snap.get("findings", [])
            ),
            "by_severity": {},
            "snapshot_id": snap.get("snapshot_id"),
        }
        from collections import Counter
        result["by_severity"] = dict(Counter(f.get("severity") for f in snap.get("findings", [])))
    else:
        result = ctrl.run_scan(cloud=args.cloud or "aws")
        if result.get("error"):
            print(result["error"], file=sys.stderr)
            return 1
    if args.format == "html":
        print(generate_html_report(result))
    else:
        print(generate_json_report(result))
    return 0


def main():
    parser = argparse.ArgumentParser(prog="cspm", description="CloudRadar - DevOps Security Platform")
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="Run security scan")
    p_scan.add_argument("cloud", choices=["aws", "azure", "gcp"])
    p_scan.add_argument("--save-snapshot", action="store_true")
    p_scan.add_argument("--only", type=str, help="Comma-separated: ec2,s3,waf,...")
    p_scan.add_argument("--region", type=str)
    p_scan.add_argument("--output", choices=["json", "html"], default="json")
    p_scan.set_defaults(func=cmd_scan)

    # assets list
    p_assets = sub.add_parser("assets", help="Asset commands")
    p_assets_sub = p_assets.add_subparsers(dest="assets_cmd")
    p_list = p_assets_sub.add_parser("list", help="List assets for audit")
    p_list.add_argument("--cloud", type=str, default="aws")
    p_list.add_argument("--type", type=str, help="Resource type filter")
    p_list.add_argument("--output", choices=["csv", "json"], default="json")
    p_list.add_argument("--snapshot", type=str)
    p_list.set_defaults(func=cmd_assets_list)
    # fix: list has optional cloud as positional
    p_diff = p_assets_sub.add_parser("diff", help="Diff two snapshots")
    p_diff.add_argument("snapshot_before", type=str)
    p_diff.add_argument("snapshot_after", type=str)
    p_diff.set_defaults(func=cmd_assets_diff)

    # changes
    p_changes = sub.add_parser("changes", help="Changes since last run")
    p_changes.add_argument("--cloud", type=str, default="aws")
    p_changes.add_argument("--output", choices=["json", "html"], default="json")
    p_changes.set_defaults(func=cmd_changes)

    # compliance
    p_comp = sub.add_parser("compliance", help="Compliance report")
    p_comp.add_argument("--framework", choices=["cis", "soc2"], default="cis")
    p_comp.add_argument("--cloud", type=str, default="aws")
    p_comp.add_argument("--output", choices=["json", "html"], default="json")
    p_comp.set_defaults(func=cmd_compliance)

    # governance
    p_gov = sub.add_parser("governance", help="Governance report")
    p_gov.add_argument("--cloud", type=str, default="aws")
    p_gov.add_argument("--output", choices=["json", "html"], default="json")
    p_gov.set_defaults(func=cmd_governance)

    # pentest
    p_pt = sub.add_parser("pentest", help="Basic pen test")
    p_pt.add_argument("--cloud", type=str, default="aws")
    p_pt.add_argument("--exposed", action="store_true")
    p_pt.add_argument("--secrets", action="store_true")
    p_pt.add_argument("--exploit-map", action="store_true")
    p_pt.add_argument("--repo-path", type=str)
    p_pt.set_defaults(func=cmd_pentest)

    # report
    p_rep = sub.add_parser("report", help="Generate report")
    p_rep.add_argument("--format", choices=["json", "html"], default="json")
    p_rep.add_argument("--snapshot", type=str)
    p_rep.add_argument("--cloud", type=str, default="aws")
    p_rep.set_defaults(func=cmd_report)

    # ui
    p_ui = sub.add_parser("ui", help="Run Web UI (FastAPI)")
    p_ui.add_argument("--host", type=str, default="127.0.0.1")
    p_ui.add_argument("--port", type=int, default=8000)
    p_ui.add_argument("--reload", action="store_true")
    p_ui.set_defaults(func=cmd_ui)

    args = parser.parse_args()
    if args.command == "assets":
        if getattr(args, "assets_cmd", None) == "list":
            return cmd_assets_list(args)
        if getattr(args, "assets_cmd", None) == "diff":
            return cmd_assets_diff(args)
    func = getattr(args, "func", None)
    if not func:
        parser.error("Use: scan, assets list, assets diff, changes, compliance, governance, pentest, report, ui")
    return func(args)


if __name__ == "__main__":
    sys.exit(main())
