from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator


class PredictionLabel(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class PredictionResponse(BaseModel):
    reasoning: str
    prediction: PredictionLabel


class ModelRow(BaseModel):
    model_id: str
    generation: int = 0
    task: Literal["classification", "regression"] = "classification"
    model_path: str
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
    current_generation: int = 0
    created_at_utc: str
    autoquant_commit_hash: str | None = None


class Settings(BaseModel):
    available_predictor_models: list[str] = ["gemini/gemini-2.5-flash"]
    llm_temperature: float = 0
    llm_max_tokens: int = 65536
    max_experiments: int = 8
    max_concurrent_models: int = Field(default=4, ge=1, le=4)
    prediction_time: str = "17:00"
    prediction_time_timezone: str = "UTC"
    task: Literal["classification", "regression"] = "classification"
    objective_function: str = "macro_f1"
    min_news_coverage: float = Field(default=50.0, ge=0, le=100)

    @field_validator("prediction_time")
    @classmethod
    def validate_prediction_time(cls, v: str) -> str:
        hour_str, minute_str = v.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
        if len(hour_str) != 2 or len(minute_str) != 2 or hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("prediction_time must be HH:MM in 24-hour format")
        return v

    @field_validator("prediction_time_timezone")
    @classmethod
    def validate_prediction_time_timezone(cls, v: str) -> str:
        ZoneInfo(v)
        return v

    @field_validator("objective_function")
    @classmethod
    def validate_objective_function(cls, v: str, info: Any) -> str:
        task = info.data.get("task", "classification")
        allowed = {"accuracy", "f1", "macro_f1", "weighted_f1"} if task == "classification" else {"r2"}
        if v not in allowed:
            raise ValueError(f"objective_function must be one of {sorted(allowed)} for task={task}")
        return v
