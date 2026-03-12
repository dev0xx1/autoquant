from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
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


def walk_forward(
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    training_size_days: int,
    test_size_days: int = 7,
    first_test_at_start: bool = False,
):
    test_start_ts = start_ts if first_test_at_start else start_ts + pd.Timedelta(days=training_size_days)
    while test_start_ts < end_ts:
        test_end_ts = min(test_start_ts + pd.Timedelta(days=test_size_days), end_ts + pd.Timedelta(microseconds=1))
        train_start_ts = test_start_ts - pd.Timedelta(days=training_size_days)
        yield train_start_ts, test_start_ts, test_end_ts
        test_start_ts = test_end_ts


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
    train_actual: Sequence[float | int],
    train_pred: Sequence[float | int],
    validation_actual: Sequence[float | int],
    validation_pred: Sequence[float | int],
) -> dict[str, object]:
    if task not in {TASK_CLASSIFICATION, TASK_REGRESSION}:
        raise ValueError("task must be classification or regression")
    if task == TASK_CLASSIFICATION:
        train_metrics = _compute_classification_metrics([int(value) for value in train_actual], [int(value) for value in train_pred])
        validation_metrics = _compute_classification_metrics(
            [int(value) for value in validation_actual], [int(value) for value in validation_pred]
        )
    else:
        train_metrics = _compute_regression_metrics([float(value) for value in train_actual], [float(value) for value in train_pred])
        validation_metrics = _compute_regression_metrics(
            [float(value) for value in validation_actual], [float(value) for value in validation_pred]
        )
    return {
        "train": train_metrics,
        "validation": validation_metrics,
    }
