# ClawBench -- Agent Context

This file is for coding agents (Claude Code, Cursor, Copilot, etc.) to understand and operate on the ClawBench project. If you are a human, see the [README](README.md).

## What This Is

ClawBench is a benchmarking framework for evaluating AI web agents on 153 real-world online tasks spanning 144 live websites and 15 life categories. Each task runs in an isolated Docker container with Chromium, a recording Chrome extension, and an AI agent harness (`openclaw` or `opencode`, selectable via `--harness`). The framework captures five layers of data: session replay (MP4), action screenshots, HTTP traffic, browser actions, and agent messages.

## Project Structure

```
ClawBench/
  run.sh                          # Entry point -- launches interactive TUI
  Dockerfile.base                 # Base image (Chromium + extension + Node + uv, harness-agnostic)
  Dockerfile.openclaw             # Layer that adds the openclaw CLI on top of base
  Dockerfile.opencode             # Layer that adds opencode + @playwright/mcp on top of base
  entrypoint.sh                   # Shared infra (Xvfb, Chrome, noVNC, human mode); execs /run-harness.sh in agent mode
  setup-openclaw.sh               # Generates ~/.openclaw/openclaw.json from env vars (called from run-openclaw.sh)
  setup-opencode.sh               # Generates ~/.config/opencode/opencode.json from env vars (called from run-opencode.sh)
  run-openclaw.sh                 # Per-harness agent runner; copied into clawbench-openclaw image as /run-harness.sh
  run-opencode.sh                 # Per-harness agent runner; copied into clawbench-opencode image as /run-harness.sh
  .env.example                    # Template for PurelyMail credentials
  models/
    models.yaml                   # Model API configs (gitignored -- copy from example)
    models.example.yaml           # Template with placeholder keys
    model.schema.json             # JSON schema for model entries
  test-cases/                     # 153 task directories
    task.schema.json              # JSON schema for task.json
    001-daily-life-food-uber-eats/
      task.json                   # Task instruction, eval schema, time limit
    ...
  test-driver/
    tui.py                        # Interactive TUI (called by run.sh)
    run.py                        # Single test-case runner
    batch.py                      # Batch runner (model x case cross-product)
    generate_resume_pdf.py        # Resume PDF generator
    README.md                     # Full test driver documentation
  extension-server/
    server.py                     # FastAPI data collection server
    README.md                     # Server documentation
  chrome-extension/               # Recording extension (content.js, background.js)
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
uv run --project test-driver test-driver/run.py test-cases/<case-dir> <model-name> --harness openclaw

# Batch run (model x case cross-product):
uv run --project test-driver test-driver/batch.py \
  --models <model-name> --all-cases --max-concurrent 3 --harness openclaw

# Human mode (manual browser control via noVNC; no harness needed):
uv run --project test-driver test-driver/run.py test-cases/<case-dir> --human
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
                            #   `step_start`/`tool_use`/`text`/`reasoning`/`step_finish` events)
    screenshots/            # Timestamped PNGs
    recording.mp4           # Full session video
    interception.json       # Interception result
```

## Key Documentation

- [test-driver/README.md](test-driver/README.md) -- test driver, batch runner, output format, personal info
- [extension-server/README.md](extension-server/README.md) -- FastAPI server, endpoints, screen recording
- [CONTRIBUTING.md](CONTRIBUTING.md) -- how to add new test cases
- [eval/README.md](eval/README.md) -- evaluation guide and Claude Code prompt template
- [eval/agentic_eval.md](eval/agentic_eval.md) -- evaluator rubric for PASS/FAIL judgment
