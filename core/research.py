from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)

from core.schemas import ExperimentRow, ModelRow, Settings

from core.constants import (
    EXPERIMENTS_CSV,
    EXPERIMENT_FIELDNAMES,
    MODELS_CSV,
    PRICES_CSV,
    RUN_SETTINGS_JSON,
)
from core.graph import update_model_objective
from core.utils.data_util import get_ohlcv
from core.utils.io_util import read_csv, read_json
from core.utils.model_runtime import run_train_file
from core.utils.storage import (
    get_model_map,
    get_model_rows,
    parse_experiment_rows,
    to_dict_rows,
    upsert_csv,
)
from core.utils.time_utils import now_utc


def get_objective_value(metrics: dict[str, object], objective_function: str, task: str) -> float:
    if task == "classification":
        if objective_function == "accuracy":
            return float(metrics["accuracy"])
        if objective_function == "f1":
            return float(metrics["f1"])
        if objective_function == "macro_f1":
            return float(metrics["macro_f1"])
        return float(metrics["weighted_f1"])
    return float(metrics["r2"])


def run_experiment(base_dir: Path, settings: Settings, exp: ExperimentRow) -> None:
    logger.info("Experiment start model=%s ticker=%s range=%s..%s", exp.model_id, exp.ticker, exp.from_date, exp.to_date)
    exp.status = "running"
    exp.started_at_utc = now_utc()
    exp.finished_at_utc = None
    exp.error = None
    exp.task = settings.task
    upsert_csv(base_dir / EXPERIMENTS_CSV, EXPERIMENT_FIELDNAMES, ["ticker", "from_date", "to_date", "model_id"], to_dict_rows([exp]))
    models = get_model_map(base_dir, MODELS_CSV)
    model: ModelRow | None = models.get(exp.model_id)
    if model is None:
        raise RuntimeError(f"Unknown model_id: {exp.model_id}")
    try:
        price_rows = get_ohlcv(base_dir.name, ticker=exp.ticker)
        if not price_rows:
            raise RuntimeError(f"No rows found in {PRICES_CSV} for ticker={exp.ticker}")
        train_output = run_train_file(
            base_dir / model.model_path,
            price_rows,
            train_ratio=0.6,
            validation_ratio=0.2,
            test_ratio=0.2,
            expected_task=settings.task,
        )
        validation_metrics = train_output.get("validation")
        test_metrics = train_output.get("test")
        if not isinstance(validation_metrics, dict) or not isinstance(test_metrics, dict):
            raise RuntimeError("Invalid train output: validation and test must be dicts")
        exp.status = "completed"
        exp.metrics = {
            "validation": validation_metrics,
            "test": test_metrics,
        }
        exp.error = None
        exp.finished_at_utc = now_utc()
        upsert_csv(base_dir / EXPERIMENTS_CSV, EXPERIMENT_FIELDNAMES, ["ticker", "from_date", "to_date", "model_id"], to_dict_rows([exp]))
        objective_value = get_objective_value(validation_metrics, settings.objective_function, settings.task)
        update_model_objective(
            base_dir,
            exp.model_id,
            settings.objective_function,
            objective_value,
            {"task": settings.task, "metrics": {"validation": validation_metrics, "test": test_metrics}},
        )
        summary_metric = "macro_f1" if settings.task == "classification" else "r2"
        summary_value = float(validation_metrics[summary_metric])
        logger.info(
            "Experiment done model=%s validation_n=%s test_n=%s objective=%s value=%.4f task=%s summary_metric=%s summary_value=%.4f",
            exp.model_id,
            validation_metrics.get("n_samples"),
            test_metrics.get("n_samples"),
            settings.objective_function,
            objective_value,
            settings.task,
            summary_metric,
            summary_value,
        )
    except Exception as exc:
        exp.status = "failed"
        exp.error = str(exc)
        exp.finished_at_utc = now_utc()
        upsert_csv(base_dir / EXPERIMENTS_CSV, EXPERIMENT_FIELDNAMES, ["ticker", "from_date", "to_date", "model_id"], to_dict_rows([exp]))
        logger.error("Experiment failed model=%s error=%s", exp.model_id, str(exc))
        raise


def count_completed_experiments(base_dir: Path, ticker: str, from_date: str, to_date: str) -> int:
    rows = parse_experiment_rows(read_csv(base_dir / EXPERIMENTS_CSV))
    return len([r for r in rows if r.ticker == ticker and r.from_date == from_date and r.to_date == to_date and r.status == "completed"])


