"""Tests for compliance report generation across all frameworks."""
import json
import pytest
from cspm.compliance.compliance_report import generate_compliance_report
from cspm.compliance.hipaa_checks import get_hipaa_checks, HIPAA_MAP
from cspm.compliance.pci_checks import get_pci_checks, PCI_MAP
from cspm.compliance.iso27001_checks import get_iso27001_checks, ISO27001_MAP


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_findings():
    return [
        {"rule_id": "s3_encryption", "resource_id": "my-bucket", "resource_type": "s3", "severity": "high"},
        {"rule_id": "iam_admin_policy", "resource_id": "arn:aws:iam::123:policy/AdminPolicy", "resource_type": "iam", "severity": "critical"},
        {"rule_id": "security_group_open_world", "resource_id": "sg-0abc", "resource_type": "security_group", "severity": "high"},
        {"rule_id": "cloudtrail_logging_disabled", "resource_id": "trail-1", "resource_type": "cloudtrail", "severity": "medium"},
        {"rule_id": "vpc_flow_logs_disabled", "resource_id": "vpc-001", "resource_type": "vpc", "severity": "medium"},
        {"rule_id": "guardduty_not_enabled", "resource_id": "us-east-1", "resource_type": "guardduty", "severity": "high"},
    ]


# ---------------------------------------------------------------------------
# CIS
# ---------------------------------------------------------------------------

def test_cis_report_structure(sample_findings):
    out = generate_compliance_report(sample_findings, "cis")
    data = json.loads(out)
    assert data["framework"] == "cis"
    assert "passed" in data
    assert "failed" in data
    assert isinstance(data["passed_controls"], list)
    assert isinstance(data["failed_controls"], list)


def test_cis_report_detects_failures(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "cis"))
    assert data["failed"] > 0


def test_cis_report_no_findings():
    data = json.loads(generate_compliance_report([], "cis"))
    assert data["failed"] == 0


# ---------------------------------------------------------------------------
# SOC2
# ---------------------------------------------------------------------------

def test_soc2_report_structure(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "soc2"))
    assert data["framework"] == "soc2"
    assert "failures_detail" in data


def test_soc2_report_detects_failures(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "soc2"))
    assert data["failed"] > 0


# ---------------------------------------------------------------------------
# HIPAA
# ---------------------------------------------------------------------------

def test_hipaa_report_structure(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "hipaa"))
    assert data["framework"] == "hipaa"
    assert isinstance(data["passed_controls"], list)
    assert isinstance(data["failed_controls"], list)


def test_hipaa_report_encryption_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "hipaa"))
    assert "164.312(a)(2)(iv)" in data["failed_controls"]


def test_hipaa_report_audit_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "hipaa"))
    assert "164.312(b)" in data["failed_controls"]


def test_hipaa_report_access_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "hipaa"))
    assert "164.312(a)(1)" in data["failed_controls"]


def test_hipaa_report_no_findings():
    data = json.loads(generate_compliance_report([], "hipaa"))
    assert data["failed"] == 0
    assert data["passed"] > 0


# ---------------------------------------------------------------------------
# PCI
# ---------------------------------------------------------------------------

def test_pci_report_structure(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "pci"))
    assert data["framework"] == "pci"
    assert isinstance(data["failures_detail"], dict)


def test_pci_report_encryption_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "pci"))
    assert "PCI.3.4" in data["failed_controls"]


def test_pci_report_network_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "pci"))
    assert "PCI.1.2" in data["failed_controls"]


def test_pci_report_no_findings():
    data = json.loads(generate_compliance_report([], "pci"))
    assert data["failed"] == 0


# ---------------------------------------------------------------------------
# ISO 27001
# ---------------------------------------------------------------------------

def test_iso27001_report_structure(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "iso27001"))
    assert data["framework"] == "iso27001"
    assert isinstance(data["passed_controls"], list)
    assert isinstance(data["failed_controls"], list)
    assert "failures_detail" in data


def test_iso27001_encryption_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "iso27001"))
    # s3_encryption maps to A.8.24 (Use of cryptography)
    assert "A.8.24" in data["failed_controls"]


def test_iso27001_access_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "iso27001"))
    # iam_admin_policy maps to A.5.15 (Access control)
    assert "A.5.15" in data["failed_controls"]


def test_iso27001_monitoring_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "iso27001"))
    # guardduty_not_enabled and vpc_flow_logs_disabled map to A.8.16 (Monitoring)
    assert "A.8.16" in data["failed_controls"]


def test_iso27001_logging_control_fails(sample_findings):
    data = json.loads(generate_compliance_report(sample_findings, "iso27001"))
    # cloudtrail_logging_disabled maps to A.8.15 (Logging)
    assert "A.8.15" in data["failed_controls"]


def test_iso27001_no_findings():
    data = json.loads(generate_compliance_report([], "iso27001"))
    assert data["failed"] == 0
    assert data["passed"] > 0


def test_get_iso27001_checks_returns_list():
    checks = get_iso27001_checks()
    assert isinstance(checks, list)
    assert len(checks) > 0


def test_get_iso27001_checks_unique_ids():
    checks = get_iso27001_checks()
    ids = [c["id"] for c in checks]
    assert len(ids) == len(set(ids))


def test_get_iso27001_checks_schema():
    for check in get_iso27001_checks():
        assert "id" in check
        assert "title" in check
        assert "category" in check


def test_iso27001_map_covers_key_rules():
    assert "s3_encryption" in ISO27001_MAP
    assert "iam_admin_policy" in ISO27001_MAP
    assert "cloudtrail_logging_disabled" in ISO27001_MAP
    assert "guardduty_not_enabled" in ISO27001_MAP


# ---------------------------------------------------------------------------
# Unknown framework
# ---------------------------------------------------------------------------

def test_unknown_framework_returns_error():
    out = generate_compliance_report([], "nist800")
    data = json.loads(out)
    assert "error" in data
    assert "nist800" in data["error"]


# ---------------------------------------------------------------------------
# HIPAA / PCI / ISO27001 control helper functions
# ---------------------------------------------------------------------------

def test_get_hipaa_checks_returns_list():
    checks = get_hipaa_checks()
    assert isinstance(checks, list)
    assert len(checks) > 0


def test_get_hipaa_checks_unique_ids():
    checks = get_hipaa_checks()
    ids = [c["id"] for c in checks]
    assert len(ids) == len(set(ids))


def test_get_hipaa_checks_schema():
    for check in get_hipaa_checks():
        assert "id" in check
        assert "title" in check
        assert "category" in check


def test_get_pci_checks_returns_list():
    checks = get_pci_checks()
    assert isinstance(checks, list)
    assert len(checks) > 0


def test_get_pci_checks_unique_ids():
    checks = get_pci_checks()
    ids = [c["id"] for c in checks]
    assert len(ids) == len(set(ids))


def test_get_pci_checks_schema():
    for check in get_pci_checks():
        assert "id" in check
        assert "title" in check
        assert "category" in check
