from __future__ import annotations

import ast
from pathlib import Path
from types import CodeType
from typing import Any

ALLOWED_IMPORTS = {"math", "statistics", "typing", "datetime"}
DISALLOWED_NAMES = {"eval", "exec", "compile", "__import__", "open", "input", "globals", "locals", "vars"}
DISALLOWED_ATTRS = {"system", "popen", "run", "Popen", "fork", "remove", "unlink", "rmtree"}


def _validate_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            else:
                module = (node.module or "").split(".")[0]
                modules = [module] if module else []
            for module in modules:
                if module and module not in ALLOWED_IMPORTS and module != "__future__":
                    raise ValueError(f"Disallowed import: {module}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DISALLOWED_NAMES:
                raise ValueError(f"Disallowed call: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in DISALLOWED_ATTRS:
                raise ValueError(f"Disallowed call attribute: {node.func.attr}")


def _compile_model(path: Path) -> CodeType:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    _validate_ast(tree)
    return compile(tree, str(path), "exec")


def load_model_module(path: Path) -> tuple[str, Any, int, str, float]:
    code = _compile_model(path)
    def _safe_import(name: str, globals: dict | None = None, locals: dict | None = None, fromlist: tuple | list = (), level: int = 0) -> Any:
        root = name.split(".")[0]
        if root not in ALLOWED_IMPORTS and root != "__future__":
            raise ImportError(f"Disallowed import: {name}")
        return __import__(name, globals, locals, fromlist, level)
    env: dict[str, Any] = {"__builtins__": {"__import__": _safe_import, "len": len, "min": min, "max": max, "sum": sum, "range": range, "abs": abs, "round": round, "float": float, "int": int, "str": str, "bool": bool, "list": list, "dict": dict, "set": set, "tuple": tuple}}
    exec(code, env, env)
    prompt = env.get("prompt")
    process_prices = env.get("process_prices")
    if "price_lookback_window_days" not in env:
        raise ValueError("Model must define price_lookback_window_days (int, 1-30)")
    if "predictor_model" not in env:
        raise ValueError("Model must define predictor_model (str, one of available_predictor_models from run settings)")
    if "temperature" not in env:
        raise ValueError("Model must define temperature (float)")
    try:
        days = int(env["price_lookback_window_days"])
    except (TypeError, ValueError):
        raise ValueError("price_lookback_window_days must be an int")
    predictor_model = str(env["predictor_model"]).strip()
    try:
        temperature = float(env["temperature"])
    except (TypeError, ValueError):
        raise ValueError("temperature must be a float")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Model must define non-empty `prompt` string")
    if not callable(process_prices):
        raise ValueError("Model must define callable `process_prices(price_rows)`")
    price_lookback_window_days = max(1, min(30, days))
    return prompt, process_prices, price_lookback_window_days, predictor_model, temperature


def validate_model_file(path: Path, allowed_predictor_models: list[str] | None = None) -> None:
    prompt, process_prices, price_lookback_window_days, predictor_model, temperature = load_model_module(path)
    if allowed_predictor_models is not None and predictor_model not in allowed_predictor_models:
        raise ValueError(f"predictor_model must be one of {allowed_predictor_models}, got {predictor_model!r}")
    sample = [{"timestamp": "2026-01-01T00:00:00+00:00", "ticker": "X", "price": "100", "volume": "1"}]
    result = process_prices(sample)
    if not isinstance(result, dict):
        raise ValueError("process_prices must return a dict")
    if not prompt:
        raise ValueError("prompt cannot be empty")
    if not isinstance(temperature, float):
        raise ValueError("temperature must be a float")
