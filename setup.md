# AutoClaw Setup

This guide is for a fresh OpenClaw agent that needs to run as `AutoClaw` for the `autoquant` project.

## 1) Publish autoquant as a public git repo

Run these steps once from the maintainer machine.

```bash
cd /path/to/ai_trader
git init
git add autoquant
git commit -m "Initialize autoquant project"
git branch -M main
gh repo create autoquant --public --source=. --remote=origin --push
```

If `autoquant/.env` contains secrets, do not commit it. Create and commit `autoquant/.env.example` instead.

## 2) Fresh OpenClaw workspace bootstrap

```bash
mkdir -p /tmp/autoclaw-workspace
cd /tmp/autoclaw-workspace
git clone https://github.com/<org-or-user>/autoquant.git
cd autoquant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

If `.env.example` does not exist, ask the maintainer for required keys and create `.env` manually.

## 3) Identity and mission

The agent identity is `AutoClaw`.

Primary mission:
- Run iterative model research for next-24h UP/DOWN prediction.
- Use `autoquant.py` commands only.
- Keep all outputs machine-readable and JSON-based.

## 4) Mandatory first actions in every new session

1. Read `README.md` fully before taking any action.
2. Read `autoquant.py` to confirm command signatures.
3. Run `python autoquant.py --help` to verify runtime.
4. Call `/status` then `/context list` to inspect context budget.

Reason: OpenClaw context is bounded and includes system prompt, chat history, tool schemas, and tool results, so early context inspection keeps runs stable and avoids truncation issues.

## 5) Repo concepts the agent must know

- `autoquant.py`: CLI entrypoint and official command surface.
- `core/commands.py`: operational functions backing all CLI commands.
- `core/schemas.py`: typed payload/state objects.
- `core/prediction_time.py`: prediction window/time conversion logic.
- `core/research.py`: generation and scoring logic.
- `core/storage.py`: CSV persistence.

## 6) Canonical execution loop

For a run id like `nvda_feb`:

1. `run-init`
2. `data-sync`
3. `generation-run`
4. `model-scoreboard`
5. Propose new candidate model files
6. `model-create` for each candidate
7. `model-validate` for each candidate
8. `generation-run`
9. Repeat from scoreboard until stop condition or `max_experiments`
10. `visualize`
11. Final `model-scoreboard`

This mirrors the framework runbook and keeps the process deterministic.

## 7) Command checklist

Use only these commands:

- `run-init`
- `data-sync`
- `experiments-list`
- `experiment-run`
- `generation-run`
- `model-create`
- `model-list`
- `model-read`
- `model-validate`
- `model-scoreboard`
- `predictions-read`
- `visualize`
- `config-get`
- `generation-state`
- `runs-summary`

## 8) Agent loop and context discipline

OpenClaw runs as a serialized agent loop per session. Use this behavior deliberately:

- Keep one objective per session lane.
- Avoid unrelated tool spam.
- Use `/context detail` when sessions become long.
- Use `/compact` before context saturation.
- Prefer short factual outputs over long narrative logs.

## 9) Output contract for AutoClaw

For each action:

- Echo exact command run.
- Return raw JSON result.
- Add a short decision line: `continue`, `retry`, or `stop`.
- If failing, include a single actionable fix and rerun.

## 10) Start template for a new AutoClaw run

Use this exact sequence:

```bash
python autoquant.py run-init --run_id <run_id> --ticker <ticker> --from_date <yyyy-mm-dd> --to_date <yyyy-mm-dd> --available_predictor_models <model_a> --generation_sample_size <n> --max_experiments <n> --max_concurrent_models <n> --prediction_time 17:00 --prediction_time_timezone UTC
python autoquant.py data-sync --run_id <run_id>
python autoquant.py generation-run --run_id <run_id>
python autoquant.py model-scoreboard --run_id <run_id>
python autoquant.py generation-state --run_id <run_id>
```

## 11) Hard rules

- Never invent commands not present in `autoquant.py`.
- Never skip reading `README.md` at session start.
- Never mutate run artifacts outside provided commands unless explicitly requested.
- Never commit secrets.
- Always keep behavior reproducible from command history.
