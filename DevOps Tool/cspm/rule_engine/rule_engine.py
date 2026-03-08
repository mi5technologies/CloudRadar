"""Evaluate assets against loaded rules."""
from typing import Any


class RuleEngine:
    def __init__(self, rules: list[dict[str, Any]]):
        self.rules = rules

    def evaluate(self, assets: dict[str, list[dict]]) -> list[dict[str, Any]]:
        findings = []
        for rule in self.rules:
            rule_id = rule.get("id", "")
            resource_type = rule.get("resource_type", "")
            asset_list = assets.get(resource_type, [])
            for asset in asset_list:
                if self._matches(asset, rule) and not self._compliant(asset, rule):
                    findings.append({
                        "rule_id": rule_id,
                        "severity": rule.get("severity", "medium"),
                        "category": rule.get("category", ""),
                        "title": rule.get("title", rule_id),
                        "description": rule.get("description", ""),
                        "resource_type": resource_type,
                        "resource_id": asset.get("id") or asset.get("name") or str(asset.get("arn", "")),
                        "account_id": asset.get("account_id"),
                        "asset": asset,
                        "required": rule.get("required", False),
                    })
        return findings

    def _matches(self, asset: dict, rule: dict) -> bool:
        rt = rule.get("resource_type", "")
        at = asset.get("type", "")
        if rt and at and rt != at:
            return False
        return True

    def _compliant(self, asset: dict, rule: dict) -> bool:
        condition = rule.get("condition")
        if not condition:
            return True
        op = condition.get("op")
        key = condition.get("key")
        expected = condition.get("value")
        if not key:
            return True
        actual = asset.get(key)
        if op == "equals":
            return actual == expected
        if op == "not_equals":
            return actual != expected
        if op == "true":
            return actual is True
        if op == "false":
            return actual is False
        if op == "in":
            return actual in (expected or [])
        if op == "not_in":
            return actual not in (expected or [])
        if op == "gt":
            if actual is None:
                return True
            try:
                return float(actual) <= float(expected)
            except (TypeError, ValueError):
                return True
        return True
