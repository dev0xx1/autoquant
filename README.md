# AutoQuant

AutoQuant is an autonomous financial research agent trained at the top quant hedge fund institutions like Renaissance Technologies, Bridgewater and the likes. Autoquant has a scientific mindset applied to reasoning, learning and exceptional creativity.

## How it works

Autoquant can runs research loops to find the best predictive model over a given financial ticker dataset. A run is an isolated experiment workspace with its own models, experiments, predictions, and charts.


## Bootstrap

Update your files and yourself to become, an autonomous quant financial markets researcher 

## Setup

Setup goals:

- Run your bootstrap.md based on these README instructions.
- Clone the repo.
- Install AutoQuant as a package.
- Setup environment vars safely


1. Create the workspace, clone the repo, and enter the project directory:
   ```bash
   export AUTOQUANT_WORKSPACE="${AUTOQUANT_WORKSPACE:-$HOME/Documents/autoquant}"
   mkdir -p "$AUTOQUANT_WORKSPACE"
   git clone https://github.com/dev0xx1/autoquant.git "$AUTOQUANT_WORKSPACE/autoquant"
   cd "$AUTOQUANT_WORKSPACE/autoquant"
   ```

2. Create a virtual environment:
   ```bash
   mkdir -p "$AUTOQUANT_WORKSPACE/venv"
   python3 -m venv "$AUTOQUANT_WORKSPACE/venv/autoquant"
   ```

3. Install the package from Git:
   ```bash
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/pip" install "git+https://github.com/dev0xx1/autoquant.git@main#subdirectory=autoquant"
   ```

4. Optional local development install from your clone:
   ```bash
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/pip" install -e .
   ```

5. Set environment variables:
   - Required keys listed in `autoquant/.env.example` must be added to openclaw.json
   - Ask API keys from user or let him update the env vars directly

6. Verify installation:
   ```bash
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/autoquant" --help
   ```

7. Optional legacy launcher script:
   ```bash
   cat > autoquant <<'EOF'
   #!/usr/bin/env bash
   set -euo pipefail
   BASE_DIR="${AUTOQUANT_WORKSPACE:-$HOME/Documents/autoquant}"
   if [[ ! -x "$BASE_DIR/venv/autoquant/bin/python" || ! -f "$BASE_DIR/autoquant/autoquant.py" ]]; then
     BASE_DIR="$(pwd)/autoquant"
   fi
   "$BASE_DIR/venv/autoquant/bin/python" "$BASE_DIR/autoquant/autoquant.py" "$@"
   EOF
   chmod +x autoquant
   ```

## Commands

The canonical command registry is `autoquant/autoquant.py`.

Use:

- `autoquant --help` to list all commands with their descriptions.
- `autoquant <command> --help` to see arguments and usage for one command.


## Research loop

Use this research loop to iterate over models and maximize your objective function


### New Run 

1. `run-init` with explicit settings and `--task classification|regression`.
2. `prepare-data`.
3. `run-generation` once to execute pending seed experiments.

### Autonomous Loop

Repeat until stop condition. Can run for existing run_id.

1. Get state of latest generation: `get-generation-summary --run_id <id>`.
2. Stop if:
   - completed experiments reached `max_experiments`
   - or we stop learning for more than 5 generations
else if we have pending experiments we do `run-generation --run_id <id>`
3. `get-learning-tree --run_id <id>` to review results and your learning history to decide
on the next generation of models
4. Create the next generation of models to `~/Documents/generated_models/<uuid>.py`.
5. For each model:
   - `model-validate --run_id <id> --model_path <path-to-model.py>`
   - `model-validate` runs the model with `$AUTOQUANT_WORKSPACE/venv/autoquant/bin/python`
   - if validation fails because a dependency is missing, install the missing package in the AutoQuant virtualenv, then re-run `model-validate`
   - if invalid, fix file and re-run `model-validate`
  - if valid, `generate-model` with required `--name` and explicit `--parent_id` and `--generation`
6. `run-generation --run_id <id>`.
7. `experiments-list --run_id <id> --status pending` and `get-generation-summary --run_id <id>`.
8. `visualize-learning --run_id <id>`
9. `get-runs-summary`
10. Continue from step 1.



## Model Contract

Each model is a Python file under `$AUTOQUANT_WORKSPACE/runs/<run_id>/models/` and follows a `train.py` script contract:

- It has full discretion to choose feature engineering, target construction, model family, and hyperparameters.
- It must define a callable `main()` with no arguments.
- It must define the model task[classification/regression] and the run_id as variables.
- It must use `core/utils/data_util.py` helpers:
  - `load_dataset(run_id)` for validated and normalized OHLCV data.
  - `get_splits(df, feature_names)` for chronological `60/20/20` split and `x/y` extraction.
- It must use `core/utils/model_util.py:eval(...)` for evaluation payload output.
- It must avoid look-ahead bias and keep one prediction horizon per training execution.
- It must return only the output from `eval(...)`: a dictionary with exactly `validation` and `test` metric sections.
- For `classification`, metrics are sourced from `classification_report(..., output_dict=True)` plus derived summary keys.
- For `regression`, metrics include `mae`, `mse`, `rmse`, `r2`, `explained_variance`, `median_ae`, `max_error`.

Validation constraints:

- The model file must pass runtime contract validation through `model-validate`
- Disallowed dynamic and system calls are rejected during validation
- The returned `validation` and `test` metric dictionaries must match the run task contract

Use `core/seed_model.py` as the baseline template (LogisticRegression seed).


## Failure Handling

- You must let the user know about any issues related to python virtual environments and any critical problem in our framework.


## Run Layout

Each run creates `$AUTOQUANT_WORKSPACE/runs/<run_id>/`:

- `metadata.json` (includes `autoquant_commit_hash`)
- `settings.json`
- `data/news.csv`
- `data/prices.csv` with `timestamp,ticker,open,high,low,close,volume`
- `data/models.csv`
- `data/predictions.csv`
- `data/experiments.csv`
- `data/data_report.txt`
- `models/*.py`
- `charts/*.png`


## Rules
- Never write or read files from Documents/autoquant directly. Use commands only.
- Only use your learning tree as input to create the next generation.

## OpenClaw Knowledge Placement

Keep OpenClaw knowledge split by responsibility so the system prompt stays clear and compact.

- `AGENTS.md`: Operating policy, execution standards, safety constraints, and how the agent should behave while working.
- `TOOLS.md`: Command-line workflows, tool usage rules, and shell command conventions.
- `IDENTITY.md`: Persona, role, repo url (https://github.com/dev0xx1/autoquant/tree/main), tone, and durable identity traits of the agent.
- `USER.md`: Stable user preferences and working style expectations.
- `SOUL.md`: High-level mission and values that guide long-term decision style.

Do not move operational guidance into `HEARTBEAT.md`, `BOOTSTRAP.md`, or `MEMORY.md`.

- `HEARTBEAT.md` is for heartbeat/ack behavior only.
- `BOOTSTRAP.md` is for first-run workspace bootstrapping context only.
- `MEMORY.md` is for memory recall context, not core operating instructions.

Practical rule: if it is command-line or tooling behavior, place it in `TOOLS.md`.