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
from core.schemas import Settings

def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=True))


def main() -> None:
    defaults = Settings()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run-init")
    p.add_argument("--run_id", required=True)
    p.add_argument("--ticker", required=True)
    p.add_argument("--from_date", required=True)
    p.add_argument("--to_date", required=True)
    p.add_argument("--available_predictor_models", nargs="+", default=defaults.available_predictor_models)
    p.add_argument("--llm_temperature", type=float, default=defaults.llm_temperature)
    p.add_argument("--llm_max_tokens", type=int, default=defaults.llm_max_tokens)
    p.add_argument("--generation_sample_size", type=int, default=defaults.generation_sample_size)
    p.add_argument("--max_experiments", type=int, default=defaults.max_experiments)
    p.add_argument("--max_concurrent_models", type=int, default=defaults.max_concurrent_models)
    p.add_argument("--prediction_time", default=defaults.prediction_time)
    p.add_argument("--prediction_time_timezone", default=defaults.prediction_time_timezone)
    p.add_argument("--objective_function", choices=["accuracy", "f1", "macro_f1", "weighted_f1"], default=defaults.objective_function)
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
                a.generation_sample_size,
                a.max_experiments,
                a.max_concurrent_models,
                a.prediction_time,
                a.prediction_time_timezone,
                a.objective_function,
            )
        )
    )
    p = sub.add_parser("data-sync")
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(data_sync(a.run_id)))
    p = sub.add_parser("experiments-list")
    p.add_argument("--run_id", required=True)
    p.add_argument("--status", default="")
    p.set_defaults(func=lambda a: _print(experiments_list(a.run_id, status=(a.status or None))))
    p = sub.add_parser("experiment-run")
    p.add_argument("--run_id", required=True)
    p.add_argument("--model_id", required=True)
    p.set_defaults(func=lambda a: _print(experiment_run(a.run_id, a.model_id)))
    p = sub.add_parser("generation-run")
    p.add_argument("--run_id", required=True)
    p.add_argument("--max_workers", type=int, default=0)
    p.set_defaults(func=lambda a: _print(generation_run(a.run_id, max_workers=(a.max_workers or None))))
    p = sub.add_parser("model-create")
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
    p = sub.add_parser("model-list")
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(model_list(a.run_id)))
    p = sub.add_parser("model-read")
    p.add_argument("--run_id", required=True)
    p.add_argument("--model_id", required=True)
    p.set_defaults(func=lambda a: _print(model_read(a.run_id, a.model_id)))
    p = sub.add_parser("model-validate")
    p.add_argument("--run_id", required=True)
    p.add_argument("--model_id", required=True)
    p.set_defaults(func=lambda a: _print(model_validate(a.run_id, a.model_id)))
    p = sub.add_parser("get-learning-tree")
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(get_learning_tree(a.run_id)))
    p = sub.add_parser("predictions-read")
    p.add_argument("--run_id", required=True)
    p.add_argument("--model_id", default="")
    p.add_argument("--date_from", default="")
    p.add_argument("--date_to", default="")
    p.set_defaults(func=lambda a: _print(predictions_read(a.run_id, model_id=(a.model_id or None), date_from=(a.date_from or None), date_to=(a.date_to or None))))
    p = sub.add_parser("visualize")
    p.add_argument("--run_id", required=True)
    p.add_argument("--output", default="")
    p.set_defaults(func=lambda a: _print(visualize(a.run_id, output=(a.output or None))))
    p = sub.add_parser("config-get")
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(config_get(a.run_id)))
    p = sub.add_parser("generation-state")
    p.add_argument("--run_id", required=True)
    p.set_defaults(func=lambda a: _print(get_generation_state(a.run_id)))
    p = sub.add_parser("runs-summary")
    p.set_defaults(func=lambda a: _print(runs_summary()))
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
