# AutoQuant

AutoQuant is an autonomous financial research agent that predicts next-day direction for one ticker over a configured date range using price and news data. A run is an isolated experiment workspace with its own models, experiments, predictions, and charts.

All commands return JSON and are designed to be called by an agent loop.

## Setup

Setup goals:

Clone the repo.
Create a virtual environment and install dependencies.
Create a local script to easily call commands.
Setup environment vars safely


1. Clone the repo and enter the project directory:
   ```bash
   git clone <repo-url>
   cd autoquant
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .autoquantvenv
   .autoquantvenv/bin/pip install -r requirements.txt
   ```

3. Create the launcher script:
   ```bash
   cat > autoquant <<'EOF'
   #!/usr/bin/env bash
   set -euo pipefail
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   "$SCRIPT_DIR/.autoquantvenv/bin/python" "$SCRIPT_DIR/autoquant.py" "$@"
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

## Model Contract

Each model is a Python file under `~/Documents/autoquant/runs/<run_id>/models/` and must define:

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

## Commands

The canonical command registry is `autoquant/autoquant.py`.

Use:

- `./autoquant --help` to list all commands with their descriptions.
- `./autoquant <command> --help` to see arguments and usage for one command.


## Research loop

Use this research loop logic

### New Run Bootstrap

1. `run-init` with explicit settings.
2. `data-sync`.
3. If `data-sync` fails on news coverage, stop and report the error.
4. `generation-run` once to execute pending seed experiments.

### Iterative Research Loop

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


## Failure Handling

- You must let the user know about any issues related to python virtual environments and any critical problem in our framework.


## Run Layout

Each run creates `~/Documents/autoquant/runs/<run_id>/`:

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
