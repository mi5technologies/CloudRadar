"""Tests for rule engine evaluate() covering all supported operators."""
import os
import pytest
from cspm.rule_engine import load_rules, RuleEngine

RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "cspm", "rules")


def _engine(*rules):
    return RuleEngine(list(rules))


def _rule(op, key="flag", value=None, resource_type="s3"):
    r = {"id": f"test_{op}", "resource_type": resource_type, "condition": {"op": op, "key": key}}
    if value is not None:
        r["condition"]["value"] = value
    return r


# ---------------------------------------------------------------------------
# load_rules smoke test
# ---------------------------------------------------------------------------

def test_load_rules_returns_list():
    rules = load_rules(RULES_DIR)
    assert isinstance(rules, list)
    assert len(rules) >= 1


# ---------------------------------------------------------------------------
# op: true / false
# ---------------------------------------------------------------------------

def test_op_true_compliant():
    engine = _engine(_rule("true"))
    assert engine.evaluate({"s3": [{"id": "b1", "flag": True}]}) == []


def test_op_true_non_compliant():
    engine = _engine(_rule("true"))
    findings = engine.evaluate({"s3": [{"id": "b1", "flag": False}]})
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "test_true"


def test_op_false_compliant():
    engine = _engine(_rule("false"))
    assert engine.evaluate({"s3": [{"id": "b1", "flag": False}]}) == []


def test_op_false_non_compliant():
    engine = _engine(_rule("false"))
    findings = engine.evaluate({"s3": [{"id": "b1", "flag": True}]})
    assert len(findings) == 1


# ---------------------------------------------------------------------------
# op: equals / not_equals
# ---------------------------------------------------------------------------

def test_op_equals_compliant():
    engine = _engine(_rule("equals", value="enabled"))
    assert engine.evaluate({"s3": [{"id": "b1", "flag": "enabled"}]}) == []


def test_op_equals_non_compliant():
    engine = _engine(_rule("equals", value="enabled"))
    findings = engine.evaluate({"s3": [{"id": "b1", "flag": "disabled"}]})
    assert len(findings) == 1


def test_op_not_equals_compliant():
    engine = _engine(_rule("not_equals", value="disabled"))
    assert engine.evaluate({"s3": [{"id": "b1", "flag": "enabled"}]}) == []


def test_op_not_equals_non_compliant():
    engine = _engine(_rule("not_equals", value="disabled"))
    findings = engine.evaluate({"s3": [{"id": "b1", "flag": "disabled"}]})
    assert len(findings) == 1


# ---------------------------------------------------------------------------
# op: in / not_in
# ---------------------------------------------------------------------------

def test_op_in_compliant():
    engine = _engine(_rule("in", value=["a", "b"]))
    assert engine.evaluate({"s3": [{"id": "b1", "flag": "a"}]}) == []


def test_op_in_non_compliant():
    engine = _engine(_rule("in", value=["a", "b"]))
    findings = engine.evaluate({"s3": [{"id": "b1", "flag": "c"}]})
    assert len(findings) == 1


def test_op_not_in_compliant():
    engine = _engine(_rule("not_in", value=["bad1", "bad2"]))
    assert engine.evaluate({"s3": [{"id": "b1", "flag": "good"}]}) == []


def test_op_not_in_non_compliant():
    engine = _engine(_rule("not_in", value=["bad1", "bad2"]))
    findings = engine.evaluate({"s3": [{"id": "b1", "flag": "bad1"}]})
    assert len(findings) == 1


# ---------------------------------------------------------------------------
# op: gt  (triggers when actual > expected threshold)
# ---------------------------------------------------------------------------

def test_op_gt_compliant():
    """actual (5) <= expected (10) → compliant (no finding)."""
    engine = _engine(_rule("gt", value=10))
    assert engine.evaluate({"s3": [{"id": "b1", "flag": 5}]}) == []


def test_op_gt_non_compliant():
    """actual (15) > expected (10) → non-compliant (finding generated)."""
    engine = _engine(_rule("gt", value=10))
    findings = engine.evaluate({"s3": [{"id": "b1", "flag": 15}]})
    assert len(findings) == 1


# ---------------------------------------------------------------------------
# Finding metadata
# ---------------------------------------------------------------------------

def test_finding_contains_resource_id():
    engine = _engine(_rule("false"))
    findings = engine.evaluate({"s3": [{"id": "my-bucket", "flag": True}]})
    assert findings[0]["resource_id"] == "my-bucket"


def test_no_finding_when_asset_list_empty():
    engine = _engine(_rule("false"))
    assert engine.evaluate({"s3": []}) == []


def test_multiple_assets_only_non_compliant_flagged():
    engine = _engine(_rule("true"))
    assets = {"s3": [
        {"id": "good", "flag": True},
        {"id": "bad", "flag": False},
    ]}
    findings = engine.evaluate(assets)
    assert len(findings) == 1
    assert findings[0]["resource_id"] == "bad"
