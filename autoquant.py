from __future__ import annotations

import json
from typing import Annotated, Literal

import typer

from core.commands import (
    run_experiment,
    experiments_list,
    write_generation_report,
    run_generation,
    prepare_data,
    get_learning_tree,
    get_generation_summary,
    register_model,
    list_models,
    get_model,
    validate_model,
    read_predictions,
    get_run_metadata,
    get_runs_summary,
    init_run,
    get_run_status,
    visualize_learning,
    status,
)


app = typer.Typer(
    no_args_is_help=True,
    help="AutoQuant CLI.",
)


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=True))


def _empty_to_none(value: str) -> str | None:
    return value or None


def _register(name: str, help_text: str):
    def decorator(func):
        return app.command(name, help=help_text)(func)

    return decorator


@_register(
    "status",
    "Check required environment variables and workspace configuration.",
)
def status_command() -> None:
    _print(status())


@_register(
    "init-run",
    "Initialize a run with metadata and seed model experiments. Returns run metadata and initial experiment registration details.",
)
def run_init_command(
    ticker: Annotated[str, typer.Option(...)],
    from_date: Annotated[str, typer.Option(...)],
    to_date: Annotated[str, typer.Option(...)],
    task: Annotated[Literal["classification", "regression"], typer.Option(...)],
    max_experiments: Annotated[int, typer.Option()] = 8,
    max_concurrent_models: Annotated[int, typer.Option()] = 4,
    train_time_limit: Annotated[float, typer.Option()] = 5.0,
    objective_function: Annotated[Literal["accuracy", "f1", "macro_f1", "weighted_f1", "r2"] | None, typer.Option()] = None,
    seed_model_path: Annotated[str, typer.Option()] = "",
    run_id: Annotated[str, typer.Option()] = "",
) -> None:
    _print(
        init_run(
            run_id,
            ticker,
            from_date,
            to_date,
            task,
            max_experiments,
            max_concurrent_models,
            train_time_limit,
            objective_function,
            seed_model_path=(seed_model_path or None),
        )
    )


@_register(
    "prepare-data",
    "Fetch and store run OHLCV data for the configured ticker/date range. Returns sync status and data summary.",
)
def prepare_data_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(prepare_data(run_id))


@_register(
    "experiments-list",
    "List experiments for a run, optionally filtered by status. Returns experiment records.",
)
def experiments_list_command(
    run_id: Annotated[str, typer.Option(...)],
    status: Annotated[str, typer.Option()] = "",
) -> None:
    _print(experiments_list(run_id, status=_empty_to_none(status)))


@_register(
    "run-experiment",
    "Execute one experiment for a specific model in a run. Returns execution result and metrics payload.",
)
def experiment_run_command(
    run_id: Annotated[str, typer.Option(...)],
    model_id: Annotated[str, typer.Option(...)],
) -> None:
    _print(run_experiment(run_id, model_id))


@_register(
    "run-generation",
    "Execute pending experiments for the run generation up to worker limits. Returns generation execution summary.",
)
def generation_run_command(
    run_id: Annotated[str, typer.Option(...)],
    max_workers: Annotated[int, typer.Option()] = 0,
) -> None:
    _print(run_generation(run_id, max_workers=(max_workers or None)))


@_register(
    "write-generation-report",
    "Write reports/generation_n.md for a run generation. Returns the report path.",
)
def generation_report_write_command(
    run_id: Annotated[str, typer.Option(...)],
    generation: Annotated[int, typer.Option(...)],
    content: Annotated[str, typer.Option()] = "",
) -> None:
    _print(write_generation_report(run_id, generation, content))


@_register(
    "register-model",
    "Validate a model source file, then register it with lineage metadata for a run.",
)
def register_model_command(
    run_id: Annotated[str, typer.Option(...)],
    name: Annotated[str, typer.Option(...)],
    model_path: Annotated[str, typer.Option(...)],
    log: Annotated[str, typer.Option(...)],
    reasoning: Annotated[str, typer.Option()] = "",
    training_size_days: Annotated[int, typer.Option()] = 30,
    test_size_days: Annotated[int, typer.Option()] = 7,
    generation: Annotated[int | None, typer.Option()] = None,
    parent_id: Annotated[str, typer.Option()] = "",
    refresh_data: Annotated[bool, typer.Option()] = False,
) -> None:
    _print(
        register_model(
            run_id=run_id,
            name=name,
            model_path=model_path,
            log=log,
            reasoning=reasoning,
            training_size_days=training_size_days,
            test_size_days=test_size_days,
            generation=generation,
            parent_id=_empty_to_none(parent_id),
            refresh_data=refresh_data,
        )
    )


@_register(
    "validate-model",
    "Validate a model by running it as an experiment in shared sandbox run (AAPL, Feb 2026). Returns status and metrics.",
)
def validate_model_command(
    model_path: Annotated[str, typer.Option(...)],
    task: Annotated[Literal["classification", "regression"], typer.Option(...)],
    training_size_days: Annotated[int, typer.Option()] = 30,
    test_size_days: Annotated[int, typer.Option()] = 7,
    refresh_data: Annotated[bool, typer.Option()] = False,
) -> None:
    _print(
        validate_model(
            model_path=model_path,
            task=task,
            training_size_days=training_size_days,
            test_size_days=test_size_days,
            refresh_data=refresh_data,
        )
    )


@_register(
    "list-models",
    "List all registered models for a run. Returns model metadata array.",
)
def model_list_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(list_models(run_id))


@_register(
    "get-model",
    "Read one model's metadata and source by model id. Returns full model payload.",
)
def get_model_command(
    run_id: Annotated[str, typer.Option(...)],
    model_id: Annotated[str, typer.Option(...)],
) -> None:
    _print(get_model(run_id, model_id))


@_register(
    "get-learning-tree",
    "Build lineage and performance view for model selection decisions. Returns learning tree payload.",
)
def get_learning_tree_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(get_learning_tree(run_id))


@_register(
    "read-predictions",
    "Read run predictions with optional model and date filters. Returns prediction rows.",
)
def predictions_read_command(
    run_id: Annotated[str, typer.Option(...)],
    model_id: Annotated[str, typer.Option()] = "",
    date_from: Annotated[str, typer.Option()] = "",
    date_to: Annotated[str, typer.Option()] = "",
) -> None:
    _print(read_predictions(run_id, model_id=_empty_to_none(model_id), date_from=_empty_to_none(date_from), date_to=_empty_to_none(date_to)))


@_register(
    "visualize-learning",
    "Generate run charts and optionally write files to an output directory. Returns chart artifact info.",
)
def visualize_learning_command(
    run_id: Annotated[str, typer.Option(...)],
    output: Annotated[str, typer.Option()] = "",
) -> None:
    _print(visualize_learning(run_id, output=_empty_to_none(output)))


@_register(
    "get-run-metadata",
    "Read saved run metadata. Returns run metadata.",
)
def run_metadata_get_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(get_run_metadata(run_id))


@_register(
    "get-generation-summary",
    "Read current generation progress and pending/completed counts. Returns generation status.",
)
def generation_state_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(get_generation_summary(run_id))


@_register(
    "get-run-status",
    "Read run metadata and current generation state in one call. Returns merged metadata and generation payload.",
)
def run_status_command(run_id: Annotated[str, typer.Option(...)]) -> None:
    _print(get_run_status(run_id))


@_register(
    "get-runs-summary",
    "Summarize all discovered runs and their top-level performance. Returns run summary list.",
)
def runs_summary_command() -> None:
    _print(get_runs_summary())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
