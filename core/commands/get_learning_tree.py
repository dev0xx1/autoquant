from __future__ import annotations

from typing import Any

import networkx as nx

from core.constants import EXPERIMENTS_CSV, MODELS_CSV
from core.graph import load_graph
from core.paths import run_dir
from core.utils.storage import get_model_map, parse_experiment_rows, read_csv

from .shared import load_run_settings, read_run_meta


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
            exp_map[row.model_id] = row.model_dump(mode="json")
    return exp_map


def get_learning_tree(run_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    settings = load_run_settings(run_id)
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
        if not node_attrs.get("parent_id") and model and model.parent_id:
            node_attrs["parent_id"] = model.parent_id
        node_attrs["model"] = model.model_dump(mode="json") if model else None
        node_attrs["experiment"] = experiment
        enriched_graph.nodes[node_id].update(node_attrs)
    return {
        "run_id": run_id,
        "objective_function": settings.objective_function,
        "task": settings.task,
        "graph": nx.node_link_data(enriched_graph),
    }