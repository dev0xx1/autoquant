from __future__ import annotations

import ast
import math
from pathlib import Path

DISALLOWED_NAMES = {"eval", "exec", "compile", "__import__", "input", "globals", "locals", "vars"}
DISALLOWED_ATTRS = {"system", "popen", "run", "Popen", "fork", "remove", "unlink", "rmtree"}
REQUIRED_OUTPUT_KEYS = ("validation", "test")


def _validate_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DISALLOWED_NAMES:
                raise ValueError(f"Disallowed call: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in DISALLOWED_ATTRS:
                raise ValueError(f"Disallowed call attribute: {node.func.attr}")


def _compile_model(path: Path) -> object:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    _validate_ast(tree)
    return compile(tree, str(path), "exec")


def _sample_ohlcv_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    close = 100.0
    for i in range(320):
        drift = 0.0004 if i % 7 in {0, 1, 2, 3} else -0.00025
        wave = math.sin(i / 9.0) * 0.0012
        noise = math.cos(i / 5.0) * 0.0006
        ret = drift + wave + noise
        open_price = close
        close = max(1.0, close * (1.0 + ret))
        high = max(open_price, close) * (1.0 + 0.001 + abs(noise))
        low = min(open_price, close) * (1.0 - 0.001 - abs(noise))
        volume = 50000 + (i % 30) * 750 + int(abs(math.sin(i / 8.0)) * 3500)
        rows.append(
            {
                "timestamp": f"2026-01-{1 + (i // 24):02d}T{i % 24:02d}:00:00+00:00",
                "ticker": "SAMPLE",
                "open": f"{open_price:.6f}",
                "high": f"{high:.6f}",
                "low": f"{low:.6f}",
                "close": f"{close:.6f}",
                "volume": str(volume),
            }
        )
    return rows


def _read_train_output(payload: object, expected_task: str | None = None) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("train.py main() must return a dict")
    output: dict[str, object] = dict(payload)
    for key in REQUIRED_OUTPUT_KEYS:
        if key not in payload:
            raise ValueError(f"Missing train output key: {key}")
    validation_metrics = payload["validation"]
    test_metrics = payload["test"]
    if not isinstance(validation_metrics, dict) or not isinstance(test_metrics, dict):
        raise ValueError("validation and test must be dicts")
    classification_keys = {"accuracy", "precision", "recall", "f1", "weighted_f1", "macro_f1", "y_dist", "report", "n_samples"}
    regression_keys = {"mae", "mse", "rmse", "r2", "explained_variance", "median_ae", "max_error", "n_samples"}
    required_keys: set[str] | None = None
    if expected_task == "classification":
        required_keys = classification_keys
    elif expected_task == "regression":
        required_keys = regression_keys
    if required_keys is not None:
        for section_name, section_metrics in [("validation", validation_metrics), ("test", test_metrics)]:
            missing = [key for key in required_keys if key not in section_metrics]
            if missing:
                raise ValueError(f"Missing {section_name} metric keys: {missing}")
    else:
        validation_matches_classification = classification_keys.issubset(validation_metrics.keys())
        validation_matches_regression = regression_keys.issubset(validation_metrics.keys())
        test_matches_classification = classification_keys.issubset(test_metrics.keys())
        test_matches_regression = regression_keys.issubset(test_metrics.keys())
        if not (
            (validation_matches_classification and test_matches_classification)
            or (validation_matches_regression and test_matches_regression)
        ):
            raise ValueError("Could not infer task from validation/test metric keys")
    output["validation"] = validation_metrics
    output["test"] = test_metrics
    return output


def _load_main(path: Path, load_ohlcv_fn: object) -> object:
    code = _compile_model(path)
    env: dict[str, object] = {"__name__": "__autoquant_model__", "load_ohlcv": load_ohlcv_fn}
    exec(code, env, env)
    main_fn = env.get("main")
    if not callable(main_fn):
        raise ValueError("train.py must define callable main()")
    return main_fn


def run_train_file(
    path: Path,
    price_rows: list[dict[str, str]],
    train_ratio: float = 0.6,
    validation_ratio: float = 0.2,
    test_ratio: float = 0.2,
    expected_task: str | None = None,
) -> dict[str, object]:
    del train_ratio, validation_ratio, test_ratio

    def _load_ohlcv() -> list[dict[str, str]]:
        return price_rows

    main_fn = _load_main(path, _load_ohlcv)
    payload = main_fn()
    return _read_train_output(payload, expected_task=expected_task)


def validate_model_file(
    path: Path, allowed_predictor_models: list[str] | None = None, expected_task: str | None = None
) -> None:
    del allowed_predictor_models
    run_train_file(path, _sample_ohlcv_rows(), train_ratio=0.6, validation_ratio=0.2, test_ratio=0.2, expected_task=expected_task)
