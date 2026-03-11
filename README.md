# AutoQuant

OpenClaw-driven research framework for UP/DOWN next-24h prediction with isolated run folders.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill keys.
3. Set run settings via `run-init` args (`generation_sample_size`, `max_experiments`, `max_concurrent_models`, etc.).

## Model contract

Each model is a Python file under `<runs_root>/<run_id>/models/` (default: `~/Documents/autoquant/runs/<run_id>/models/`) and must define:

```python
price_lookback_window_days = 7  # 1-30
predictor_model = "gemini/gemini-2.5-flash"  # must be one of available_predictor_models in config
temperature = 0.2

prompt = """
system prompt string
"""


def process_prices(price_rows):
    return {"feature_name": 1.23}
```

`process_prices` receives price rows for the last `price_lookback_window_days` days. News in context is always the past 24 hours. Run settings list allowed LLMs in `available_predictor_models`; each model sets `predictor_model` to one of them.

## Commands

- `python autoquant.py run-init --run_id nvda_feb --ticker NVDA --from_date 2026-02-01 --to_date 2026-02-28 --available_predictor_models gemini/gemini-2.5-flash --generation_sample_size 4 --max_experiments 8 --max_concurrent_models 4 --prediction_time 17:00 --prediction_time_timezone UTC`
- `python autoquant.py data-sync --run_id nvda_feb`
- `python autoquant.py experiments-list --run_id nvda_feb --status pending`
- `python autoquant.py generation-run --run_id nvda_feb`
- `python autoquant.py model-scoreboard --run_id nvda_feb`
- `python autoquant.py model-create --run_id nvda_feb --name g1_m0 --content "$(cat candidate.py)" --log "gen1 idea" --reasoning "feature update"`
- `python autoquant.py model-validate --run_id nvda_feb --model_id g1_m0`
- `python autoquant.py model-list --run_id nvda_feb`
- `python autoquant.py model-read --run_id nvda_feb --model_id g1_m0`
- `python autoquant.py experiment-run --run_id nvda_feb --model_id g1_m0`
- `python autoquant.py predictions-read --run_id nvda_feb --model_id g1_m0`
- `python autoquant.py visualize --run_id nvda_feb`
- `python autoquant.py runs-summary`
- `python autoquant.py config-get --run_id nvda_feb`
- `python autoquant.py generation-state --run_id nvda_feb`

All command outputs are JSON.

## OpenClaw runbook

1. `run-init`
2. `data-sync`
3. `generation-run` to execute pending experiments in current generation
4. `model-scoreboard`
5. OpenClaw proposes `generation_sample_size` new model files for next generation
6. `model-create` for each candidate
7. `model-validate` for each candidate
8. `generation-run`
9. Repeat from step 4 until `max_experiments` or OpenClaw stop condition
10. `visualize` and final `model-scoreboard`

## Run layout

Each run creates `<runs_root>/<run_id>/` (default: `~/Documents/autoquant/runs/<run_id>/`) with:
- `meta.json`
- `settings.json`
- `data/news.csv`, `data/prices.csv`, `data/models.csv`, `data/predictions.csv`, `data/experiments.csv`
- `models/*.py`
- `charts/*.png`
