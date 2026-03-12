from __future__ import annotations

from pathlib import Path
from typing import Any

from core.constants import MODELS_CSV, PRICES_CSV, RUN_META_JSON
from core.paths import run_dir
from core.utils.io_util import read_csv
from core.utils.storage import get_model_rows

from .run_experiment import run_experiment
from .register_model import create_model
from .prepare_data import prepare_data
from .init_run import init_run
from .shared import read_run_meta

SANDBOX_RUN_ID = "sandbox"
SANDBOX_TICKER = "AAPL"
SANDBOX_FROM_DATE = "2026-02-01"
SANDBOX_TO_DATE = "2026-02-28"


def _latest_model_id(rows: list[Any]) -> str:
    if not rows:
        raise RuntimeError("Sandbox has no models")
    latest = max(rows, key=lambda row: (row.generation, row.created_at_utc, row.model_id))
    return latest.model_id


def _validation_model_name(path: Path) -> str:
    name = f"val_{path.stem}"
    return name[:20]


def _resolve_validation_model(
    source_path: Path,
    task: str,
    training_size_days: int,
    test_size_days: int,
) -> tuple[str, Path, bool]:
    sandbox_dir = run_dir(SANDBOX_RUN_ID)
    if not (sandbox_dir / RUN_META_JSON).exists():
        init_payload = init_run(
            run_id=SANDBOX_RUN_ID,
            ticker=SANDBOX_TICKER,
            from_date=SANDBOX_FROM_DATE,
            to_date=SANDBOX_TO_DATE,
            task=task,
            seed_model_path=str(source_path),
            seed_training_size_days=training_size_days,
            seed_test_size_days=test_size_days,
        )
        return str(init_payload["seed_model_id"]), sandbox_dir, True
    meta = read_run_meta(SANDBOX_RUN_ID)
    if meta.task != task:
        raise RuntimeError(f"Sandbox task mismatch: existing={meta.task} requested={task}")
    source = source_path.read_text(encoding="utf-8")
    models = get_model_rows(sandbox_dir, MODELS_CSV)
    parent_id = _latest_model_id(models)
    generation = max((row.generation for row in models), default=0) + 1
    created = create_model(
        run_id=SANDBOX_RUN_ID,
        name=_validation_model_name(source_path),
        content=source,
        log="sandbox validation",
        reasoning="validate-model",
        training_size_days=training_size_days,
        test_size_days=test_size_days,
        generation=generation,
        parent_id=parent_id,
    )
    return str(created["model_id"]), sandbox_dir, False


def validate_model(
    model_path: str,
    task: str,
    training_size_days: int = 30,
    test_size_days: int = 7,
    refresh_data: bool = False,
) -> dict[str, Any]:
    source_path = Path(model_path)
    if not source_path.exists():
        raise RuntimeError(f"Model file not found: {source_path}")
    model_id, sandbox_dir, initialized = _resolve_validation_model(
        source_path,
        task,
        training_size_days,
        test_size_days,
    )
    prices_rows = read_csv(sandbox_dir / PRICES_CSV)
    if refresh_data or not prices_rows:
        prepare_data(SANDBOX_RUN_ID)
        data_source = "downloaded"
    else:
        data_source = "reused"
    result = run_experiment(SANDBOX_RUN_ID, model_id)
    return {
        "validation_run_id": SANDBOX_RUN_ID,
        "validation_run_dir": str(sandbox_dir),
        "model_id": model_id,
        "status": result.get("status"),
        "metrics": result.get("metrics"),
        "error": result.get("error"),
        "task": task,
        "ticker": SANDBOX_TICKER,
        "from_date": SANDBOX_FROM_DATE,
        "to_date": SANDBOX_TO_DATE,
        "training_size_days": training_size_days,
        "test_size_days": test_size_days,
        "data_source": data_source,
        "sandbox_initialized": initialized,
    }
