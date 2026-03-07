"""Save and load scan snapshots."""
import json
from pathlib import Path
from datetime import datetime
from typing import Any


class SnapshotManager:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        cloud: str,
        account_id: str,
        region: str,
        assets: dict[str, list[dict]],
        findings: list[dict],
        catalog: list[dict],
    ) -> str:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_id = f"{cloud}_{account_id}_{region}_{ts}"
        path = self.base_dir / f"{snapshot_id}.json"
        data = {
            "snapshot_id": snapshot_id,
            "cloud": cloud,
            "account_id": account_id,
            "region": region,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "assets": assets,
            "findings": findings,
            "catalog": catalog,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return snapshot_id

    def load(self, snapshot_id: str) -> dict | None:
        path = self.base_dir / f"{snapshot_id}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_snapshots(self, cloud: str | None = None) -> list[dict]:
        out = []
        for path in self.base_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if cloud and data.get("cloud") != cloud:
                    continue
                out.append({
                    "snapshot_id": data.get("snapshot_id"),
                    "cloud": data.get("cloud"),
                    "account_id": data.get("account_id"),
                    "region": data.get("region"),
                    "timestamp": data.get("timestamp"),
                })
            except Exception:
                continue
        out.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return out

    def get_latest(self, cloud: str | None = None, account_id: str | None = None) -> dict | None:
        snapshots = self.list_snapshots(cloud=cloud)
        if account_id:
            snapshots = [s for s in snapshots if s.get("account_id") == account_id]
        if not snapshots:
            return None
        return self.load(snapshots[0]["snapshot_id"])
