"""Unit tests for cost_scanner — no cloud credentials required."""
import pytest
from cspm.scanners.cost_scanner import scan_cost, _scan_aws, _scan_gcp, _scan_azure


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rule_ids(result: dict) -> list[str]:
    return [f["rule_id"] for f in result.get("findings", [])]


def _ebs(state="available", size=50, tags=None):
    return {"id": "vol-001", "name": "test-vol", "state": state, "size": size,
            "volume_type": "gp2", "region": "us-east-1", "tags": tags or {}}


def _ec2(state="running", itype="t3.medium", tags=None):
    return {"id": "i-001", "name": "test-ec2", "state": state,
            "instance_type": itype, "region": "us-east-1", "tags": tags or {}}


def _rds(status="available", tags=None):
    return {"id": "db-001", "name": "test-rds", "status": status,
            "region": "us-east-1", "tags": tags or {}}


def _s3(tags=None):
    return {"id": "my-bucket", "name": "my-bucket", "region": "us-east-1", "tags": tags or {}}


def _lambda_fn(memory=128):
    return {"id": "fn-001", "name": "fn-001", "memory_size": memory, "region": "us-east-1"}


def _gce(status="RUNNING", labels=None):
    return {"id": "inst-001", "name": "test-gce", "status": status,
            "region": "us-central1", "labels": labels or {}}


def _gcs(labels=None):
    return {"id": "my-gcs-bucket", "name": "my-gcs-bucket", "labels": labels or {}}


def _azure_vm(power_state="running", tags=None):
    return {"id": "vm-001", "name": "test-vm", "power_state": power_state,
            "region": "eastus", "tags": tags or {}}


def _azure_sa(tags=None):
    return {"id": "sa-001", "name": "test-sa", "region": "eastus", "tags": tags or {}}


# ---------------------------------------------------------------------------
# AWS: EBS
# ---------------------------------------------------------------------------

class TestEBS:
    def test_unattached_ebs_flagged(self):
        result = scan_cost({"ebs": [_ebs(state="available")]}, cloud="aws")
        assert "cost.ebs_unattached" in _rule_ids(result)

    def test_attached_ebs_not_flagged(self):
        result = scan_cost({"ebs": [_ebs(state="in-use")]}, cloud="aws")
        assert "cost.ebs_unattached" not in _rule_ids(result)

    def test_unattached_ebs_has_positive_waste_usd(self):
        result = scan_cost({"ebs": [_ebs(state="available", size=100)]}, cloud="aws")
        finding = next(f for f in result["findings"] if f["rule_id"] == "cost.ebs_unattached")
        assert finding["estimated_monthly_usd"] > 0

    def test_unattached_ebs_category_is_idle(self):
        result = scan_cost({"ebs": [_ebs(state="available")]}, cloud="aws")
        finding = next(f for f in result["findings"] if f["rule_id"] == "cost.ebs_unattached")
        assert finding["category"] == "idle"


# ---------------------------------------------------------------------------
# AWS: EC2
# ---------------------------------------------------------------------------

class TestEC2:
    def test_stopped_ec2_flagged(self):
        result = scan_cost({"ec2": [_ec2(state="stopped")]}, cloud="aws")
        assert "cost.ec2_stopped" in _rule_ids(result)

    def test_running_ec2_not_flagged_idle(self):
        result = scan_cost({"ec2": [_ec2(state="running")]}, cloud="aws")
        assert "cost.ec2_stopped" not in _rule_ids(result)

    def test_large_on_demand_flagged(self):
        result = scan_cost({"ec2": [_ec2(itype="m5.4xlarge")]}, cloud="aws")
        assert "cost.ec2_on_demand_large" in _rule_ids(result)

    def test_small_instance_not_flagged_reservation(self):
        result = scan_cost({"ec2": [_ec2(itype="t3.micro")]}, cloud="aws")
        assert "cost.ec2_on_demand_large" not in _rule_ids(result)

    def test_missing_tags_flagged(self):
        result = scan_cost({"ec2": [_ec2(tags={})]}, cloud="aws")
        assert "cost.ec2_missing_tags" in _rule_ids(result)

    def test_complete_tags_not_flagged(self):
        full_tags = {"Owner": "team", "CostCenter": "123", "Environment": "prod", "Project": "x", "Team": "y"}
        result = scan_cost({"ec2": [_ec2(tags=full_tags)]}, cloud="aws")
        assert "cost.ec2_missing_tags" not in _rule_ids(result)


# ---------------------------------------------------------------------------
# AWS: RDS
# ---------------------------------------------------------------------------

class TestRDS:
    def test_stopped_rds_flagged(self):
        result = scan_cost({"rds": [_rds(status="stopped")]}, cloud="aws")
        assert "cost.rds_stopped" in _rule_ids(result)

    def test_available_rds_not_flagged_idle(self):
        result = scan_cost({"rds": [_rds(status="available")]}, cloud="aws")
        assert "cost.rds_stopped" not in _rule_ids(result)

    def test_rds_missing_tags_flagged(self):
        result = scan_cost({"rds": [_rds(tags={})]}, cloud="aws")
        assert "cost.rds_missing_tags" in _rule_ids(result)


# ---------------------------------------------------------------------------
# AWS: S3
# ---------------------------------------------------------------------------

