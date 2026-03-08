"""Tests for CSPM."""
import os
import pytest
from cspm.rule_engine import load_rules, RuleEngine
from cspm.core.asset_catalog import build_catalog, filter_catalog
from cspm.risk_engine import RiskEngine
from cspm.change_detection.snapshot_manager import SnapshotManager
from cspm.change_detection.change_detector import ChangeDetector
from cspm.governance.tag_policy_engine import TagPolicyEngine
from cspm.pentest.exposed_services import find_exposed_services
from cspm.pentest.misconfig_exploit_check import map_findings_to_exploits
import tempfile

RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "cspm", "rules")


def test_rule_loader():
    rules = load_rules(RULES_DIR)
    assert isinstance(rules, list)
    ids = [r.get("id") for r in rules if r.get("id")]
    assert len(ids) >= 1


def test_rule_engine_evaluate():
    # op="true" means "field should be True — finding when it is NOT True (i.e. False)"
    # This correctly detects encryption_enabled=False as a security finding.
    engine = RuleEngine([
        {"id": "r1", "resource_type": "s3", "condition": {"op": "true", "key": "encryption_enabled"}},
    ])
    assets = {"s3": [{"id": "b1", "type": "s3", "encryption_enabled": False}]}
    findings = engine.evaluate(assets)
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "r1"


def test_asset_catalog_build():
    assets = {"ec2": [{"id": "i-1", "type": "ec2", "tags": {"a": "b"}}]}
    catalog = build_catalog(assets, "aws", "123", "us-east-1")
    assert len(catalog) == 1
    assert catalog[0]["cloud"] == "aws"
    assert catalog[0]["type"] == "ec2"


def test_filter_catalog():
    catalog = [
        {"id": "1", "cloud": "aws", "type": "ec2"},
        {"id": "2", "cloud": "aws", "type": "s3"},
    ]
    out = filter_catalog(catalog, resource_type="ec2")
    assert len(out) == 1
    assert out[0]["type"] == "ec2"


def test_risk_engine():
    engine = RiskEngine()
    findings = [{"severity": "high"}, {"severity": "medium"}]
    score, by_sev = engine.compute(findings)
    assert by_sev.get("high") == 1
    assert by_sev.get("medium") == 1


def test_snapshot_manager():
    with tempfile.TemporaryDirectory() as d:
        mgr = SnapshotManager(d)
        sid = mgr.save("aws", "123", "us-east-1", {"ec2": []}, [], [{"id": "a", "type": "ec2"}])
        assert sid
        loaded = mgr.load(sid)
        assert loaded is not None
        assert len(loaded["catalog"]) == 1


def test_change_detector():
    with tempfile.TemporaryDirectory() as d:
        mgr = SnapshotManager(d)
        sid1 = mgr.save("aws", "123", "us-east-1", {}, [], [{"id": "1", "type": "ec2", "cloud": "aws", "account_id": "123", "region": "us-east-1"}])
        sid2 = mgr.save("aws", "123", "us-east-1", {}, [], [
            {"id": "1", "type": "ec2", "cloud": "aws", "account_id": "123", "region": "us-east-1"},
            {"id": "2", "type": "ec2", "cloud": "aws", "account_id": "123", "region": "us-east-1"},
        ])
        det = ChangeDetector(mgr)
        diff = det.diff(sid1, sid2)
        assert len(diff["added"]) == 1
        assert len(diff["removed"]) == 0


def test_tag_policy_engine():
    engine = TagPolicyEngine(required_tags=["Owner"])
    catalog = [
        {"id": "1", "tags": {"Owner": "team-a"}},
        {"id": "2", "tags": {}},
    ]
    result = engine.evaluate(catalog)
    assert result["compliant_count"] == 1
    assert result["non_compliant_count"] == 1


def test_exposed_services():
    assets = {
        "security_group": [
            {"id": "sg-1", "ip_permissions": [{"cidr": "0.0.0.0/0", "from_port": 22, "to_port": 22}]},
        ],
    }
    out = find_exposed_services(assets)
    assert len(out) >= 1


def test_exploit_map():
    findings = [{"rule_id": "s3_public_block", "resource_type": "s3", "resource_id": "b1", "severity": "high"}]
    out = map_findings_to_exploits(findings)
    assert len(out) == 1
    assert "exfiltration" in out[0]["exploit_scenario"].lower()
