from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from core.constants import RUN_META_JSON
from core.graph import init_graph
from core.paths import run_dir
from core.schemas import RunMeta
from core.utils.git_util import current_repo_commit_hash
from core.utils.time_utils import now_utc

from .model_create import model_create
from .shared import ensure_run_layout, write_run_meta

SEED_MODEL_PATH = Path(__file__).resolve().parent.parent / "seed_train.py"


def run_init(
    run_id: str,
    ticker: str,
    from_date: str,
    to_date: str,
    task: str,
    max_experiments: int | None = None,
    max_concurrent_models: int | None = None,
    train_time_limit_minutes: float | None = None,
    objective_function: str | None = None,
    min_news_coverage: float | None = None,
    seed_model_path: str | None = None,
    seed_training_size_days: int = 30,
    seed_test_size_days: int = 7,
) -> dict[str, Any]:
    if not run_id:
        run_id = uuid.uuid4().hex[:8]
    target_run_dir = run_dir(run_id)
    defaults = RunMeta(run_id=run_id, ticker=ticker, from_date=from_date, to_date=to_date, created_at_utc=now_utc()).model_dump(mode="json")
    objective = objective_function
    if objective is None:
        objective = "r2" if task == "regression" else defaults["objective_function"]
    target_run_dir.parent.mkdir(parents=True, exist_ok=True)
    ensure_run_layout(target_run_dir)
    init_graph(target_run_dir)
    meta = RunMeta(
        run_id=run_id,
        ticker=ticker,
        from_date=from_date,
        to_date=to_date,
        task=task,
        objective_function=objective,
        max_experiments=max_experiments if max_experiments is not None else defaults["max_experiments"],
        max_concurrent_models=max_concurrent_models if max_concurrent_models is not None else defaults["max_concurrent_models"],
        train_time_limit_minutes=(
            train_time_limit_minutes if train_time_limit_minutes is not None else defaults["train_time_limit_minutes"]
        ),
        min_news_coverage=min_news_coverage if min_news_coverage is not None else defaults["min_news_coverage"],
        current_generation=0,
        created_at_utc=now_utc(),
        autoquant_commit_hash=current_repo_commit_hash(),
    )
    write_run_meta(meta)
    seed_path = Path(seed_model_path) if seed_model_path else SEED_MODEL_PATH
    if not seed_path.exists():
        raise RuntimeError(f"Seed model not found: {seed_path}")
    seed_content = seed_path.read_text(encoding="utf-8")
    seed_result = model_create(
        run_id=run_id,
        name="seed",
        content=seed_content,
        log="seed model",
        reasoning="initial seed",
        training_size_days=seed_training_size_days,
        test_size_days=seed_test_size_days,
        generation=0,
        parent_id=None,
    )
    return {
        "run_id": run_id,
        "run_dir": str(target_run_dir),
        "ticker": ticker,
        "from_date": from_date,
        "to_date": to_date,
        "task": meta.task,
        "metadata_path": str(target_run_dir / RUN_META_JSON),
        "seed_model_id": seed_result["model_id"],
    }