class TestS3:
    def test_s3_missing_tags_flagged(self):
        result = scan_cost({"s3": [_s3(tags={})]}, cloud="aws")
        assert "cost.s3_missing_tags" in _rule_ids(result)

    def test_s3_with_tags_not_flagged(self):
        full = {"Owner": "x", "CostCenter": "y", "Environment": "z", "Project": "a", "Team": "b"}
        result = scan_cost({"s3": [_s3(tags=full)]}, cloud="aws")
        assert "cost.s3_missing_tags" not in _rule_ids(result)


# ---------------------------------------------------------------------------
# AWS: Lambda
# ---------------------------------------------------------------------------

class TestLambda:
    def test_oversized_lambda_flagged(self):
        result = scan_cost({"lambda": [_lambda_fn(memory=8192)]}, cloud="aws")
        assert "cost.lambda_oversized" in _rule_ids(result)

    def test_normal_lambda_not_flagged(self):
        result = scan_cost({"lambda": [_lambda_fn(memory=512)]}, cloud="aws")
        assert "cost.lambda_oversized" not in _rule_ids(result)


# ---------------------------------------------------------------------------
# GCP
# ---------------------------------------------------------------------------

class TestGCP:
    def test_terminated_gce_flagged(self):
        result = scan_cost({"gce_instance": [_gce(status="TERMINATED")]}, cloud="gcp")
        assert "cost.gce_terminated" in _rule_ids(result)

    def test_running_gce_not_flagged_idle(self):
        result = scan_cost({"gce_instance": [_gce(status="RUNNING")]}, cloud="gcp")
        assert "cost.gce_terminated" not in _rule_ids(result)

    def test_gce_missing_labels_flagged(self):
        result = scan_cost({"gce_instance": [_gce(labels={})]}, cloud="gcp")
        assert "cost.gce_missing_labels" in _rule_ids(result)

    def test_gce_complete_labels_not_flagged(self):
        result = scan_cost({"gce_instance": [_gce(labels={"owner": "x", "environment": "prod", "cost-center": "123"})]}, cloud="gcp")
        assert "cost.gce_missing_labels" not in _rule_ids(result)

    def test_gcs_missing_labels_flagged(self):
        result = scan_cost({"gcs_bucket": [_gcs(labels={})]}, cloud="gcp")
        assert "cost.gcs_missing_labels" in _rule_ids(result)

    def test_gcs_complete_labels_not_flagged(self):
        result = scan_cost({"gcs_bucket": [_gcs(labels={"owner": "x", "environment": "y", "cost-center": "z"})]}, cloud="gcp")
        assert "cost.gcs_missing_labels" not in _rule_ids(result)


# ---------------------------------------------------------------------------
# Azure
# ---------------------------------------------------------------------------

class TestAzure:
    def test_deallocated_vm_flagged(self):
        result = scan_cost({"azure_vm": [_azure_vm(power_state="deallocated")]}, cloud="azure")
        assert "cost.azure_vm_deallocated" in _rule_ids(result)

    def test_running_vm_not_flagged_idle(self):
        result = scan_cost({"azure_vm": [_azure_vm(power_state="running")]}, cloud="azure")
        assert "cost.azure_vm_deallocated" not in _rule_ids(result)

    def test_azure_vm_missing_tags_flagged(self):
        result = scan_cost({"azure_vm": [_azure_vm(tags={})]}, cloud="azure")
        assert "cost.azure_missing_tags" in _rule_ids(result)

    def test_azure_vm_complete_tags_not_flagged(self):
        full = {"Owner": "x", "CostCenter": "y", "Environment": "z", "Project": "a"}
        result = scan_cost({"azure_vm": [_azure_vm(tags=full)]}, cloud="azure")
        assert "cost.azure_missing_tags" not in _rule_ids(result)

    def test_azure_storage_missing_tags_flagged(self):
        result = scan_cost({"azure_storage": [_azure_sa(tags={})]}, cloud="azure")
        assert "cost.azure_missing_tags" in _rule_ids(result)


# ---------------------------------------------------------------------------
# Summary structure
# ---------------------------------------------------------------------------

class TestSummary:
    def test_summary_keys_present(self):
        result = scan_cost({"ebs": [_ebs(state="available")]}, cloud="aws")
        s = result["summary"]
        assert "total_findings" in s
        assert "estimated_monthly_waste_usd" in s
        assert "tagging_score" in s
        assert "by_category" in s

    def test_empty_assets_returns_zero_findings(self):
        result = scan_cost({}, cloud="aws")
        assert result["summary"]["total_findings"] == 0
        assert result["summary"]["estimated_monthly_waste_usd"] == 0

    def test_tagging_score_100_when_no_resources(self):
        result = scan_cost({}, cloud="aws")
        assert result["summary"]["tagging_score"] == 100

    def test_tagging_report_present(self):
        result = scan_cost({"ec2": [_ec2()]}, cloud="aws")
        assert "tagging_report" in result

    def test_unknown_cloud_returns_empty_findings(self):
        result = scan_cost({"ec2": [_ec2()]}, cloud="unknown")
        assert result["summary"]["total_findings"] == 0

    def test_idle_category_counted(self):
        result = scan_cost({"ebs": [_ebs(state="available")]}, cloud="aws")
        assert result["summary"]["by_category"].get("idle", 0) >= 1

    def test_tagging_category_counted(self):
        result = scan_cost({"ec2": [_ec2(tags={})]}, cloud="aws")
        assert result["summary"]["by_category"].get("tagging", 0) >= 1
