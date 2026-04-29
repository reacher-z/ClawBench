# ClawBench -- Agent Context

This file is for coding agents (Claude Code, Cursor, Copilot, etc.) to understand and operate on the ClawBench project. If you are a human, see the [README](README.md).

## What This Is

ClawBench is a benchmarking framework for evaluating AI web agents on 153 real-world online tasks spanning 144 live websites and 15 life categories. Each task runs in an isolated Docker container with Chromium, a recording Chrome extension, and an AI agent harness (`openclaw`, `opencode`, `claude-code`, `claude-code-chrome-extension`, `codex`, `browser-use`, `claw-code`, or `hermes`, selectable via `--harness`). The framework captures five layers of data: session replay (MP4), action screenshots, HTTP traffic, browser actions, and agent messages.

## Project Structure

```
ClawBench/
  run.sh                          # Entry point -- launches interactive TUI
  pyproject.toml                  # Root uv package metadata and CLI scripts
  .env.example                    # Template for PurelyMail credentials
  src/
    tui.py                        # Interactive TUI (called by run.sh)
    runner/
      run.py                      # Single test-case runner
      batch.py                    # Batch runner (model x case cross-product)
    utils/
      generate_resume_pdf.py      # Resume PDF generator
      hf_upload.py                # Optional HuggingFace upload helpers
    extension-server/
      pyproject.toml              # Container-only uv project for server deps
      uv.lock
      server.py                   # FastAPI data collection server
    chrome-extension/             # Recording extension (content.js, background.js)
    harnesses/
      base/
        Dockerfile.base           # Base image + shared entrypoint
        entrypoint.sh             # Shared infra; execs /run-harness.sh in agent mode
      openclaw/                   # Dockerfile + setup/run scripts
      opencode/
      claude-code/
      claude-code-chrome-extension/
      codex/
      browser-use/
      claw-code/
      hermes/
  models/
    models.yaml                   # Model API configs (gitignored -- copy from example)
    models.example.yaml           # Template with placeholder keys
    model.schema.json             # JSON schema for model entries
  test-cases/                     # 153 task directories
    task.schema.json              # JSON schema for task.json
    001-daily-life-food-uber-eats/
      task.json                   # Task instruction, eval schema, time limit
    ...
  shared/
    alex_green_personal_info.json # Synthetic user profile template
  eval/
    README.md                     # Evaluation guide + Claude Code prompt template
    agentic_eval.md               # Evaluator rubric for judging agent success
```

## Setup

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), Docker or Podman.

```bash
# 1. Configure PurelyMail credentials (disposable email for each run)
cp .env.example .env
# Edit .env: set PURELY_MAIL_API_KEY and PURELY_MAIL_DOMAIN

# 2. Configure at least one model
cp models/models.example.yaml models/models.yaml
# Edit models.yaml: add API key and base URL for your model(s)

# 3. Launch
./run.sh
```

## Common Commands

```bash
# Interactive TUI (recommended):
./run.sh

# Single run:
uv run --no-editable clawbench-run test-cases/<case-dir> <model-name> --harness openclaw

# Single run with Claude Code harness:
uv run --no-editable clawbench-run test-cases/<case-dir> <model-name> --harness claude-code

# Batch run (model x case cross-product):
uv run --no-editable clawbench-batch \
  --models <model-name> --all-cases --max-concurrent 3 --harness openclaw

# Human mode (manual browser control via noVNC; no harness needed):
uv run --no-editable clawbench-run test-cases/<case-dir> --human
```

## Model Configuration

Each model entry in `models/models.yaml` requires:
- `base_url` -- API endpoint (e.g. `https://openrouter.ai/api/v1`)
- `api_type` -- one of: `openai-completions`, `openai-responses`, `anthropic-messages`, `google-generative-ai`
- `api_key` -- API key (or `api_keys` for round-robin)

Optional: `thinking_level`, `temperature`, `max_tokens`. See `models/model.schema.json` for the full schema.

## Test Case Format

Each `test-cases/<id>-<metaclass>-<class>-<platform>/task.json` contains:
- `instruction` -- task prompt for the agent
- `eval_schema` -- request interceptor config (`url_pattern` regex + `method`)
- `time_limit` -- max minutes before watchdog stops the agent
- `extra_info` -- optional additional files to mount into the container

See `test-cases/task.schema.json` for the full schema.

## Output Structure

Each run produces:
```
test-output/<model>/<harness>-<case>-<model>-<timestamp>/
  run-meta.json             # Run metadata (harness, model, duration, intercepted)
  eval-schema.json          # Schema used for this run
  data/
    actions.jsonl           # Browser action log
    requests.jsonl          # HTTP request log
    agent-messages.jsonl    # Agent conversation transcript (shape varies by harness:
                            #   openclaw → session-schema events; opencode → AI-SDK
                            #   `step_start`/`tool_use`/`text`/`reasoning`/`step_finish` events;
                            #   claude-code → stream-json events with `system`/`assistant`/`user`/`result` types;
                            #   codex → full session rollout: timestamped `session_meta`/
                            #   `turn_context`/`event_msg`/`response_item` entries with reasoning,
                            #   function_call, and function_call_output items interleaved;
                            #   browser-use → one `AgentHistory` item per step with `model_output.action`,
                            #   `result`, `state`, `metadata` fields;
                            #   hermes → live `session_meta`/`thinking`/`reasoning`/
                            #   `tool_use`/`tool_result` capture, falling back to
                            #   Hermes session export when it contains messages)
    screenshots/            # Timestamped PNGs
    recording.mp4           # Full session video
    interception.json       # Interception result
```

## Key Documentation

- [README.md#-cli](README.md#-cli) -- CLI usage, batch runner flags, output format
- [src/extension-server/README.md](src/extension-server/README.md) -- FastAPI server, endpoints, screen recording
- [CONTRIBUTING.md](CONTRIBUTING.md) -- how to add new test cases
- [eval/README.md](eval/README.md) -- evaluation guide and Claude Code prompt template
- [eval/agentic_eval.md](eval/agentic_eval.md) -- evaluator rubric for PASS/FAIL judgment
