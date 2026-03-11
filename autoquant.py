from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

import typer

from core.commands import (
    config_get,
    experiment_run,
    experiments_list,
    generation_run,
    prepare_data,
    get_learning_tree,
    get_generation_state,
    model_create,
    model_list,
    model_read,
    model_validate,
    predictions_read,
    runs_summary,
    run_init,
    run_status,
    visualize,
)


app = typer.Typer(
    no_args_is_help=True,
    help="AutoQuant CLI.",
)


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=True))


@app.command(
    "run-init",
    help="Initialize a run with settings and seed model experiments. Returns run metadata and initial experiment registration details.",
)
def run_init_command(
    ticker: Annotated[str, typer.Option(...)],
    from_date: Annotated[str, typer.Option(...)],
    to_date: Annotated[str, typer.Option(...)],
    task: Annotated[Literal["classification", "regression"], typer.Option(...)],
    available_predictor_models: Annotated[list[str], typer.Option()] = ["gemini/gemini-2.5-flash"],
    llm_temperature: Annotated[float, typer.Option()] = 0,
    llm_max_tokens: Annotated[int, typer.Option()] = 65536,
    max_experiments: Annotated[int, typer.Option()] = 8,
    max_concurrent_models: Annotated[int, typer.Option()] = 4,
    prediction_time: Annotated[str, typer.Option()] = "17:00",
    prediction_time_timezone: Annotated[str, typer.Option()] = "UTC",
    objective_function: Annotated[Literal["accuracy", "f1", "macro_f1", "weighted_f1", "r2"] | None, typer.Option()] = None,
    min_news_coverage: Annotated[float, typer.Option()] = 50.0,
    seed_model_path: Annotated[str, typer.Option()] = "",
    run_id: Annotated[str, typer.Option()] = "",
) -> None:
    _print(
        run_init(
            run_id,
            ticker,
            from_date,
            to_date,
            task,
            available_predictor_models,
            llm_temperature,
            llm_max_tokens,
            max_experiments,
            max_concurrent_models,
            prediction_time,
            prediction_time_timezone,
            objective_function,
            min_news_coverage,
            seed_model_path=(seed_model_path or None),
        )
    )


@app.command(
    "prepare-data",
    help="Fetch and store run OHLCV data for the configured ticker/date range. Returns sync status and data summary.",
)
def prepare_data_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(prepare_data(run_id))


@app.command(
    "experiments-list",
    help="List experiments for a run, optionally filtered by status. Returns experiment records.",
)
def experiments_list_command(
    run_id: Annotated[str, typer.Option(...)],
    status: Annotated[str, typer.Option()] = "",
) -> None:
    _print(experiments_list(run_id, status=(status or None)))


@app.command(
    "run-experiment",
    help="Execute one experiment for a specific model in a run. Returns execution result and metrics payload.",
)
def experiment_run_command(
    run_id: Annotated[str, typer.Option(...)],
    model_id: Annotated[str, typer.Option(...)],
) -> None:
    _print(experiment_run(run_id, model_id))


@app.command(
    "run-generation",
    help="Execute pending experiments for the run generation up to worker limits. Returns generation execution summary.",
)
def generation_run_command(
    run_id: Annotated[str, typer.Option(...)],
    max_workers: Annotated[int, typer.Option()] = 0,
) -> None:
    _print(generation_run(run_id, max_workers=(max_workers or None)))


@app.command(
    "generate-model",
    help="Register a validated model source file and lineage metadata for a run. Returns created model metadata.",
)
def generate_model_command(
    run_id: Annotated[str, typer.Option(...)],
    name: Annotated[str, typer.Option(...)],
    model_path: Annotated[str, typer.Option(...)],
    log: Annotated[str, typer.Option(...)],
    reasoning: Annotated[str, typer.Option()] = "",
    generation: Annotated[int | None, typer.Option()] = None,
    parent_id: Annotated[str, typer.Option()] = "",
) -> None:
    content = Path(model_path).read_text(encoding="utf-8")
    _print(
        model_create(
            run_id,
            name,
            content,
            log,
            reasoning,
            generation=generation,
            parent_id=(parent_id or None),
        )
    )


@app.command(
    "list-models",
    help="List all registered models for a run. Returns model metadata array.",
)
def model_list_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(model_list(run_id))


@app.command(
    "get-model",
    help="Read one model's metadata and source by model id. Returns full model payload.",
)
def get_model_command(
    run_id: Annotated[str, typer.Option(...)],
    model_id: Annotated[str, typer.Option(...)],
) -> None:
    _print(model_read(run_id, model_id))


@app.command(
    "model-validate",
    help="Validate a candidate model file against runtime and metrics contract rules. Returns validation outcome details.",
)
def model_validate_command(
    run_id: Annotated[str, typer.Option(...)],
    model_path: Annotated[str, typer.Option(...)],
) -> None:
    _print(model_validate(run_id, model_path))


@app.command(
    "get-learning-tree",
    help="Build lineage and performance view for model selection decisions. Returns learning tree payload.",
)
def get_learning_tree_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(get_learning_tree(run_id))


@app.command(
    "read-predictions",
    help="Read run predictions with optional model and date filters. Returns prediction rows.",
)
def predictions_read_command(
    run_id: Annotated[str, typer.Option(...)],
    model_id: Annotated[str, typer.Option()] = "",
    date_from: Annotated[str, typer.Option()] = "",
    date_to: Annotated[str, typer.Option()] = "",
) -> None:
    _print(predictions_read(run_id, model_id=(model_id or None), date_from=(date_from or None), date_to=(date_to or None)))


@app.command(
    "visualize-learning",
    help="Generate run charts and optionally write files to an output directory. Returns chart artifact info.",
)
def visualize_learning_command(
    run_id: Annotated[str, typer.Option(...)],
    output: Annotated[str, typer.Option()] = "",
) -> None:
    _print(visualize(run_id, output=(output or None)))


@app.command(
    "get-config",
    help="Read saved run settings snapshot. Returns run configuration.",
)
def config_get_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(config_get(run_id))


@app.command(
    "get-generation-summary",
    help="Read current generation progress and pending/completed counts. Returns generation status.",
)
def generation_state_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(get_generation_state(run_id))


@app.command(
    "get-run-status",
    help="Read run config and current generation state in one call. Returns merged config and generation payload.",
)
def run_status_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(run_status(run_id))


@app.command(
    "get-runs-summary",
    help="Summarize all discovered runs and their top-level performance. Returns run summary list.",
)
def runs_summary_command() -> None:
    _print(runs_summary())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
