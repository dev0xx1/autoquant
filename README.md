# AutoQuant

AutoQuant is an autonomous financial research agent that predicts next-day direction for one ticker over a configured date range using price and news data. A run is an isolated experiment workspace with its own models, experiments, predictions, and charts.

All commands return JSON and are designed to be called by an agent loop.


## Boostrap

Run your bootstrap and soul identity to be autoquant, an autonomous quant financial markets researcher trained at the top quant hedge fund institutions like Renaissance Technologies, Bridgewater and the likes. Autoquant has scientific reasoning and exceptional creativity.


## Setup

Setup goals:

- Run your bootstrap.md based on these README instructions.
- Clone the repo.
- Create a virtual environment and install dependencies.
- Create a local script to easily call commands.
- Setup environment vars safely


1. Create the workspace, clone the repo, and enter the project directory:
   ```bash
   export AUTOQUANT_WORKSPACE="${AUTOQUANT_WORKSPACE:-$HOME/Documents/autoquant}"
   mkdir -p "$AUTOQUANT_WORKSPACE"
   git clone <repo-url> "$AUTOQUANT_WORKSPACE/autoquant"
   cd "$AUTOQUANT_WORKSPACE/autoquant"
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   mkdir -p "$AUTOQUANT_WORKSPACE/venv"
   python3 -m venv "$AUTOQUANT_WORKSPACE/venv/autoquant"
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/pip" install -r requirements.txt
   ```

3. Create the launcher script:
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
4. Set environment variables:
   - Required keys listed in `autoquant/.env.example` must be added to openclaw.json
   - Ask API keys from user or let him update the env vars directly

5. Verify installation:
   ```bash
   ./autoquant --help
   ```

## Commands

The canonical command registry is `autoquant/autoquant.py`.

Use:

- `./autoquant --help` to list all commands with their descriptions.
- `./autoquant <command> --help` to see arguments and usage for one command.


## Research loop

Use this research loop to maximize predictive power and the objective function over the 
training set.

### New Run 

1. `run-init` with explicit settings.
2. `data-sync`.
3. If `data-sync` fails on news coverage, stop and report the error.
4. `generation-run` once to execute pending seed experiments.

### Autonomous Loop

Repeat until stop condition. Can run for existing run_id.

1. Get state of latest generation: `generation-state --run_id <id>`.
2. Stop if:
   - completed experiments reached `max_experiments`
   - or we stop learning for more than 5 generations
else if we have pending experiments we do `generation-run --run_id <id>`
3. `get-learning-tree --run_id <id>` to review results and your learning history to decide
on the next generation of models
4. Create the next generation of models to `~/Documents/generated_models/<uuid>.py`.
5. For each model:
   - `model-validate`
   - if invalid, fix file and re-run `model-validate`
   - if valid, `model-create` with explicit `--parent_id` and `--generation`
6. `generation-run --run_id <id>`.
7. `experiments-list --run_id <id> --status pending` and `generation-state --run_id <id>`.
8. `visualize --run_id <id>`
9. `runs-summary`
10. Continue from step 1.



## Model Contract

Each model is a Python file under `$AUTOQUANT_WORKSPACE/runs/<run_id>/models/` and must define:

- `price_lookback_window_days` as integer
- `predictor_model` as string, and it must be in `available_predictor_models` from run settings
- `temperature` as float
- `prompt` as non-empty string
- `process_prices(price_rows)` as callable returning a `dict`

Validation constraints:

- Imports are restricted to `math`, `statistics`, `typing`, `datetime`, and `__future__`
- Disallowed dynamic and system calls are rejected during validation
- `price_lookback_window_days` is constrained to `1..30`

Use `core/seed_model.py` as the baseline template.


## Failure Handling

- You must let the user know about any issues related to python virtual environments and any critical problem in our framework.


## Run Layout

Each run creates `$AUTOQUANT_WORKSPACE/runs/<run_id>/`:

- `meta.json`
- `settings.json`
- `data/news.csv`
- `data/prices.csv`
- `data/models.csv`
- `data/predictions.csv`
- `data/experiments.csv`
- `data/data_report.txt`
- `models/*.py`
- `charts/*.png`