def completed_experiments(base_dir: Path, ticker: str, from_date: str, to_date: str) -> list[ExperimentRow]:
    rows = parse_experiment_rows(read_csv(base_dir / EXPERIMENTS_CSV))
    return [
        r
        for r in rows
        if r.ticker == ticker
        and r.from_date == from_date
        and r.to_date == to_date
        and r.status == "completed"
        and r.metrics is not None
    ]


def get_pending_experiments(base_dir: Path, ticker: str, from_date: str, to_date: str) -> list[ExperimentRow]:
    rows = parse_experiment_rows(read_csv(base_dir / EXPERIMENTS_CSV))
    return [
        r
        for r in rows
        if r.ticker == ticker and r.from_date == from_date and r.to_date == to_date and r.status in {"pending", "running"}
    ]


def run_generation(base_dir: Path, settings: Settings, ticker: str, from_date: str, to_date: str, max_workers: int | None = None) -> list[str]:
    pending = get_pending_experiments(base_dir, ticker, from_date, to_date)
    pending = pending[: max(0, settings.max_experiments - count_completed_experiments(base_dir, ticker, from_date, to_date))]
    if not pending:
        return []
    worker_count = settings.max_concurrent_models if max_workers is None else max_workers
    worker_count = min(max(worker_count, 1), settings.max_concurrent_models, len(pending))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(run_experiment, base_dir, settings, exp) for exp in pending]
        for future in futures:
            future.result()
    generation = max((e.generation for e in pending), default=0)
    output_path = base_dir / "charts" / f"learning_gen_{generation:03d}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_learning_chart(base_dir, output_path=output_path)
    return [e.model_id for e in pending]


def generate_learning_chart(run_dir: Path, output_path: Path | None = None) -> Path:
    import matplotlib.pyplot as plt

    exp_rows = parse_experiment_rows(read_csv(run_dir / EXPERIMENTS_CSV))
    model_rows = {m.model_id: m for m in get_model_rows(run_dir, MODELS_CSV)}
    settings = Settings.model_validate(read_json(run_dir / RUN_SETTINGS_JSON))
    completed = [
        e
        for e in exp_rows
        if e.status == "completed"
        and e.metrics is not None
        and isinstance(e.metrics.get("validation"), dict)
    ]
    completed.sort(key=lambda e: e.finished_at_utc or e.started_at_utc or "")
    if not completed:
        if output_path is None:
            output_path = run_dir / "learning.png"
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title("Learning Progress: 0 Experiments, 0 Kept Improvements")
        ax.set_xlabel("Experiment #")
        ax.set_ylabel("Validation Loss (1 - objective, lower is better)")
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        return output_path

    validation_objective = [
        get_objective_value(e.metrics["validation"], settings.objective_function, e.task) for e in completed if e.metrics is not None
    ]
    validation_loss = [1.0 - value for value in validation_objective]
    running_best = []
    best_so_far = 1.0
    for v in validation_loss:
        best_so_far = min(best_so_far, v)
        running_best.append(best_so_far)
    kept_indices = [i for i in range(len(completed)) if validation_loss[i] == running_best[i] and (i == 0 or running_best[i] < running_best[i - 1])]
    n_total = len(completed)
    n_kept = len(kept_indices)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.scatter(range(n_total), validation_loss, c="lightgray", s=20, alpha=0.8, label="Discarded", zorder=1)
    ax.scatter(kept_indices, [validation_loss[i] for i in kept_indices], c="green", s=80, edgecolors="darkgreen", linewidths=1.5, label="Kept", zorder=3)
    x_line = [0] + kept_indices + [n_total - 1]
    y_line = [running_best[kept_indices[0]]] + [running_best[kept_indices[i]] for i in range(n_kept)] + [running_best[kept_indices[-1]]]
    ax.plot(x_line, y_line, color="green", linewidth=2, label="Running best", zorder=2)
    for i in kept_indices:
        model_id = completed[i].model_id
        log = (model_rows.get(model_id).log or model_id) if model_id in model_rows else model_id
        ax.annotate(log, (i, validation_loss[i]), textcoords="offset points", xytext=(0, 10), ha="center", fontsize=7, rotation=45)
    ax.set_xlabel("Experiment #")
    ax.set_ylabel("Validation Loss (1 - objective, lower is better)")
    ax.set_title(f"Learning Progress: {n_total} Experiments, {n_kept} Kept Improvements")
    ax.legend(loc="upper right")
    ax.grid(True, color="lightgray", linestyle="-")
    ax.set_xlim(-0.5, n_total - 0.5)
    y_min = min(validation_loss)
    y_max = max(validation_loss)
    margin = (y_max - y_min) * 0.1 or 0.01
    ax.set_ylim(y_min - margin, y_max + margin)
    if output_path is None:
        output_path = run_dir / "learning.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    return output_path
