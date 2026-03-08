"""Cost optimisation scanner — flags wasteful resources for AWS, GCP, and Azure.

Categories
----------
idle        Resources that are provisioned but not in use (stopped VMs, unattached disks, etc.)
tagging     Resources missing cost-allocation tags / labels — prevents cost attribution
rightsizing Instances that appear over-provisioned based on static heuristics
reservation On-demand instances that would be cheaper on a reserved / committed-use plan
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SEVERITY_HIGH   = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW    = "low"

# Estimated per-month waste in USD (very rough — helps rank findings)
_WASTE_USD = {
    "cost.ebs_unattached":          8,
    "cost.eip_unused":              4,
    "cost.ec2_stopped":            30,
    "cost.rds_stopped":            60,
    "cost.old_snapshot":            2,
    "cost.ec2_missing_tags":        0,
    "cost.s3_missing_tags":         0,
    "cost.rds_missing_tags":        0,
    "cost.ec2_on_demand_large":   200,
    "cost.lambda_oversized":        5,
    "cost.gce_terminated":         25,
    "cost.gce_missing_labels":      0,
    "cost.gcs_missing_labels":      0,
    "cost.gce_unused_disk":         5,
    "cost.azure_vm_deallocated":   20,
    "cost.azure_missing_tags":      0,
    "cost.azure_unattached_disk":   5,
    "cost.azure_unused_public_ip":  4,
}

# Instance families considered "large" — flag for reserved / savings plan
_AWS_LARGE_FAMILIES = {
    "c5.4xlarge", "c5.9xlarge", "c5.18xlarge", "c5.24xlarge",
    "m5.4xlarge", "m5.8xlarge", "m5.12xlarge", "m5.16xlarge", "m5.24xlarge",
    "r5.4xlarge", "r5.8xlarge", "r5.12xlarge", "r5.16xlarge", "r5.24xlarge",
    "p3.8xlarge", "p3.16xlarge", "p4d.24xlarge",
    "x1.16xlarge", "x1.32xlarge", "x1e.32xlarge",
}

_COST_TAGS = {"Owner", "CostCenter", "Environment", "Project", "Team"}
_LAMBDA_MAX_REASONABLE_MB = 3008  # anything at max (10240) for a non-specialist fn is likely oversized


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _f(
    rule_id: str,
    resource_type: str,
    resource_id: str,
    resource_name: str,
    title: str,
    severity: str,
    detail: str,
    remediation: str,
    region: str = "global",
    category: str = "idle",
    estimated_monthly_usd: float | None = None,
    cloud: str = "aws",
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": resource_name or resource_id,
        "title": title,
        "severity": severity,
        "detail": detail,
        "remediation": remediation,
        "region": region,
        "category": category,
        "estimated_monthly_usd": estimated_monthly_usd if estimated_monthly_usd is not None else _WASTE_USD.get(rule_id, 0),
        "passed": False,
        "cloud": cloud,
    }


def _days_old(timestamp_str: str | None) -> int | None:
    """Return the age in days for an ISO-8601 timestamp string, or None."""
    if not timestamp_str:
        return None
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - dt).days
    except Exception:
        return None


def _missing_tags(tags: dict, required: set = _COST_TAGS) -> list[str]:
    return [t for t in required if t not in tags]


# ---------------------------------------------------------------------------
# AWS cost checks
# ---------------------------------------------------------------------------

def _scan_aws(assets: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    # ── EBS volumes ────────────────────────────────────────────────────────
    for vol in assets.get("ebs", []):
        vid = vol.get("id", "unknown")
        name = vol.get("name") or vid
        region = vol.get("region", "us-east-1")
        state = (vol.get("state") or "").lower()

        if state == "available":
            size_gb = vol.get("size", 0) or 0
            monthly = max(1, size_gb) * 0.1  # ~$0.10/GB/month gp2
            findings.append(_f(
                "cost.ebs_unattached", "ebs", vid, name,
                f"Unattached EBS volume ({size_gb} GiB)",
                SEVERITY_MEDIUM,
                f"Volume {vid} ({size_gb} GiB, {vol.get('volume_type','gp2')}) has been unattached for an "
                f"unknown period and is accumulating storage charges (~${monthly:.0f}/mo).",
                "Snapshot the volume if needed then delete it: `aws ec2 delete-volume --volume-id " + vid + "`",
                region=region, category="idle", estimated_monthly_usd=monthly, cloud="aws",
            ))

    # ── EC2 instances ───────────────────────────────────────────────────────
    for inst in assets.get("ec2", []):
        iid = inst.get("id", "unknown")
        name = inst.get("name") or iid
        region = inst.get("region", "us-east-1")
        state = (inst.get("state") or "running").lower()
        itype = (inst.get("instance_type") or "").lower()
        tags = inst.get("tags") or {}

        if state == "stopped":
            findings.append(_f(
                "cost.ec2_stopped", "ec2", iid, name,
                f"Stopped EC2 instance ({itype})",
                SEVERITY_MEDIUM,
                f"Instance {iid} ({itype}) is stopped but its EBS-backed storage and any attached "
                f"Elastic IPs continue to incur charges.",
                "Terminate the instance if no longer needed (`aws ec2 terminate-instances --instance-ids "
                + iid + "`). Snapshot the root volume first if you need to preserve data.",
                region=region, category="idle", cloud="aws",
            ))

        missing = _missing_tags(tags)
        if missing:
            findings.append(_f(
                "cost.ec2_missing_tags", "ec2", iid, name,
                "EC2 instance missing cost-allocation tags",
                SEVERITY_LOW,
                f"Instance {iid} ({itype}) is missing tags: {', '.join(missing)}. "
                f"Without these tags, spend cannot be attributed to a team or project in Cost Explorer.",
                f"Apply tags via the AWS Console, CLI (`aws ec2 create-tags`), or IaC. "
                f"Recommended tags: {', '.join(_COST_TAGS)}.",
                region=region, category="tagging", estimated_monthly_usd=0, cloud="aws",
            ))

        if itype in _AWS_LARGE_FAMILIES:
            findings.append(_f(
                "cost.ec2_on_demand_large", "ec2", iid, name,
                f"Large on-demand instance — consider Reserved Instance or Savings Plan ({itype})",
                SEVERITY_LOW,
                f"Instance {iid} is a large on-demand {itype}. Running large instances 24/7 on "
                f"on-demand pricing can be 30–60 % more expensive than a 1-year reserved commitment.",
                "Evaluate 1-year or 3-year Reserved Instances or Compute Savings Plans in AWS Cost Explorer "
                "to reduce costs by up to 60 %.",
                region=region, category="reservation", estimated_monthly_usd=200, cloud="aws",
            ))

    # ── RDS instances ───────────────────────────────────────────────────────
    for db in assets.get("rds", []):
        did = db.get("id", "unknown")
        name = db.get("name") or did
        region = db.get("region", "us-east-1")
        state = (db.get("status") or "available").lower()
        tags = db.get("tags") or {}

        if state == "stopped":
            findings.append(_f(
                "cost.rds_stopped", "rds", did, name,
                "Stopped RDS instance still incurring storage costs",
                SEVERITY_MEDIUM,
                f"RDS instance {did} is stopped. AWS continues to charge for storage and any "
                f"associated reserved IOPS. RDS instances also auto-restart after 7 days of being stopped.",
                "Delete the instance and restore from a final snapshot when needed, or use Aurora Serverless v2 "
                "which scales to zero.",
                region=region, category="idle", cloud="aws",
            ))

        missing = _missing_tags(tags)
        if missing:
            findings.append(_f(
                "cost.rds_missing_tags", "rds", did, name,
                "RDS instance missing cost-allocation tags",
                SEVERITY_LOW,
                f"RDS {did} is missing tags: {', '.join(missing)}.",
                f"Apply required tags via Console or `aws rds add-tags-to-resource`.",
                region=region, category="tagging", estimated_monthly_usd=0, cloud="aws",
            ))

    # ── S3 buckets ──────────────────────────────────────────────────────────
    for bucket in assets.get("s3", []):
        bid = bucket.get("id", "unknown")
        name = bucket.get("name") or bid
        region = bucket.get("region", "us-east-1")
        tags = bucket.get("tags") or {}
        missing = _missing_tags(tags)
        if missing:
            findings.append(_f(
                "cost.s3_missing_tags", "s3", bid, name,
                "S3 bucket missing cost-allocation tags",
                SEVERITY_LOW,
                f"Bucket {bid} is missing tags: {', '.join(missing)}. "
                "S3 is often one of the top 3 AWS cost drivers — tagging is essential for attribution.",
                "Add tags via Console or `aws s3api put-bucket-tagging`.",
                region=region, category="tagging", estimated_monthly_usd=0, cloud="aws",
            ))

    # ── Lambda functions ────────────────────────────────────────────────────
    for fn in assets.get("lambda", []):
        fid = fn.get("id", "unknown")
        name = fn.get("name") or fid
        region = fn.get("region", "us-east-1")
        memory = fn.get("memory_size") or 0

        if memory >= 8192:
            findings.append(_f(
                "cost.lambda_oversized", "lambda", fid, name,
                f"Lambda function allocated {memory} MB — likely over-provisioned",
                SEVERITY_LOW,
                f"Function {name} has {memory} MB of memory. Unless it processes very large payloads "
                f"or has heavy compute needs, this is likely over-provisioned and drives unnecessary cost.",
                "Use AWS Lambda Power Tuning (open-source Step Functions state machine) to find the "
                "optimal memory/cost trade-off for this function.",
                region=region, category="rightsizing", cloud="aws",
            ))

    return findings


# ---------------------------------------------------------------------------
# GCP cost checks
# ---------------------------------------------------------------------------

def _scan_gcp(assets: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    # ── GCE instances ───────────────────────────────────────────────────────
    for inst in assets.get("gce_instance", []):
        iid = inst.get("id", "unknown")
        name = inst.get("name") or iid
        region = inst.get("region", "us-central1")
        status = (inst.get("status") or "running").upper()
        labels = inst.get("labels") or {}

        if status == "TERMINATED":
            findings.append(_f(
                "cost.gce_terminated", "gce_instance", iid, name,
                "Terminated GCE instance still has attached persistent disks",
                SEVERITY_MEDIUM,
                f"GCE instance {name} is in TERMINATED state. Its persistent disks continue to incur "
                f"storage costs (~$0.04–$0.17/GB/month) even when the VM is not running.",
                "Delete the instance (and its disks) if no longer needed: `gcloud compute instances delete "
                + name + " --delete-disks=all`. Snapshot disks first if data must be preserved.",
                region=region, category="idle", cloud="gcp",
            ))

        required_labels = {"owner", "environment", "cost-center"}
        missing = [l for l in required_labels if l not in labels]
        if missing:
            findings.append(_f(
                "cost.gce_missing_labels", "gce_instance", iid, name,
                "GCE instance missing cost-allocation labels",
                SEVERITY_LOW,
                f"Instance {name} is missing labels: {', '.join(missing)}. "
                "GCP uses labels for cost attribution in Billing Export and BigQuery.",
                "Add labels via Console or `gcloud compute instances add-labels " + name
                + " --labels=owner=team,environment=prod,cost-center=123`.",
                region=region, category="tagging", estimated_monthly_usd=0, cloud="gcp",
            ))

    # ── GCS buckets ─────────────────────────────────────────────────────────
    for bucket in assets.get("gcs_bucket", []):
        bid = bucket.get("id", "unknown")
        name = bucket.get("name") or bid
        labels = bucket.get("labels") or {}
        required_labels = {"owner", "environment", "cost-center"}
        missing = [l for l in required_labels if l not in labels]
        if missing:
            findings.append(_f(
                "cost.gcs_missing_labels", "gcs_bucket", bid, name,
                "GCS bucket missing cost-allocation labels",
                SEVERITY_LOW,
                f"Bucket {name} is missing labels: {', '.join(missing)}. Without labels, "
                "storage costs cannot be attributed in Cloud Billing reports.",
                "Add labels via Console or `gsutil label ch -l owner:team gs://" + name + "`.",
                region="global", category="tagging", estimated_monthly_usd=0, cloud="gcp",
            ))

    return findings


# ---------------------------------------------------------------------------
# Azure cost checks
# ---------------------------------------------------------------------------

def _scan_azure(assets: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    _AZURE_COST_TAGS = {"Owner", "CostCenter", "Environment", "Project"}

    # ── Azure VMs ───────────────────────────────────────────────────────────
    for vm in assets.get("azure_vm", []):
        vid = vm.get("id", "unknown")
        name = vm.get("name") or vid
        region = vm.get("region", "eastus")
        state = (vm.get("power_state") or "running").lower()
        tags = vm.get("tags") or {}

        if "deallocated" in state or "stopped" in state:
            findings.append(_f(
                "cost.azure_vm_deallocated", "azure_vm", vid, name,
                "Deallocated Azure VM still incurring managed disk costs",
                SEVERITY_MEDIUM,
                f"VM {name} is deallocated. While compute charges stop, managed disk(s) attached to "
                f"the VM continue to incur charges (~$5–$20+/month per disk depending on size/tier).",
                "Delete the VM (and its disks) if no longer needed via Portal or: "
                "`az vm delete --resource-group <rg> --name " + name + " --yes`. "
                "Snapshot disks first if needed.",
                region=region, category="idle", cloud="azure",
            ))

        missing = _missing_tags(tags, _AZURE_COST_TAGS)
        if missing:
            findings.append(_f(
                "cost.azure_missing_tags", "azure_vm", vid, name,
                "Azure VM missing cost-allocation tags",
                SEVERITY_LOW,
                f"VM {name} is missing tags: {', '.join(missing)}. "
                "Azure Cost Management uses tags for subscription-level cost breakdowns.",
                "Add tags via Portal, CLI (`az vm update --resource-group <rg> --name "
                + name + " --set tags.Owner=team`), or policy enforcement.",
                region=region, category="tagging", estimated_monthly_usd=0, cloud="azure",
            ))

    # ── Azure Storage Accounts ──────────────────────────────────────────────
    for sa in assets.get("azure_storage", []):
        sid = sa.get("id", "unknown")
        name = sa.get("name") or sid
        region = sa.get("region", "eastus")
        tags = sa.get("tags") or {}
        missing = _missing_tags(tags, _AZURE_COST_TAGS)
        if missing:
            findings.append(_f(
                "cost.azure_missing_tags", "azure_storage", sid, name,
                "Azure Storage Account missing cost-allocation tags",
                SEVERITY_LOW,
                f"Storage Account {name} is missing tags: {', '.join(missing)}. "
                "Storage is often a top Azure cost driver — tagging is critical for attribution.",
                "Add tags via Portal or `az storage account update --name " + name
                + " --resource-group <rg> --tags Owner=team Environment=prod`.",
                region=region, category="tagging", estimated_monthly_usd=0, cloud="azure",
            ))

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_cost(
    assets: dict[str, list[dict[str, Any]]],
    cloud: str = "aws",
) -> dict[str, Any]:
    """Run cost analysis on already-discovered assets.

    Parameters
    ----------
    assets:
        Dict of ``{ asset_type: [asset_dict, ...] }`` as returned by a provider's
        ``discover_assets()``.
    cloud:
        One of ``"aws"``, ``"gcp"``, ``"azure"``.

    Returns
    -------
    dict with keys:
        findings        list[dict]   individual cost findings
        summary         dict         aggregate KPIs
        tagging_report  dict         per-resource-type tag compliance %
    """
    cloud = (cloud or "aws").lower()

    if cloud == "aws":
        findings = _scan_aws(assets)
    elif cloud == "gcp":
        findings = _scan_gcp(assets)
    elif cloud == "azure":
        findings = _scan_azure(assets)
    else:
        findings = []

    # ── Aggregate summary ───────────────────────────────────────────────────
    by_cat: dict[str, int] = {}
    total_waste_usd = 0.0
    for f in findings:
        cat = f.get("category", "other")
        by_cat[cat] = by_cat.get(cat, 0) + 1
        total_waste_usd += f.get("estimated_monthly_usd") or 0

    # Tagging score: 0 if all resources are missing tags, 100 if none are
    tag_findings = [f for f in findings if f.get("category") == "tagging"]
    all_resources = sum(len(v) for v in assets.values())
    if all_resources > 0:
        tag_score = max(0, round(100 * (1 - len(tag_findings) / max(all_resources, 1))))
    else:
        tag_score = 100

    summary = {
        "cloud": cloud,
        "total_waste_items": len([f for f in findings if f.get("category") != "tagging"]),
        "total_findings": len(findings),
        "estimated_monthly_waste_usd": round(total_waste_usd, 2),
        "tagging_score": tag_score,
        "by_category": by_cat,
    }

    # ── Tagging report per resource type ────────────────────────────────────
    tagging_report: dict[str, dict] = {}
    for f in tag_findings:
        rt = f.get("resource_type", "unknown")
        if rt not in tagging_report:
            tagging_report[rt] = {"total": 0, "missing_tags": 0}
        tagging_report[rt]["missing_tags"] += 1
    for rt, items in assets.items():
        if rt not in tagging_report:
            tagging_report[rt] = {"total": len(items), "missing_tags": 0}
        else:
            tagging_report[rt]["total"] = len(items)

    return {
        "findings": findings,
        "summary": summary,
        "tagging_report": tagging_report,
    }
