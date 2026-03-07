"""Simple persistence for snapshots (file-based)."""
from pathlib import Path
import json
from typing import Any


def get_db(db_url: str | None = None):
    """Placeholder for future DB; snapshots are file-based."""
    return None


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
