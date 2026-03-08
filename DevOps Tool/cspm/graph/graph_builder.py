"""Graph builder and relationship mapper stubs."""
from typing import Any


def build_graph(assets: dict) -> Any:
    from cspm.graph.asset_graph import build_asset_graph
    return build_asset_graph(assets)
