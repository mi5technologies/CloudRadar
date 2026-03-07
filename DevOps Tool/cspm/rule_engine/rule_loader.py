"""Load rules from YAML files."""
import os
from pathlib import Path
from typing import Any

import yaml


def load_rules(rules_dir: str | Path) -> list[dict[str, Any]]:
    rules_dir = Path(rules_dir)
    rules = []
    if not rules_dir.exists():
        return rules
    for path in rules_dir.rglob("*.yaml"):
        if path.name.startswith("."):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                if "rules" in data:
                    rules.extend(data["rules"])
                elif "id" in data:
                    rules.append(data)
            elif isinstance(data, list):
                rules.extend(data)
        except Exception:
            continue
    return rules
