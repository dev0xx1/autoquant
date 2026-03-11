import pandas as pd
from sklearn.linear_model import LogisticRegression

from core.utils.data_util import get_splits, load_dataset
from core.utils.model_util import eval as model_eval


def main():

    # Define model task
    run_id = "appl_dev_23"
    task = "classification"

    # Load dataset
    df = load_dataset(run_id)

    # Feature engineering
    lag_windows = [1, 3, 6, 12, 24]
    rolling_windows = [6, 24]
    for window in lag_windows:
        df[f"ret_{window}"] = df["close"].pct_change(window)
    for window in rolling_windows:
        df[f"ret_mean_{window}"] = df["ret_1"].rolling(window).mean()
        df[f"ret_std_{window}"] = df["ret_1"].rolling(window).std(ddof=0)
    for window in [24]:
        df[f"volume_mean_{window}"] = df["volume"].rolling(window).mean()
        df[f"volume_std_{window}"] = df["volume"].rolling(window).std(ddof=0)
        df[f"volume_z_{window}"] = ((df["volume"] - df[f"volume_mean_{window}"]) / df[f"volume_std_{window}"]).replace(
            [float("inf"), float("-inf")], 0.0
        ).fillna(0.0)
    df["range_ratio"] = (df["high"] - df["low"]) / df["close"]
    feature_names = [f"ret_{window}" for window in lag_windows]
    feature_names += [f"ret_mean_{window}" for window in rolling_windows]
    feature_names += [f"ret_std_{window}" for window in rolling_windows]
    feature_names += ["volume_z_24", "range_ratio"]


    # Target construction
    target_horizon = 24
    frame = df.copy()
    frame["future_ret"] = frame["close"].shift(-target_horizon) / frame["close"] - 1.0
    frame["target"] = (frame["future_ret"] > 0).astype(int)
    frame = frame.dropna(subset=feature_names + ["future_ret"]).reset_index(drop=True)

    # Data split
    x_train, y_train, x_validation, y_validation, x_test, y_test = get_splits(frame, feature_names)

    # Training
    model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
    model.fit(x_train, y_train)

    # Eval
    validation_pred = model.predict(x_validation).astype(int).tolist()
    test_pred = model.predict(x_test).astype(int).tolist()
    validation_actual = y_validation.astype(int).tolist()
    test_actual = y_test.astype(int).tolist()
    metrics = model_eval(task, validation_actual, validation_pred, test_actual, test_pred)

    return metrics