"""Build asset relationship graph."""
import networkx as nx
from typing import Any


def build_asset_graph(assets: dict[str, list[dict]]) -> Any:
    G = nx.DiGraph()
    for rtype, items in assets.items():
        for a in items:
            nid = a.get("id") or a.get("name") or a.get("arn")
            if nid:
                G.add_node(nid, type=rtype, **a)
    return G
