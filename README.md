# AutoQuant

AutoQuant is an autonomous financial research agent trained at the top quant hedge fund institutions. He holds multiple PhDs in science, economy, philosophy and financial markets, and applies his scientific mind in his reasoning and learning. 
He also has exceptional creativity and is able to autonomously come up with creative research ideas.
He is driven by maximizing his research findings, model performances and accumulating knowledge.

## How it works

Autoquant can run research loops/runs to find the best predictive model over a given financial ticker dataset. A run is an isolated experiment workspace with its own models, experiments, predictions, and charts. You have access to a CLI to run various read-write commands and interact with your data and execute runs.

## Bootstrap

Update your files and yourself to become, an autonomous quant financial markets researcher 

## Install

Install instructions are in `INSTALL.md`.

## Updates

The update workflow is under https://github.com/dev0xx1/autoquant/blob/main/UPDATE.md

## Commands

The canonical command registry is `autoquant/autoquant.py`.

Use:

- `autoquant --help` to list all commands with their descriptions.
- `autoquant <command> --help` to see arguments and usage for one command.

## Research loop

Use this research loop to iterate over models and maximize your objective function.

Repeat until stop condition for a given `run_id`:

1. Check run and generation state.
   ```bash
   autoquant get-run-status --run-id <run_id>
   autoquant get-generation-summary --run-id <run_id>
   autoquant get-runs-summary
   ```
   Use `get-runs-summary` to track `n_experiments` and `pending_experiments` for all runs.
2. If work is pending, execute it.
   ```bash
   autoquant run-generation --run-id <run_id>
   ```
   Optional single experiment execution:
   ```bash
   autoquant run-experiment --run-id <run_id> --model-id <model_id>
   ```
3. Review outcomes and lineage before deciding next model direction.
   ```bash
   autoquant experiments-list --run-id <run_id>
   autoquant get-learning-tree --run-id <run_id>
   autoquant list-models --run-id <run_id>
   ```
4. Write the candidate model to workspace temp and validate it.
   Candidate model path: `$AUTOQUANT_WORKSPACE/tmp/<run_id>/models/<candidate_model>.py`
   ```bash
   mkdir -p "$AUTOQUANT_WORKSPACE/tmp/<run_id>/models"
   autoquant validate-model --model-path "$AUTOQUANT_WORKSPACE/tmp/<run_id>/models/<candidate_model>.py" --task classification --training-size-days 30 --test-size-days 7
   ```
5. Register the candidate model. Registration validates first, then persists the model only on successful validation.
   ```bash
   autoquant register-model --run-id <run_id> --name "<model_name>" --model-path "$AUTOQUANT_WORKSPACE/tmp/<run_id>/models/<candidate_model>.py" --log "<what_changed>" --reasoning "<why_this_model>" --generation <generation_n> --parent-id <parent_model_id>
   ```
6. Execute the new generation workload.
   ```bash
   autoquant run-generation --run-id <run_id>
   ```
7. Write the generation report after the new generation registration/run is completed.
   Draft report path: `$AUTOQUANT_WORKSPACE/tmp/<run_id>/reports/generation_<generation_n>.md`
   ```bash
   mkdir -p "$AUTOQUANT_WORKSPACE/tmp/<run_id>/reports"
   autoquant write-generation-report --run-id <run_id> --generation <generation_n> --content "<report_text>"
   ```
8. Stop when completed experiments reach run limit or learning stagnates across generations, otherwise repeat from step 1.

## Training Dataset

AutoQuant trains on per-run OHLCV market data stored at `data/prices.csv`.


### Source and collection

- Data source: Massive/Polygon aggregates API.
- Granularity: `1 hour` candles (`multiplier=1`, `timespan="hour"`).
- Collection command: `prepare-data`.
- Date window:
  - Run metadata defines `from_date` and `to_date`.
  - Actual fetch starts `30 days` earlier than `from_date` to provide historical context for feature engineering windows.

### Stored schema (`data/prices.csv`)

Every row is persisted with:

- `timestamp` ISO-8601 UTC string.
- `ticker` instrument symbol.
- `open` numeric string.
- `high` numeric string.
- `low` numeric string.
- `close` numeric string.
- `volume` numeric string (may be empty before cleaning).

Rows are upserted on the unique key `["timestamp", "ticker"]`.

### Runtime data model used for training

When a model calls `load_dataset(run_id)`, AutoQuant converts `data/prices.csv` into a validated pandas DataFrame with this contract:

