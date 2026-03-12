from __future__ import annotations

import io
import json
from typing import Any

import networkx as nx

from core.constants import EXPERIMENTS_CSV, MODELS_CSV
from core.graph import load_graph
from core.paths import run_dir
from core.utils.metrics_util import extract_validation_metrics
from core.utils.storage import get_model_map, parse_experiment_rows, read_csv

from .shared import read_run_meta


def _get_experiment_map(run_id: str) -> dict[str, dict[str, Any]]:
    meta = read_run_meta(run_id)
    rows = parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV))
    filtered = [row for row in rows if row.ticker == meta.ticker and row.from_date == meta.from_date and row.to_date == meta.to_date]
    exp_map: dict[str, dict[str, Any]] = {}
    for row in filtered:
        previous = exp_map.get(row.model_id)
        previous_ts = (previous["finished_at_utc"] or previous["started_at_utc"] or "") if previous else ""
        current_ts = row.finished_at_utc or row.started_at_utc or ""
        if previous is None or current_ts > previous_ts:
            payload = row.model_dump(mode="json")
            payload["metrics"] = extract_validation_metrics(payload.get("metrics"))
            exp_map[row.model_id] = payload
    return exp_map


def _to_network_text(graph: nx.Graph) -> str:
    relabeled = nx.DiGraph() if graph.is_directed() else nx.Graph()
    labels = {
        node_id: f"{node_id} | attrs={json.dumps(dict(graph.nodes[node_id]), ensure_ascii=True, sort_keys=True, default=str)}"
        for node_id in graph.nodes
    }
    relabeled.add_nodes_from(labels.values())
    relabeled.add_edges_from((labels[source], labels[target]) for source, target in graph.edges())
    buffer = io.StringIO()
    nx.write_network_text(relabeled, path=buffer, ascii_only=True)
    return buffer.getvalue()


def get_learning_tree(run_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    target_run_dir = run_dir(run_id)
    graph = load_graph(target_run_dir)
    model_map = get_model_map(target_run_dir, MODELS_CSV)
    experiment_map = _get_experiment_map(run_id)
    enriched_graph = graph.copy()
    for node_id in list(enriched_graph.nodes):
        model_id = str(node_id)
        model = model_map.get(model_id)
        experiment = experiment_map.get(model_id)
        node_attrs = dict(enriched_graph.nodes[node_id])
        node_attrs["metrics"] = extract_validation_metrics(node_attrs.get("metrics"))
        if not node_attrs.get("parent_id") and model and model.parent_id:
            node_attrs["parent_id"] = model.parent_id
        node_attrs["model"] = model.model_dump(mode="json") if model else None
        node_attrs["experiment"] = experiment
        enriched_graph.nodes[node_id].update(node_attrs)
    return {
        "run_id": run_id,
        "objective_function": meta.objective_function,
        "task": meta.task,
        "graph": _to_network_text(enriched_graph),
    }