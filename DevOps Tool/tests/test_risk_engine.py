"""Tests for the Risk Engine and risk_summary report helper.

No cloud credentials or moto required — all inputs are synthetic dicts.
"""
import pytest
from cspm.risk_engine.risk_engine import RiskEngine
from cspm.reporting.risk_summary import risk_summary
from cspm.constants import SEVERITY_MAP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _f(severity: str) -> dict:
    return {"rule_id": f"test.{severity}", "resource_id": "r1", "severity": severity}


# ---------------------------------------------------------------------------
# RiskEngine.compute()
# ---------------------------------------------------------------------------

class TestRiskEngineCompute:
    def test_empty_findings_returns_zero(self):
        engine = RiskEngine()
        score, by_sev = engine.compute([])
        assert score == 0
        assert by_sev == {}

    def test_single_critical_returns_correct_score(self):
        engine = RiskEngine()
        score, by_sev = engine.compute([_f("critical")])
        assert score == SEVERITY_MAP["critical"]
        assert by_sev == {"critical": 1}

    def test_single_high_returns_correct_score(self):
        engine = RiskEngine()
        score, by_sev = engine.compute([_f("high")])
        assert score == SEVERITY_MAP["high"]

    def test_single_medium_returns_correct_score(self):
        engine = RiskEngine()
        score, by_sev = engine.compute([_f("medium")])
        assert score == SEVERITY_MAP["medium"]

    def test_single_low_returns_correct_score(self):
        engine = RiskEngine()
        score, by_sev = engine.compute([_f("low")])
        assert score == SEVERITY_MAP["low"]

    def test_mixed_severities_sum_correctly(self):
        engine = RiskEngine()
        findings = [_f("critical"), _f("high"), _f("medium"), _f("low")]
        score, by_sev = engine.compute(findings)
        expected = sum(SEVERITY_MAP[s] for s in ["critical", "high", "medium", "low"])
        assert score == expected

    def test_multiple_same_severity_accumulates(self):
        engine = RiskEngine()
        findings = [_f("critical")] * 3
        score, by_sev = engine.compute(findings)
        assert score == SEVERITY_MAP["critical"] * 3
        assert by_sev["critical"] == 3

    def test_by_severity_counts_are_accurate(self):
        engine = RiskEngine()
        findings = [_f("critical"), _f("critical"), _f("high"), _f("medium")]
        _, by_sev = engine.compute(findings)
        assert by_sev["critical"] == 2
        assert by_sev["high"] == 1
        assert by_sev["medium"] == 1
        assert by_sev.get("low", 0) == 0

    def test_critical_higher_impact_than_low(self):
        """Critical should always produce a more negative score than low."""
        engine = RiskEngine()
        score_crit, _ = engine.compute([_f("critical")])
        score_low, _  = engine.compute([_f("low")])
        assert score_crit < score_low

    def test_unknown_severity_does_not_crash(self):
        """Findings with an unrecognised severity should not raise."""
        engine = RiskEngine()
        findings = [{"rule_id": "x", "resource_id": "r", "severity": "unknown_level"}]
        score, by_sev = engine.compute(findings)
        assert isinstance(score, (int, float))

    def test_missing_severity_key_does_not_crash(self):
        """Findings without a severity key at all should not raise."""
        engine = RiskEngine()
        findings = [{"rule_id": "x", "resource_id": "r"}]
        score, by_sev = engine.compute(findings)
        assert isinstance(score, (int, float))

    def test_severity_case_insensitive(self):
        """Severity matching should be case-insensitive (CRITICAL == critical)."""
        engine = RiskEngine()
        score_lower, _ = engine.compute([_f("critical")])
        score_upper, _ = engine.compute([{"severity": "CRITICAL", "resource_id": "r"}])
        assert score_lower == score_upper

    def test_returns_tuple_of_two(self):
        engine = RiskEngine()
        result = engine.compute([_f("high")])
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_score_is_numeric(self):
        engine = RiskEngine()
        score, _ = engine.compute([_f("high")])
        assert isinstance(score, (int, float))

    def test_by_severity_is_dict(self):
        engine = RiskEngine()
        _, by_sev = engine.compute([_f("high")])
        assert isinstance(by_sev, dict)

    def test_large_finding_set_performance(self):
        """100 findings should complete without error."""
        engine = RiskEngine()
        findings = [_f("medium")] * 100
        score, by_sev = engine.compute(findings)
        assert by_sev["medium"] == 100


# ---------------------------------------------------------------------------
# risk_summary() report helper
# ---------------------------------------------------------------------------

class TestRiskSummary:
    def _scan_result(self, score=42, critical=1, high=2, medium=3, low=4) -> dict:
        return {
            "risk_score": score,
            "by_severity": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            },
        }

    def test_output_contains_risk_score(self):
        out = risk_summary(self._scan_result(score=42))
        assert "42" in out

    def test_output_contains_severity_counts(self):
        out = risk_summary(self._scan_result(critical=3, high=5))
        assert "3" in out
        assert "5" in out

    def test_output_is_string(self):
        out = risk_summary(self._scan_result())
        assert isinstance(out, str)

    def test_empty_scan_result_does_not_crash(self):
        out = risk_summary({})
        assert isinstance(out, str)

    def test_zero_score_renders(self):
        out = risk_summary(self._scan_result(score=0))
        assert "0" in out
