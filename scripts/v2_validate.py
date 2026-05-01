#!/usr/bin/env python3
"""Validate ClawBench V2 JSONL, task schema, and data/task consistency."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data-v2" / "clawbench_all_verified.jsonl"
TASKS_DIR = ROOT / "test-cases-v2"
TASK_SCHEMA_PATH = ROOT / "test-cases" / "task.schema.json"
CORE_FIELDS = ("instruction", "eval_schema", "time_limit", "extra_info", "metadata")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def task_id_from_dir(task_dir: Path) -> str:
    return task_dir.name.removeprefix("v2-")


def rel_path_errors(task_id: str, task_dir: Path, task: dict) -> list[str]:
    errors: list[str] = []
    for index, item in enumerate(task.get("extra_info", [])):
        if not isinstance(item, dict):
            errors.append(f"{task_id}: extra_info[{index}] is not an object")
            continue
        rel = item.get("path")
        if not rel:
            continue
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"{task_id}: unsafe extra_info path {rel!r}")
            continue
        if not (task_dir / path).is_file():
            errors.append(f"{task_id}: missing extra_info file {rel}")
    return errors


def data_schema(task_schema: dict) -> dict:
    props = task_schema["properties"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "instruction": props["instruction"],
            "domain": {"type": "string"},
            "platform": {"type": "string"},
            "eval_schema": props["eval_schema"],
            "time_limit": props["time_limit"],
            "extra_info": props["extra_info"],
            "metadata": props["metadata"],
        },
        "required": [
            "id",
            "instruction",
            "domain",
            "platform",
            "eval_schema",
            "time_limit",
            "extra_info",
            "metadata",
        ],
        "additionalProperties": False,
    }


def main() -> int:
    errors: list[str] = []
    task_schema = load_json(TASK_SCHEMA_PATH)
    task_validator = Draft202012Validator(task_schema)
    record_validator = Draft202012Validator(data_schema(task_schema))

    tasks: dict[str, dict] = {}
    task_paths = sorted(TASKS_DIR.glob("v2-*/task.json"))
    for path in task_paths:
        task_id = task_id_from_dir(path.parent)
        try:
            task = load_json(path)
        except Exception as exc:
            errors.append(f"{task_id}: invalid task JSON: {exc}")
            continue
        tasks[task_id] = task
        for err in sorted(task_validator.iter_errors(task), key=lambda e: list(e.path)):
            loc = ".".join(str(part) for part in err.path) or "<root>"
            errors.append(f"{task_id}: task schema {loc}: {err.message}")
        errors.extend(rel_path_errors(task_id, path.parent, task))

    records: dict[str, dict] = {}
    duplicate_ids: set[str] = set()
    try:
        lines = [line for line in DATA_PATH.read_text().splitlines() if line.strip()]
    except Exception as exc:
        errors.append(f"data file unreadable: {exc}")
        lines = []

    for line_no, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
        except Exception as exc:
            errors.append(f"data line {line_no}: invalid JSON: {exc}")
            continue
        record_id = record.get("id")
        if isinstance(record_id, str):
            if record_id in records:
                duplicate_ids.add(record_id)
            records[record_id] = record
        for err in sorted(
            record_validator.iter_errors(record), key=lambda e: list(e.path)
        ):
            loc = ".".join(str(part) for part in err.path) or "<root>"
            label = record_id if record_id is not None else f"line {line_no}"
            errors.append(f"{label}: data schema {loc}: {err.message}")

    for record_id in sorted(duplicate_ids):
        errors.append(f"{record_id}: duplicate data id")

    data_ids = set(records)
    task_ids = set(tasks)
    for record_id in sorted(data_ids - task_ids):
        errors.append(f"{record_id}: data record has no task directory")
    for task_id in sorted(task_ids - data_ids):
        errors.append(f"{task_id}: task directory has no data record")

    for task_id in sorted(data_ids & task_ids):
        task = tasks[task_id]
        record = records[task_id]
        for field in CORE_FIELDS:
            if record.get(field) != task.get(field):
                errors.append(f"{task_id}: data/task mismatch in {field}")

    if errors:
        print(f"FAIL errors={len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OK")
    print(f"records={len(records)}")
    print(f"tasks={len(tasks)}")
    print("task_schema=pass")
    print("data_schema=pass")
    print("data_task_consistency=pass")
    print("extra_info_files=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
