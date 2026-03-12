from __future__ import annotations

from typing import Mapping


def extract_validation_metrics(metrics: object) -> dict[str, object] | None:
    if not isinstance(metrics, dict):
        return None
    validation = metrics.get("validation")
    if isinstance(validation, dict):
        return validation
    return metrics


def objective_value(task: str, objective_function: str, metrics: Mapping[str, object]) -> float:
    if task == "classification":
        if objective_function == "accuracy":
            return float(metrics["accuracy"])
        if objective_function == "f1":
            return float(metrics["f1"])
        if objective_function == "macro_f1":
            return float(metrics["macro_f1"])
        return float(metrics["weighted_f1"])
    return float(metrics["r2"])
