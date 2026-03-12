from __future__ import annotations

import re
import uuid
from typing import Any

from core.constants import EXPERIMENTS_CSV, EXPERIMENT_FIELDNAMES, MODEL_FIELDNAMES, MODELS_CSV, MODELS_DIR
from core.graph import upsert_model_node
from core.utils.io_util import write_text
from core.paths import run_dir
from core.schemas import ExperimentRow, ModelRow
from core.utils.storage import get_model_rows, to_dict_rows, upsert_csv
from core.utils.time_utils import now_utc

from .shared import read_run_meta, safe_model_text, write_run_meta


def _safe_model_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")


def model_create(
    run_id: str,
    name: str,
    content: str,
    log: str,
    reasoning: str,
    training_size_days: int = 90,
    test_size_days: int = 7,
    generation: int | None = None,
    parent_id: str | None = None,
) -> dict[str, Any]:
    model_name = name.strip()
    if not model_name:
        raise ValueError("name cannot be empty")
    if len(model_name) > 20:
        raise ValueError("name cannot be longer than 20 characters")
    if training_size_days < 1:
        raise ValueError("training_size_days must be >= 1")
    if test_size_days < 1:
        raise ValueError("test_size_days must be >= 1")
    target_run_dir = run_dir(run_id)
    meta = read_run_meta(run_id)
    models = get_model_rows(target_run_dir, MODELS_CSV)
    target_generation = generation if generation is not None else (max((model.generation for model in models), default=-1) + 1)
    existing_model_ids = {model.model_id for model in models}
    model_id = ""
    while not model_id or model_id in existing_model_ids:
        model_id = uuid.uuid4().hex[:8]
    if models and not parent_id:
        raise ValueError("parent_id is required for non-seed models")
    if not models and parent_id:
        raise ValueError("seed model cannot define parent_id")
    if parent_id and parent_id not in existing_model_ids:
        raise ValueError(f"Unknown parent_id: {parent_id}")
    safe_name = _safe_model_name(model_name)
    model_filename = f"{safe_name}_{model_id}.py" if safe_name else f"{model_id}.py"
    model_path = f"{MODELS_DIR}/{model_filename}"
    write_text(target_run_dir / model_path, safe_model_text(content))
    model_row = ModelRow(
        name=model_name,
        model_id=model_id,
        generation=target_generation,
        task=meta.task,
        model_path=model_path,
        training_size_days=training_size_days,
        test_size_days=test_size_days,
        parent_id=parent_id,
        reasoning=reasoning,
        log=log,
        created_at_utc=now_utc(),
    )
    upsert_csv(target_run_dir / MODELS_CSV, MODEL_FIELDNAMES, ["model_id"], to_dict_rows([model_row]))
    exp_row = ExperimentRow(
        ticker=meta.ticker,
        from_date=meta.from_date,
        to_date=meta.to_date,
        model_id=model_id,
        generation=target_generation,
        task=meta.task,
        status="pending",
    )
    upsert_csv(target_run_dir / EXPERIMENTS_CSV, EXPERIMENT_FIELDNAMES, ["ticker", "from_date", "to_date", "model_id"], to_dict_rows([exp_row]))
    upsert_model_node(target_run_dir, model_id, target_generation, parent_id, model_row.created_at_utc)
    meta.current_generation = max(meta.current_generation, target_generation)
    write_run_meta(meta)
    return {
        "name": model_name,
        "run_id": run_id,
        "model_id": model_id,
        "generation": target_generation,
        "model_path": model_path,
        "training_size_days": training_size_days,
        "test_size_days": test_size_days,
        "parent_id": parent_id,
    }