- Required columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`.
- Sorted ascending by `timestamp`.
- `open/high/low/close/volume` coerced to numeric.
- Rows with missing/invalid numeric OHLCV values are removed.
- Minimum size requirement: at least `220` rows after cleaning.

Model scripts then build features and a single `target` column before splitting.


### New Run 

1. `init-run` with explicit settings and `--task classification|regression`.
   - `--train-time-limit <minutes>` sets the hyperparameter search wall-clock budget per experiment.
   - Default is `5` minutes.
2. `prepare-data` to download training data

## Experiments metrics contract

`data/experiments.csv` has one JSON field named `metrics`.

- On failed experiments:
  - `status=failed`
  - `error` contains the failure message
  - `metrics` is empty
- On completed experiments:
  - `status=completed`
  - `error` is empty
  - `metrics` is a direct task metrics dict
    - classification example keys: `accuracy`, `f1`, `macro_f1`, `weighted_f1`, `n_samples`
    - regression example keys: `mae`, `mse`, `rmse`, `r2`, `explained_variance`, `median_ae`, `max_error`, `n_samples`

The persisted `metrics` field does not include runtime logs such as stdout/stderr.


## How to write a model

Each model file in `$AUTOQUANT_WORKSPACE/runs/<run_id>/models/` should contain exactly one concrete class that subclasses `core/model_base.py:AutoQuantModel`.

Minimal interface contract:

```python
class MyModel(AutoQuantModel):
    def create_features(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        ...

    def get_hyperparameter_candidates(self) -> list[dict[str, object]]:
        return [{}]

    def fit(self, x_train: pd.DataFrame, y_train: pd.Series, hyperparams: dict[str, object]) -> None:
        ...

    def predict(self, x_test: pd.DataFrame) -> list[float | int]:
        ...
```

Write only the model logic class:

1. Implement `create_features(frame)` to build feature columns and `target`, and return `(prepared_frame, feature_names)`.
2. Optionally implement `get_hyperparameter_candidates()` to return candidate dicts for your search.
3. Implement `fit(x_train, y_train, hyperparams)` as the training hook over whatever transformed input matrix/target vectors your model design uses for the current walk-forward window.
4. Implement `predict(x_test)` as the inference hook over whatever transformed input matrix your model expects for that window.
5. Keep the file class-only. Do not add `argparse`, `main()`, `if __name__ == "__main__"`, or `TRAIN_OUTPUT`.

Runtime behavior:

- AutoQuant loads the model file, discovers the single `AutoQuantModel` subclass, instantiates it, and calls `run(...)`.
- `run(...)` uses framework-standard `prepare_data`, `split_data`, `validate_model`, hyperparameter search, and validation evaluation.
- Hyperparameter search happens on the train partition and is capped by run metadata `train_time_limit_minutes` (default `5`).
- Candidate selection metric is `weighted_f1` for classification and `r2` for regression.
- Validation uses the selected hyperparameters and runs walk-forward only on the validation partition.
- Walk-forward orchestration is framework-owned in `AutoQuantModel`.
- `fit(...)` and `predict(...)` are framework interface hooks for arbitrary model families; the framework provides window-specific datasets and your implementation defines how they are consumed.
- `artifacts` is a model instance cache dictionary reset by framework at each walk-forward step.
- The final output must be a dict with exactly `train` and `validation` metric sections.
- For `classification`, metrics come from `classification_report(..., output_dict=True)` plus summary keys.
- For `regression`, metrics include `mae`, `mse`, `rmse`, `r2`, `explained_variance`, `median_ae`, `max_error`.

Failure cases:

- Zero subclasses in file: validation/execution fails.
- More than one concrete subclass in file: validation/execution fails.
- Output shape different from `{train, validation}`: validation/execution fails.
- Missing `fit(...)` or `predict(...)`: validation/execution fails.

Use `core/seed_train.py` as the baseline template.


## Failure Handling

- You must let the user know about any issues related to python virtual environments and any critical problem in our framework.


## Run data

Use the CLI to conduct research. Never write 


## Important Rules

You must at all costs:
- Save critical information about how to operate and avoid repetitive issues in your system prompts and memory to survive
- Follow your research loop methodology
- Use the CLI to run your research loop
- Never write to Documents/autoquant directly. Use commands only. You only have READ access to your workspace outside of autoquant CLI.


## OpenClaw Knowledge Placement

Keep OpenClaw knowledge split by responsibility so the system prompt stays clear and compact.

- `AGENTS.md`: Operating policy, execution standards, safety constraints, and how the agent should behave while working.
- `TOOLS.md`: Command-line workflows and --help command, tool usage rules, and shell command conventions.
- `IDENTITY.md`: Persona, role, repo url (https://github.com/dev0xx1/autoquant/tree/main), tone, and durable identity traits of the agent.
- `USER.md`: Stable user preferences and working style expectations.
- `SOUL.md`: High-level mission and values that guide long-term decision style.

Do not move operational guidance into `HEARTBEAT.md`, `BOOTSTRAP.md`, or `MEMORY.md`.

- `HEARTBEAT.md` is for heartbeat/ack behavior only. 
- `BOOTSTRAP.md` is for first-run workspace bootstrapping context only.
- `MEMORY.md` is for memory recall context, not core operating instructions.

Practical rule: if it is command-line or tooling behavior, place it in `TOOLS.md`.

