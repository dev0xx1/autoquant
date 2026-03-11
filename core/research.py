from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from smartpy.utility.log_util import getLogger

logger = getLogger(__name__)

from llms import get_actual_label, predict_one_day
from core.schemas import ExperimentRow, ModelRow, PredictionLabel, PredictionRow, Settings

from core.constants import (
    EXPERIMENTS_CSV,
    EXPERIMENT_FIELDNAMES,
    MODELS_CSV,
    PREDICTIONS_CSV,
    PREDICTION_FIELDNAMES,
    PRICES_CSV,
    NEWS_CSV,
)
from core.graph import update_model_objective
from core.storage import (
    get_model_map,
    get_model_rows,
    parse_experiment_rows,
    parse_prediction_rows,
    read_csv,
    to_dict_rows,
    upsert_csv,
)
from core.time_utils import day_iter, now_utc


def _safe_div(num: float, den: float) -> float:
    return num / den if den > 0 else 0.0


def compute_metrics(rows: list[PredictionRow]) -> tuple[int, float, float, float, float, float, float, float]:
    valid = [r for r in rows if r.actual is not None]
    n = len(valid)
    if n == 0:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    correct = sum(1 for r in valid if r.prediction == r.actual)
    tp_up = sum(1 for r in valid if r.prediction == PredictionLabel.UP and r.actual == PredictionLabel.UP)
    fp_up = sum(1 for r in valid if r.prediction == PredictionLabel.UP and r.actual == PredictionLabel.DOWN)
    fn_up = sum(1 for r in valid if r.prediction == PredictionLabel.DOWN and r.actual == PredictionLabel.UP)
    tp_down = sum(1 for r in valid if r.prediction == PredictionLabel.DOWN and r.actual == PredictionLabel.DOWN)
    fp_down = fn_up
    fn_down = fp_up
    precision_up = _safe_div(tp_up, tp_up + fp_up)
    recall_up = _safe_div(tp_up, tp_up + fn_up)
    f1_up = _safe_div(2 * precision_up * recall_up, precision_up + recall_up)
    precision_down = _safe_div(tp_down, tp_down + fp_down)
    recall_down = _safe_div(tp_down, tp_down + fn_down)
    f1_down = _safe_div(2 * precision_down * recall_down, precision_down + recall_down)
    support_up = tp_up + fn_up
    support_down = tp_down + fn_down
    macro_f1 = (f1_up + f1_down) / 2.0
    weighted_f1 = _safe_div((f1_up * support_up) + (f1_down * support_down), support_up + support_down)
    true_up = sum(1 for r in valid if r.actual == PredictionLabel.UP)
    return n, correct / n, precision_up, recall_up, f1_up, weighted_f1, macro_f1, true_up / n


def get_objective_value(accuracy: float, f1: float, macro_f1: float, weighted_f1: float, objective_function: str) -> float:
    if objective_function == "accuracy":
        return accuracy
    if objective_function == "f1":
        return f1
    if objective_function == "macro_f1":
        return macro_f1
    return weighted_f1


async def _predict_missing_rows(
    base_dir: Path,
    settings: Settings,
    model: ModelRow,
    ticker: str,
    missing_days: list[str],
    news_rows: list[dict[str, str]],
    price_rows: list[dict[str, str]],
    prediction_rows: list[dict[str, str]],
) -> list[PredictionRow]:
    semaphore = asyncio.Semaphore(5)

    async def predict_day(day: str) -> PredictionRow:
        async with semaphore:
            return await asyncio.to_thread(
                predict_one_day,
                base_dir=base_dir,
                settings=settings,
                model=model,
                ticker=ticker,
                day=day,
                news_rows=news_rows,
                price_rows=price_rows,
                prediction_rows=prediction_rows,
                created_at_utc=now_utc(),
            )

    return await asyncio.gather(*(predict_day(day) for day in missing_days))


