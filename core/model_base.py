from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import time

import pandas as pd

from core.utils.data_util import get_splits, load_dataset
from core.utils.model_util import eval as model_eval
from core.utils.model_util import walk_forward


class AutoQuantModel(ABC):
    def __init__(
        self,
        run_id: str,
        task: str,
        model_id: str | None = None,
        model_path: str | None = None,
    ):
        self.run_id = run_id
        self.task = task
        self.model_id = model_id or self._derive_model_id(model_path)
        self.artifacts: dict[str, object] = {}
        self.best_hyperparams: dict[str, object] = {}
        self.train_metrics: dict[str, object] | None = None

    def _derive_model_id(self, model_path: str | None) -> str:
        if not model_path:
            return "unknown"
        stem = Path(model_path).stem.strip()
        return stem or "unknown"

    def prepare_data(self) -> pd.DataFrame:
        frame = load_dataset(self.run_id)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).reset_index(drop=True)
        if frame.empty:
            raise RuntimeError("Dataset is empty")
        min_ts = frame["timestamp"].min()
        max_ts = frame["timestamp"].max()
        if (max_ts - min_ts) < pd.Timedelta(days=30):
            raise RuntimeError("Dataset must span at least 30 days")
        return frame

    @abstractmethod
    def create_features(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        raise NotImplementedError

    def split_data(self, frame: pd.DataFrame, feature_names: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
        x_train, y_train, x_validation, y_validation = get_splits(frame, feature_names)
        split_idx = len(x_train)
        train_frame = frame.iloc[:split_idx].reset_index(drop=True)
        validation_frame = frame.iloc[split_idx:].reset_index(drop=True)
        if len(train_frame) != len(y_train) or len(validation_frame) != len(y_validation):
            raise RuntimeError("Split alignment error")
        return train_frame, validation_frame

    def _get_attempted_window_count(
        self,
        frame: pd.DataFrame,
        training_size_days: int,
        test_size_days: int,
        first_test_at_start: bool = False,
    ) -> int:
        if frame.empty:
            return 0
        start_ts = frame["timestamp"].min()
        end_ts = frame["timestamp"].max()
        return sum(
            1
            for _ in walk_forward(
                start_ts=start_ts,
                end_ts=end_ts,
                training_size_days=training_size_days,
                test_size_days=test_size_days,
                first_test_at_start=first_test_at_start,
            )
        )

    def _enforce_min_windows(
        self,
        partition_name: str,
        frame: pd.DataFrame,
        training_size_days: int,
        test_size_days: int,
        min_windows: int,
        first_test_at_start: bool = False,
    ) -> None:
        attempted = self._get_attempted_window_count(
            frame=frame,
            training_size_days=training_size_days,
            test_size_days=test_size_days,
            first_test_at_start=first_test_at_start,
        )
        if attempted < min_windows:
            raise RuntimeError(
                f"{partition_name} requires at least {min_windows} walk-forward windows but got {attempted} "
                f"for training_size_days={training_size_days} test_size_days={test_size_days}"
            )

    def validate_model(
        self,
        train_frame: pd.DataFrame,
        validation_frame: pd.DataFrame,
        training_size_days: int,
        test_size_days: int,
    ) -> None:
        if training_size_days <= 0 or test_size_days <= 0:
            raise RuntimeError("training_size_days and test_size_days must be > 0")
        validation_start = validation_frame["timestamp"].min()
        lookback_start = validation_start - pd.Timedelta(days=training_size_days)
        if train_frame["timestamp"].min() > lookback_start:
            raise RuntimeError(
                f"Train partition does not provide enough lookback for validation: need data from {lookback_start} "
                f"but train starts at {train_frame['timestamp'].min()}"
            )
        self._enforce_min_windows(
            partition_name="train",
            frame=train_frame,
            training_size_days=training_size_days,
            test_size_days=test_size_days,
            min_windows=4,
        )
        self._enforce_min_windows(
            partition_name="validation",
            frame=validation_frame,
            training_size_days=training_size_days,
            test_size_days=test_size_days,
            min_windows=2,
            first_test_at_start=True,
        )

    def evaluate(
        self,
        train_actual: list[float | int],
        train_pred: list[float | int],
        validation_actual: list[float | int],
        validation_pred: list[float | int],
    ) -> dict[str, object]:
        return model_eval(self.task, train_actual, train_pred, validation_actual, validation_pred)

    def get_hyperparameter_candidates(self) -> list[dict[str, object]]:
        return [{}]

    @abstractmethod
    def fit(
        self,
        x_train: pd.DataFrame,
        y_train: pd.Series,
        hyperparams: dict[str, object],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def predict(self, x_test: pd.DataFrame) -> list[float | int]:
        raise NotImplementedError

    def _selection_score(self, metrics: dict[str, object]) -> float:
        if self.task == "classification":
            return float(metrics["weighted_f1"])
        return float(metrics["r2"])

    def _walk_forward_predict(
        self,
        frame: pd.DataFrame,
        feature_names: list[str],
        training_size_days: int,
        test_size_days: int,
        hyperparams: dict[str, object],
        test_range_start_ts: pd.Timestamp | None = None,
        test_range_end_ts: pd.Timestamp | None = None,
    ) -> tuple[list[float | int], list[float | int]]:
        if frame.empty:
            raise RuntimeError("Partition is empty")
        if test_range_start_ts is not None and test_range_end_ts is not None:
            start_ts = test_range_start_ts
            end_ts = test_range_end_ts
            first_test_at_start = True
        else:
            start_ts = frame["timestamp"].min()
            end_ts = frame["timestamp"].max()
            first_test_at_start = False
        actual: list[float | int] = []
        pred: list[float | int] = []
        for train_start_ts, test_start_ts, test_end_ts in walk_forward(
            start_ts=start_ts,
            end_ts=end_ts,
            training_size_days=training_size_days,
            test_size_days=test_size_days,
            first_test_at_start=first_test_at_start,
        ):
            train_window = frame[(frame["timestamp"] >= train_start_ts) & (frame["timestamp"] < test_start_ts)]
            test_window = frame[(frame["timestamp"] >= test_start_ts) & (frame["timestamp"] < test_end_ts)]
            if train_window.empty or test_window.empty:
                continue
            x_train = train_window[feature_names]
            y_train = train_window["target"]
            x_test = test_window[feature_names]
            y_test = test_window["target"]
            if self.task == "classification" and y_train.nunique() < 2:
                continue
            self.artifacts = {}
            self.fit(x_train, y_train, hyperparams)
            y_pred = list(self.predict(x_test))
            if len(y_pred) != len(x_test):
                raise RuntimeError("predict output length must match x_test length")
            if self.task == "classification":
                pred.extend([int(value) for value in y_pred])
                actual.extend(y_test.astype(int).tolist())
            else:
                pred.extend([float(value) for value in y_pred])
                actual.extend(y_test.astype(float).tolist())
        if not pred:
            raise RuntimeError("Walk-forward produced no predictions")
        return actual, pred

    def _metrics_from_predictions(
        self,
        actual: list[float | int],
        pred: list[float | int],
    ) -> dict[str, object]:
        paired_eval = self.evaluate(actual, pred, actual, pred)
        metrics = paired_eval["train"]
        if not isinstance(metrics, dict):
            raise RuntimeError("Invalid metrics payload from evaluate")
        return metrics

    def train(
        self,
        frame: pd.DataFrame,
        feature_names: list[str],
        training_size_days: int,
        test_size_days: int,
        train_time_limit_minutes: float,
    ) -> None:
        if train_time_limit_minutes <= 0:
            raise RuntimeError("train_time_limit_minutes must be > 0")
        candidates = self.get_hyperparameter_candidates() or [{}]
        best_params: dict[str, object] | None = None
        best_metrics: dict[str, object] | None = None
        best_score: float | None = None
        errors: list[str] = []
        start_time = time.monotonic()
        train_time_limit_seconds = train_time_limit_minutes * 60.0
        attempted_count = 0
        for candidate in candidates:
            if attempted_count > 0 and (time.monotonic() - start_time) >= train_time_limit_seconds:
                break
            candidate_params = dict(candidate or {})
            attempted_count += 1
            try:
                actual, pred = self._walk_forward_predict(
                    frame=frame,
                    feature_names=feature_names,
                    training_size_days=training_size_days,
                    test_size_days=test_size_days,
                    hyperparams=candidate_params,
                )
                metrics = self._metrics_from_predictions(actual, pred)
                score = self._selection_score(metrics)
            except Exception as exc:
                errors.append(str(exc))
                continue
            if best_score is None or score > best_score:
                best_score = score
                best_params = candidate_params
                best_metrics = metrics
        if best_params is None or best_metrics is None:
            joined = "; ".join(errors) if errors else "no valid candidates"
            raise RuntimeError(f"Hyperparameter search failed: {joined}")
        self.best_hyperparams = best_params
        train_metrics = dict(best_metrics)
        train_metrics["hyperparam_candidates_attempted"] = attempted_count
        train_metrics["hyperparam_search_elapsed_minutes"] = (time.monotonic() - start_time) / 60.0
        train_metrics["train_time_limit_minutes"] = float(train_time_limit_minutes)
        self.train_metrics = train_metrics

    def run(
        self,
        training_size_days: int = 30,
        test_size_days: int = 7,
        train_time_limit_minutes: float = 5.0,
    ) -> dict[str, object]:
        frame = self.prepare_data()
        prepared, feature_names = self.create_features(frame)
        train_frame, validation_frame = self.split_data(prepared, feature_names)
        self.validate_model(train_frame, validation_frame, training_size_days, test_size_days)
        self.train(train_frame, feature_names, training_size_days, test_size_days, train_time_limit_minutes)
        if self.train_metrics is None:
            raise RuntimeError("Training search did not produce metrics")
        combined_frame = pd.concat([train_frame, validation_frame], ignore_index=True)
        validation_start = validation_frame["timestamp"].min()
        validation_end = validation_frame["timestamp"].max()
        validation_actual, validation_pred = self._walk_forward_predict(
            combined_frame,
            feature_names,
            training_size_days,
            test_size_days,
            self.best_hyperparams,
            test_range_start_ts=validation_start,
            test_range_end_ts=validation_end,
        )
        validation_metrics = self._metrics_from_predictions(validation_actual, validation_pred)
        train_metrics = dict(self.train_metrics)
        train_metrics["selected_hyperparams"] = dict(self.best_hyperparams)
        return {"train": train_metrics, "validation": validation_metrics}
