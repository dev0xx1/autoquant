from __future__ import annotations

from pathlib import Path
from typing import Any

from core.paths import run_dir
from core.research import generate_learning_chart


def visualize_learning(run_id: str, output: str | None = None) -> dict[str, Any]:
    target_run_dir = run_dir(run_id)
    out_path = Path(output).resolve() if output else None
    result = generate_learning_chart(target_run_dir, output_path=out_path)
    return {"run_id": run_id, "visualization_path": str(result)}