def run_experiment(base_dir: Path, settings: Settings, exp: ExperimentRow) -> None:
    logger.info("Experiment start model=%s ticker=%s range=%s..%s", exp.model_id, exp.ticker, exp.from_date, exp.to_date)
    models = get_model_map(base_dir, MODELS_CSV)
    model = models.get(exp.model_id)
    if model is None:
        raise RuntimeError(f"Unknown model_id: {exp.model_id}")
    news_rows = read_csv(base_dir / NEWS_CSV)
    price_rows = read_csv(base_dir / PRICES_CSV)
    prediction_rows = parse_prediction_rows(read_csv(base_dir / PREDICTIONS_CSV))
    existing_index = {(r.ticker, r.date, r.model_id): r for r in prediction_rows}
    missing_days = [
        day
        for day in day_iter(exp.from_date, exp.to_date)
        if (exp.ticker, day, exp.model_id) not in existing_index
    ]
    if missing_days:
        logger.info("Predicting missing days model=%s count=%s", exp.model_id, len(missing_days))
        new_rows = asyncio.run(
            _predict_missing_rows(
                base_dir=base_dir,
                settings=settings,
                model=model,
                ticker=exp.ticker,
                missing_days=missing_days,
                news_rows=news_rows,
                price_rows=price_rows,
                prediction_rows=read_csv(base_dir / PREDICTIONS_CSV),
            )
        )
        for row in new_rows:
            existing_index[(row.ticker, row.date, row.model_id)] = row
    produced: list[PredictionRow] = []
    for day in day_iter(exp.from_date, exp.to_date):
        key = (exp.ticker, day, exp.model_id)
        row = existing_index.get(key)
        if row is None:
            continue
        if row.actual is None:
            actual = get_actual_label(price_rows, exp.ticker, day, settings)
            if actual is not None:
                row.actual = actual
                row.is_correct = row.prediction == actual
        produced.append(row)
    upsert_csv(base_dir / PREDICTIONS_CSV, PREDICTION_FIELDNAMES, ["ticker", "date", "model_id"], to_dict_rows(list(existing_index.values())))
    n, accuracy, precision, recall, f1, weighted_f1, macro_f1, y_dist = compute_metrics(produced)
    exp.status = "completed"
    exp.n_samples = n
    exp.accuracy = accuracy
    exp.precision = precision
    exp.recall = recall
    exp.f1 = f1
    exp.weighted_f1 = weighted_f1
    exp.macro_f1 = macro_f1
    exp.y_dist = y_dist
    exp.finished_at_utc = now_utc()
    upsert_csv(base_dir / EXPERIMENTS_CSV, EXPERIMENT_FIELDNAMES, ["ticker", "from_date", "to_date", "model_id"], to_dict_rows([exp]))
    objective_value = get_objective_value(accuracy, f1, macro_f1, weighted_f1, settings.objective_function)
    update_model_objective(
        base_dir,
        exp.model_id,
        settings.objective_function,
        objective_value,
        {"accuracy": accuracy, "f1": f1, "macro_f1": macro_f1, "weighted_f1": weighted_f1},
    )
    logger.info(
        "Experiment done model=%s n=%s objective=%s value=%.4f weighted_f1=%.4f accuracy=%.4f",
        exp.model_id,
        n,
        settings.objective_function,
        objective_value,
        weighted_f1,
        accuracy,
    )


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
        and (r.weighted_f1 is not None or r.f1 is not None or r.accuracy is not None)
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
    worker_count = max_workers or settings.max_concurrent_models
    worker_count = min(max(worker_count, 1), len(pending))
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
    completed = [e for e in exp_rows if e.status == "completed" and e.macro_f1 is not None]
    completed.sort(key=lambda e: e.finished_at_utc or e.started_at_utc or "")
    if not completed:
        if output_path is None:
            output_path = run_dir / "learning.png"
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title("Learning Progress: 0 Experiments, 0 Kept Improvements")
        ax.set_xlabel("Experiment #")
        ax.set_ylabel("Validation Loss (1 - Macro F1, lower is better)")
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        return output_path

    validation_loss = [1.0 - float(e.macro_f1) for e in completed]
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
    ax.set_ylabel("Validation Loss (1 - Macro F1, lower is better)")
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
