from __future__ import annotations

import argparse
import json

from core.commands import (
    config_get,
    data_sync,
    experiment_run,
    experiments_list,
    generation_run,
    get_learning_tree,
    get_generation_state,
    model_create,
    model_list,
    model_read,
    model_validate,
    predictions_read,
    runs_summary,
    run_init,
    visualize,
)

def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser(
        "run-init",
        help="Initialize a run and seed model",
        description="Create a run with settings and register the seed model with pending experiments.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--ticker", required=True)
    p.add_argument("--from_date", required=True)
    p.add_argument("--to_date", required=True)
    p.add_argument("--available_predictor_models", nargs="+", default=["gemini/gemini-2.5-flash"])
    p.add_argument("--llm_temperature", type=float, default=0)
    p.add_argument("--llm_max_tokens", type=int, default=65536)
    p.add_argument("--max_experiments", type=int, default=8)
    p.add_argument("--max_concurrent_models", type=int, default=4)
    p.add_argument("--prediction_time", default="17:00")
    p.add_argument("--prediction_time_timezone", default="UTC")
    p.add_argument("--objective_function", choices=["accuracy", "f1", "macro_f1", "weighted_f1"], default="weighted_f1")
    p.add_argument("--min_news_coverage", type=float, default=50.0)
    p.add_argument("--seed_model_path", default="")
    p.set_defaults(
        func=lambda a: _print(
            run_init(
                a.run_id,
                a.ticker,
                a.from_date,
                a.to_date,
                a.available_predictor_models,
                a.llm_temperature,
                a.llm_max_tokens,
                a.max_experiments,
                a.max_concurrent_models,
                a.prediction_time,
                a.prediction_time_timezone,
                a.objective_function,
                a.min_news_coverage,
                seed_model_path=(a.seed_model_path or None),
            )
        )
    )
    p = sub.add_parser(
        "data-sync",
        help="Fetch and store price/news data",
        description="Sync prices and news for a run and enforce min_news_coverage.",
    )
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(data_sync(a.run_id)))
    p = sub.add_parser(
        "experiments-list",
        help="List experiments for a run",
        description="List experiments for a run, optionally filtered by status.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--status", default="")
    p.set_defaults(func=lambda a: _print(experiments_list(a.run_id, status=(a.status or None))))
    p = sub.add_parser(
        "experiment-run",
        help="Run a single model experiment",
        description="Execute one experiment for a specific model in a run.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--model_id", required=True)
    p.set_defaults(func=lambda a: _print(experiment_run(a.run_id, a.model_id)))
    p = sub.add_parser(
        "generation-run",
        help="Run pending experiments in generation",
        description="Execute pending experiments up to configured limits for the current generation.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--max_workers", type=int, default=0)
    p.set_defaults(func=lambda a: _print(generation_run(a.run_id, max_workers=(a.max_workers or None))))
    p = sub.add_parser(
        "model-create",
        help="Register a validated model",
        description="Create and register a model file in the run with lineage metadata.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--reasoning", default="")
    p.add_argument("--generation", type=int, default=-1)
    p.add_argument("--parent_id", default="")
    p.set_defaults(
        func=lambda a: _print(
            model_create(
                a.run_id,
                a.name,
                a.content,
                a.log,
                a.reasoning,
                generation=(None if a.generation < 0 else a.generation),
                parent_id=(a.parent_id or None),
            )
        )
    )
    p = sub.add_parser(
        "model-list",
        help="List models in a run",
        description="Return all registered models for a run.",
    )
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(model_list(a.run_id)))
    p = sub.add_parser(
        "model-read",
        help="Read model metadata and source",
        description="Read model metadata and source code for a model id.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--model_id", required=True)
    p.set_defaults(func=lambda a: _print(model_read(a.run_id, a.model_id)))
    p = sub.add_parser(
        "model-validate",
        help="Validate candidate model file",
        description="Validate a candidate model file against runtime and contract constraints.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--file_path", required=True)
    p.set_defaults(func=lambda a: _print(model_validate(a.run_id, a.file_path)))
    p = sub.add_parser(
        "get-learning-tree",
        help="Get model lineage and learning tree",
        description="Return learning tree and lineage metrics for model selection decisions.",
    )
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(get_learning_tree(a.run_id)))
    p = sub.add_parser(
        "predictions-read",
        help="Read predictions for a run",
        description="Read predictions filtered by model id and optional date range.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--model_id", default="")
    p.add_argument("--date_from", default="")
    p.add_argument("--date_to", default="")
    p.set_defaults(func=lambda a: _print(predictions_read(a.run_id, model_id=(a.model_id or None), date_from=(a.date_from or None), date_to=(a.date_to or None))))
    p = sub.add_parser(
        "visualize",
        help="Generate run charts",
        description="Generate visualization charts for run experiments and performance.",
    )
    p.add_argument("--run_id", required=True)
    p.add_argument("--output", default="")
    p.set_defaults(func=lambda a: _print(visualize(a.run_id, output=(a.output or None))))
    p = sub.add_parser(
        "config-get",
        help="Read run configuration",
        description="Return the saved settings snapshot for a run.",
    )
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(config_get(a.run_id)))
    p = sub.add_parser(
        "generation-state",
        help="Read current generation status",
        description="Return generation progress and pending/completed counts for a run.",
    )
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(get_generation_state(a.run_id)))
    p = sub.add_parser(
        "runs-summary",
        help="Summarize all runs",
        description="Return summary metrics across available runs.",
    )
    p.set_defaults(func=lambda a: _print(runs_summary()))
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
