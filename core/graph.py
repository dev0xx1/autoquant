from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
from networkx.readwrite import json_graph

from core.constants import LINEAGE_GRAPH_JSON
from core.io_util import read_json, write_json


def _graph_path(run_dir: Path) -> Path:
    return run_dir / LINEAGE_GRAPH_JSON


def save_graph(run_dir: Path, graph: nx.DiGraph) -> None:
    write_json(_graph_path(run_dir), json_graph.node_link_data(graph))


def load_graph(run_dir: Path) -> nx.DiGraph:
    path = _graph_path(run_dir)
    if not path.exists():
        graph = nx.DiGraph()
        save_graph(run_dir, graph)
        return graph
    payload = read_json(path)
    graph = json_graph.node_link_graph(payload, directed=True, multigraph=False)
    if not isinstance(graph, nx.DiGraph):
        graph = nx.DiGraph(graph)
    return graph


def init_graph(run_dir: Path) -> None:
    save_graph(run_dir, nx.DiGraph())


def upsert_model_node(run_dir: Path, model_id: str, generation: int, parent_id: str | None, created_at_utc: str) -> None:
    graph = load_graph(run_dir)
    graph.add_node(model_id, model_id=model_id, generation=generation, parent_id=parent_id, created_at_utc=created_at_utc)
    if parent_id:
        graph.add_edge(parent_id, model_id, parent_id=parent_id, child_id=model_id)
    save_graph(run_dir, graph)


def update_model_objective(
    run_dir: Path,
    model_id: str,
    objective_function: str,
    objective_value: float,
    metrics: dict[str, float],
) -> None:
    graph = load_graph(run_dir)
    if model_id not in graph:
        graph.add_node(model_id, model_id=model_id)
    node_data = dict(graph.nodes[model_id])
    node_data.update(metrics)
    node_data["objective_function"] = objective_function
    node_data["objective_value"] = objective_value
    graph.nodes[model_id].update(node_data)
    for parent_id, _, edge_data in graph.in_edges(model_id, data=True):
        parent_value = graph.nodes[parent_id].get("objective_value")
        edge_data["objective_function"] = objective_function
        edge_data["child_objective"] = objective_value
        edge_data["parent_objective"] = parent_value
        edge_data["objective_delta"] = objective_value - float(parent_value) if parent_value is not None else None
    save_graph(run_dir, graph)


def get_frontier_nodes(graph: nx.DiGraph) -> list[str]:
    return [str(node) for node in graph.nodes if graph.out_degree(node) == 0]


def get_exploit_candidates(run_dir: Path, limit: int = 5) -> list[dict[str, Any]]:
    graph = load_graph(run_dir)
    frontier = get_frontier_nodes(graph)
    rows = [
        {
            "model_id": str(node),
            "objective_value": float(graph.nodes[node].get("objective_value") or 0.0),
            "generation": int(graph.nodes[node].get("generation") or 0),
            "out_degree": int(graph.out_degree(node)),
            "in_degree": int(graph.in_degree(node)),
            "descendants": len(nx.descendants(graph, node)),
        }
        for node in frontier
    ]
    rows.sort(key=lambda row: (row["objective_value"], row["descendants"]), reverse=True)
    return rows[: max(limit, 0)]


def get_explore_candidates(run_dir: Path, limit: int = 5) -> list[dict[str, Any]]:
    graph = load_graph(run_dir)
    rows = [
        {
            "model_id": str(node),
            "objective_value": float(graph.nodes[node].get("objective_value") or 0.0),
            "generation": int(graph.nodes[node].get("generation") or 0),
            "out_degree": int(graph.out_degree(node)),
            "in_degree": int(graph.in_degree(node)),
            "descendants": len(nx.descendants(graph, node)),
            "ancestors": len(nx.ancestors(graph, node)),
        }
        for node in graph.nodes
    ]
    rows.sort(key=lambda row: (row["descendants"], row["out_degree"], row["ancestors"], -row["objective_value"]))
    return rows[: max(limit, 0)]


def get_parent_candidates(run_dir: Path, total: int, exploit_ratio: float = 0.7) -> dict[str, list[dict[str, Any]]]:
    total_count = max(total, 0)
    exploit_count = min(total_count, max(0, int(round(total_count * exploit_ratio))))
    explore_count = max(0, total_count - exploit_count)
    return {
        "exploit": get_exploit_candidates(run_dir, exploit_count),
        "explore": get_explore_candidates(run_dir, explore_count),
    }
