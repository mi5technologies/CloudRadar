"""Attack path analysis engine."""
from __future__ import annotations

from typing import Any

from cspm.attack_path.path_analyzer import analyze_paths
from cspm.utils.logger import get_logger

logger = get_logger(__name__)


def find_attack_paths(graph: Any, findings: list[dict]) -> list[dict]:
    """Find attack paths using the asset graph and findings list.

    *graph* may be a :class:`networkx.DiGraph` produced by the graph builder,
    a plain ``dict`` of assets (as returned by the scan controller), or ``None``.
    The underlying :func:`~cspm.attack_path.path_analyzer.analyze_paths` function
    accepts a dict of assets; we extract it from the graph when possible.
    """
    assets: dict[str, Any] = {}

    if graph is None:
        pass
    elif isinstance(graph, dict):
        assets = graph
    else:
        # Try to pull the raw assets dict off a networkx-style graph object
        try:
            assets = graph.graph.get("assets", {})
        except Exception:
            pass

    try:
        return analyze_paths(assets=assets, findings=findings)
    except Exception as exc:  # noqa: BLE001
        logger.error("find_attack_paths failed: %s", exc)
        return []
