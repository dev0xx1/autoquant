from __future__ import annotations

from typing import Any

from core.utils.io_util import write_text

from .shared import ensure_run_layout, generation_report_path, read_run_meta


def _report_content(generation: int, content: str) -> str:
    body = content.strip()
    if body:
        return body + "\n"
    return (
        f"# Generation {generation}\n\n"
        "## What I learned\n\n"
        "## How this informs the next generation\n\n"
        "## Next generation plan\n"
    )


def write_generation_report(run_id: str, generation: int, content: str) -> dict[str, Any]:
    read_run_meta(run_id)
    target_run_dir = generation_report_path(run_id, generation).parent.parent
    ensure_run_layout(target_run_dir)
    path = generation_report_path(run_id, generation)
    write_text(path, _report_content(generation, content))
    return {"run_id": run_id, "generation": generation, "report_path": str(path)}
