# Test Cases

This directory contains the 153 ClawBench test cases plus the JSON schema they are validated against.

## Contents

- `task.schema.json` — the authoritative schema for `task.json` files. See [`../docs/request_interceptor.md`](../docs/request_interceptor.md) for `eval_schema` usage.
- `NNN-<metaclass>-<class>-<platform>/` — one directory per test case, named by its numeric ID prefix.

## Categorical overview

For the full category breakdown (counts per metaclass, examples, how to browse by ID range), see **[`../docs/test_cases.md`](../docs/test_cases.md)**.

## Naming convention

```
{task_id:03d}-{metaclass}-{class}-{platform}
```

Example: `001-daily-life-food-uber-eats`

- **task_id** — three-digit zero-padded integer, globally unique. Gaps are allowed.
- **metaclass** — high-level category.
- **class** — granular sub-category.
- **platform** — the primary site the task exercises.

## Structure of a test case

```
001-daily-life-food-uber-eats/
  task.json                     # Required. Validated against ../task.schema.json.
  extra_info/                   # Optional. Files mounted into /my-info/ at runtime.
    preferences.json
```

`task.json` at minimum:

```json
{
  "$schema": "../task.schema.json",
  "instruction": "Task prompt for the agent",
  "eval_schema": {
    "url_pattern": "example\\.com/api/submit",
    "method": "POST"
  },
  "time_limit": 5
}
```

The `metadata` block and `extra_info` array are optional but strongly recommended. See [`task.schema.json`](task.schema.json) for the full field reference.

## Browsing

```bash
# By category
ls | grep -E '^[0-9]+-daily-life-'
ls | grep -E '^[0-9]+-travel-'

# By platform
ls | grep airbnb
ls | grep github

# By ID range (via the batch runner)
uv run --project test-driver test-driver/batch.py \
    --all-models --case-range 1-50 --max-concurrent 3
```

## Adding a new test case

See **[`../CONTRIBUTING.md#adding-a-new-test-case`](../CONTRIBUTING.md#adding-a-new-test-case)** for the full step-by-step guide, including how to find the right `eval_schema.url_pattern` via human mode.
