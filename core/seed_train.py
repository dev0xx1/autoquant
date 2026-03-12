import pandas as pd
from sklearn.linear_model import LogisticRegression

from core.model_base import AutoQuantModel


class SeedModel(AutoQuantModel):
    def create_features(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        working = frame.copy()
        lag_windows = [1, 3, 6, 12, 24]
        rolling_windows = [6, 24]
        for window in lag_windows:
            working[f"ret_{window}"] = working["close"].pct_change(window)
        for window in rolling_windows:
            working[f"ret_mean_{window}"] = working["ret_1"].rolling(window).mean()
            working[f"ret_std_{window}"] = working["ret_1"].rolling(window).std(ddof=0)
        working["volume_mean_24"] = working["volume"].rolling(24).mean()
        working["volume_std_24"] = working["volume"].rolling(24).std(ddof=0)
        working["volume_z_24"] = ((working["volume"] - working["volume_mean_24"]) / working["volume_std_24"]).replace(
            [float("inf"), float("-inf")], 0.0
        ).fillna(0.0)
        working["range_ratio"] = (working["high"] - working["low"]) / working["close"]
        feature_names = [f"ret_{window}" for window in lag_windows]
        feature_names += [f"ret_mean_{window}" for window in rolling_windows]
        feature_names += [f"ret_std_{window}" for window in rolling_windows]
        feature_names += ["volume_z_24", "range_ratio"]
        target_horizon = 24
        working["future_ret"] = working["close"].shift(-target_horizon) / working["close"] - 1.0
        working["target"] = (working["future_ret"] > 0).astype(int)
        working = working.dropna(subset=feature_names + ["future_ret"]).reset_index(drop=True)
        return working, feature_names

    def get_hyperparameter_candidates(self) -> list[dict[str, object]]:
        return [
            {"c": 0.05, "solver": "lbfgs"},
            {"c": 0.1, "solver": "lbfgs"},
            {"c": 0.5, "solver": "lbfgs"},
            {"c": 1.0, "solver": "lbfgs"},
            {"c": 2.0, "solver": "lbfgs"},
            {"c": 5.0, "solver": "lbfgs"},
        ]

    def fit(self, x_train: pd.DataFrame, y_train: pd.Series, hyperparams: dict[str, object]) -> None:
        estimator = LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
            C=float(hyperparams.get("c", 1.0)),
            solver=str(hyperparams.get("solver", "lbfgs")),
        )
        estimator.fit(x_train, y_train)
        self.artifacts["estimator"] = estimator

    def predict(self, x_test: pd.DataFrame) -> list[float | int]:
        estimator = self.artifacts.get("estimator")
        if estimator is None:
            raise RuntimeError("Missing estimator in artifacts cache; fit must run before predict")
        return estimator.predict(x_test).tolist()
