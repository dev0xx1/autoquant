from __future__ import annotations

import csv
import json
from pathlib import Path
from threading import Lock
from typing import Any

CSV_LOCK = Lock()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            return []
        return list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, fieldnames: list[str], key_fields: list[str], rows: list[dict[str, str]]) -> None:
    with CSV_LOCK:
        existing_rows = read_csv(path)
        index: dict[tuple[str, ...], dict[str, str]] = {}
        for row in existing_rows:
            if all(key in row and row[key] != "" for key in key_fields):
                index[tuple(row[key] for key in key_fields)] = {field: str(row.get(field, "") or "") for field in fieldnames}
        for row in rows:
            normalized = {field: str(row.get(field, "") or "") for field in fieldnames}
            if all(normalized.get(key, "") != "" for key in key_fields):
                index[tuple(normalized[key] for key in key_fields)] = normalized
        write_csv(path, fieldnames, list(index.values()))


def ensure_csv_header(path: Path, fieldnames: list[str]) -> None:
    if not path.exists() or path.stat().st_size == 0:
        write_csv(path, fieldnames, [])


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
