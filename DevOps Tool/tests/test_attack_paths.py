"""Tests for attack path (stub)."""
from cspm.attack_path import find_attack_paths
from cspm.graph import build_asset_graph


def test_attack_paths_empty():
    paths = find_attack_paths(build_asset_graph({}), [])
    assert paths == []
