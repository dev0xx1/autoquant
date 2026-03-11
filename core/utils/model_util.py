from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import (
    classification_report,
    explained_variance_score,
    max_error,
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    r2_score,
)

TASK_CLASSIFICATION = "classification"
TASK_REGRESSION = "regression"


def _compute_classification_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> dict[str, float | int | dict[str, float | int]]:
    true_values = [int(value) for value in y_true]
    pred_values = [int(value) for value in y_pred]
    if len(true_values) != len(pred_values):
        raise ValueError("y_true and y_pred must have equal length")
    if not true_values:
        raise ValueError("y_true and y_pred cannot be empty")
    report = classification_report(true_values, pred_values, output_dict=True, zero_division=0)
    class_one = report.get("1", {})
    macro_avg = report.get("macro avg", {})
    weighted_avg = report.get("weighted avg", {})
    n_samples = int(len(true_values))
    y_dist = float(sum(1 for value in true_values if value == 1) / n_samples)
    return {
        "n_samples": n_samples,
        "accuracy": float(report["accuracy"]),
        "precision": float(class_one.get("precision", 0.0)),
        "recall": float(class_one.get("recall", 0.0)),
        "f1": float(class_one.get("f1-score", 0.0)),
        "weighted_f1": float(weighted_avg.get("f1-score", 0.0)),
        "macro_f1": float(macro_avg.get("f1-score", 0.0)),
        "y_dist": y_dist,
        "report": report,
    }


def _compute_regression_metrics(y_true: Sequence[float], y_pred: Sequence[float]) -> dict[str, float]:
    true_values = [float(value) for value in y_true]
    pred_values = [float(value) for value in y_pred]
    if len(true_values) != len(pred_values):
        raise ValueError("y_true and y_pred must have equal length")
    if not true_values:
        raise ValueError("y_true and y_pred cannot be empty")
    mse = mean_squared_error(true_values, pred_values)
    return {
        "n_samples": float(len(true_values)),
        "mae": float(mean_absolute_error(true_values, pred_values)),
        "mse": float(mse),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(true_values, pred_values)),
        "explained_variance": float(explained_variance_score(true_values, pred_values)),
        "median_ae": float(median_absolute_error(true_values, pred_values)),
        "max_error": float(max_error(true_values, pred_values)),
    }


def eval(
    task: str,
    validation_actual: Sequence[float | int],
    validation_pred: Sequence[float | int],
    test_actual: Sequence[float | int],
    test_pred: Sequence[float | int],
) -> dict[str, object]:
    if task not in {TASK_CLASSIFICATION, TASK_REGRESSION}:
        raise ValueError("task must be classification or regression")
    if task == TASK_CLASSIFICATION:
        validation_metrics = _compute_classification_metrics(
            [int(value) for value in validation_actual], [int(value) for value in validation_pred]
        )
        test_metrics = _compute_classification_metrics([int(value) for value in test_actual], [int(value) for value in test_pred])
    else:
        validation_metrics = _compute_regression_metrics(
            [float(value) for value in validation_actual], [float(value) for value in validation_pred]
        )
        test_metrics = _compute_regression_metrics([float(value) for value in test_actual], [float(value) for value in test_pred])
    return {
        "validation": validation_metrics,
        "test": test_metrics,
    }
