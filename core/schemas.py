from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PredictionLabel(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class ModelRow(BaseModel):
    name: str
    model_id: str
    generation: int = 0
    task: Literal["classification", "regression"] = "classification"
    model_path: str
    training_size_days: int = Field(default=30, ge=1)
    test_size_days: int = Field(default=7, ge=1)
    parent_id: Optional[str] = None
    reasoning: Optional[str] = ""
    log: Optional[str] = ""
    created_at_utc: str


class ExperimentRow(BaseModel):
    ticker: str
    from_date: str
    to_date: str
    model_id: str
    generation: int = 0
    task: Literal["classification", "regression"] = "classification"
    status: str = "pending"
    metrics: Optional[dict[str, Any]] = None
    started_at_utc: Optional[str] = None
    finished_at_utc: Optional[str] = None
    error: Optional[str] = None


class PredictionRow(BaseModel):
    ticker: str
    date: str
    model_id: str
    reasoning: str
    prediction: PredictionLabel
    actual: Optional[PredictionLabel] = None
    is_correct: Optional[bool] = None
    created_at_utc: str


class RunMeta(BaseModel):
    run_id: str
    ticker: str
    from_date: str
    to_date: str
    task: Literal["classification", "regression"] = "classification"
    objective_function: str = "macro_f1"
    max_experiments: int = 8
    max_concurrent_models: int = Field(default=4, ge=1, le=4)
    train_time_limit_minutes: float = Field(default=5.0, gt=0)
    current_generation: int = 0
    created_at_utc: str
    autoquant_commit_hash: str | None = None

    @field_validator("objective_function")
    @classmethod
    def validate_objective_function(cls, v: str, info: Any) -> str:
        task = info.data.get("task", "classification")
        allowed = {"accuracy", "f1", "macro_f1", "weighted_f1"} if task == "classification" else {"r2"}
        if v not in allowed:
            raise ValueError(f"objective_function must be one of {sorted(allowed)} for task={task}")
        return v
