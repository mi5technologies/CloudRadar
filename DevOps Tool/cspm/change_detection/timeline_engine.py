"""Timeline of changes across snapshots."""
from typing import Any


class TimelineEngine:
    def __init__(self, snapshot_manager):
        self.snapshot_manager = snapshot_manager

    def get_timeline(
        self,
        cloud: str | None = None,
        account_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        snapshots = self.snapshot_manager.list_snapshots(cloud=cloud)
        if account_id:
            snapshots = [s for s in snapshots if s.get("account_id") == account_id]
        return snapshots[:limit]
