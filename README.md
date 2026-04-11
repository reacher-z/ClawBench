# ClawBench

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

ClawBench is a benchmarking framework for evaluating web agents in real browser environments. It records user/agent interactions, HTTP requests, action screenshots, and full MP4 video recordings of each session.

Each test case runs in an isolated container (Docker or Podman) with a Chrome browser, a custom recording extension, and an AI agent. The framework captures everything the agent does and uses a request interceptor to detect task completion.

Two agent harnesses are supported: **openclaw** (default) and **opencode**. Both drive the same in-container Chromium — openclaw through its built-in browser tool, opencode through the `chrome-devtools-mcp` MCP server. The harness is selected per run via `--harness`; the same model entry in `models.yaml` can be benchmarked under either.

## Table of Contents

- [Dependencies](#dependencies)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Data Output](#data-output)
- [Building the Container](#building-the-container)
- [API Endpoints](#api-endpoints)
- [Agent Harnesses](#agent-harnesses)
  - [openclaw harness](#openclaw-harness)
  - [opencode harness](#opencode-harness)
- [Synthetic User Profile](#synthetic-user-profile)
- [Tool Restrictions](#tool-restrictions)
- [Request Interceptor](#request-interceptor)
- [Test Driver](#test-driver)
- [Human Mode](#human-mode)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Dependencies

- [Python](https://www.python.org/) 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager — installs all Python deps automatically)
- [Docker](https://www.docker.com/) or [Podman](https://podman.io/) (container runtime)

Python dependencies (`fpdf2`, `huggingface_hub`, `pyyaml`) are managed by `uv` and installed automatically on first run.

## Quick Start

```bash
# 1. Set up PurelyMail credentials:
cp .env.example .env
# Edit .env and fill in PURELY_MAIL_API_KEY and PURELY_MAIL_DOMAIN

# 2. Launch the interactive menu:
./run.sh
```

The menu will guide you through configuring models, selecting test cases, and running benchmarks.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Container (Docker / Podman)                    │
│                                                 │
│  ┌───────────┐   DOM events  ┌──────────────┐   │
│  │ content.js├──────────────►│ background.js│   │
│  │ (per tab) │               │  (service    │   │
│  └───────────┘               │   worker)    │   │
│                              └──┬──────┬────┘   │
│                                 │      │        │
│                         actions │      │ screenshots
│                                 │      │        │
│  ┌──────────┐            ┌──────▼──────▼────┐   │
│  │  Xvfb    │◄──ffmpeg──►│  FastAPI Server  │   │
│  │ :99      │  x11grab   │  :7878           │   │
│  └──────────┘            └──────────────────┘   │
│                                  │              │
│  ┌──────────┐            ┌───────▼─────────┐    │
│  │ Chromium │            │     /data       │    │
│  │ :9222 CDP│            │  actions.jsonl  │    │
│  └──────────┘            │  requests.jsonl │    │
│                          │  screenshots/   │    │
│                          │  recording.mp4  │    │
│                          └─────────────────┘    │
└─────────────────────────────────────────────────┘
```

## Data Output

All data is stored under `/data` in the container:

```
/data/
  actions.jsonl          # One JSON object per line, every DOM event
  requests.jsonl         # One JSON object per line, every HTTP request
  agent-messages.jsonl   # Agent conversation transcript — schema differs per harness; run-meta.json carries the `harness` field
  screenshots/           # Timestamped PNGs, one per action
    1710000001234.png
    1710000002345.png
  recording.mp4          # Full session video (H.264, 15fps)
  interception.json      # Details of any blocked requests by the interceptor (if applicable)
```

### Action Format (JSONL)

Each line is a JSON object:

```json
{"type": "click", "timestamp": 1710000001234, "url": "https://example.com/", "target": {"tagName": "A", "id": "", "className": "btn", "textContent": "Submit", "xpath": "/html[1]/body[1]/div[1]/a[1]"}, "x": 255, "y": 245}
{"type": "keydown", "timestamp": 1710000002345, "url": "https://example.com/", "target": {...}, "key": "Enter"}
{"type": "input", "timestamp": 1710000003456, "url": "https://example.com/", "target": {...}, "value": "search query"}
{"type": "pageLoad", "timestamp": 1710000004567, "url": "https://example.com/results", "title": "Results"}
```

Captured event types: `pageLoad`, `click`, `keydown`, `keyup`, `input`, `scroll`, `change`, `submit`.

### Agent Messages Format (JSONL)

`agent-messages.jsonl` contains the full agent conversation transcript. **Both harnesses produce the same JSONL schema** (openclaw's native format). For opencode, the translation happens in the entrypoint post-run cleanup by exporting the on-disk session and reshaping it — see [opencode harness](#opencode-harness) below.

**Event header** (first 4 lines of every transcript):

1. `{"type": "session", "version": 3, "id": "clawbench", "timestamp": "<ISO>", "cwd": "/root/workspace"}`
2. `{"type": "model_change", "id": "<hex>", "parentId": null, "timestamp": "<ISO>", "provider": "api", "modelId": "<MODEL_NAME>"}`
3. `{"type": "thinking_level_change", "id": "<hex>", "parentId": "<prev>", "timestamp": "<ISO>", "thinkingLevel": "medium"}`
4. `{"type": "custom", "customType": "model-snapshot", "data": {...}, "id": "<hex>", "parentId": "<prev>", "timestamp": "<ISO>"}`

**Message events** follow the header. Each has `id`, `parentId` (chained DAG), `timestamp`, and a nested `message` object with `role` and `content[]`:

| `message.role` | Content item `type`       | Notes                                                                                 |
| -------------- | ------------------------- | ------------------------------------------------------------------------------------- |
| `user`         | `text`                    | The initial instruction prompt                                                        |
| `assistant`    | `thinking`                | Has `thinking` field (not `text`) plus `thinkingSignature`                            |
| `assistant`    | `text`                    | Model-authored user-facing text                                                       |
| `assistant`    | `toolCall`                | Keys: `type`, `id`, `name`, `arguments`                                               |
| `toolResult`   | `text`                    | Tool output as plain text. Outer message carries `toolCallId`, `toolName`, `isError` |

Each `toolCall` in an assistant message is followed by exactly one `toolResult` message referencing the same `toolCallId`.

### HTTP Requests Format (JSONL)

`requests.jsonl` logs every HTTP request made by the browser during the session (excluding internal extension/server traffic). Each line:

```json
{"timestamp": 1710000001.234, "url": "https://example.com/api?q=test", "method": "POST", "headers": {"Content-Type": "application/json"}, "body": {"action": "send"}, "query_params": {"q": "test"}, "resource_type": "XHR"}
```

| Field           | Description                                                        |
| --------------- | ------------------------------------------------------------------ |
| `timestamp`     | Unix epoch (float)                                                 |
| `url`           | Full request URL                                                   |
| `method`        | HTTP method (GET, POST, etc.)                                      |
| `headers`       | Request headers (object)                                           |
| `body`          | Parsed request body (JSON object, form dict, raw string, or null)  |
| `query_params`  | Parsed URL query parameters (object)                               |
| `resource_type` | Resource type: Document, Script, Stylesheet, XHR, Fetch, Image, Font, etc. |

Requests to `localhost:7878` (extension server) and `chrome-extension://` URLs are filtered out.

## Building the Container

### Container engine

The framework supports both Docker and Podman (which works without root privileges). Set the `CONTAINER_ENGINE` environment variable to force one:

```bash
export CONTAINER_ENGINE=podman  # or docker
```

If unset, it auto-detects the one available on the system.

### Build

Three Dockerfiles: a shared base, then one layered image per harness. The test driver builds them for you; the manual commands are:

```bash
# Shared base: Chromium, Xvfb, ffmpeg, noVNC, uv, extension-server, chrome-extension,
# plus entrypoint.sh (inherited by both harness images).
docker build -t clawbench-base     -f Dockerfile.base     .

# openclaw harness image — FROM clawbench-base, adds openclaw + setup-openclaw.sh
docker build -t clawbench-openclaw -f Dockerfile.openclaw .

# opencode harness image — FROM clawbench-base, adds opencode + chrome-devtools-mcp + setup-opencode.sh
docker build -t clawbench-opencode -f Dockerfile.opencode .
```

Same commands with `podman build` — the framework supports either engine.

`clawbench-base` is a legitimate runnable image on its own:
- **Human mode** (`HUMAN_MODE=1`) — noVNC on `:6080`, no agent binary needed.
- **Manual mode** (leave `INSTRUCTION` unset) — Xvfb + Chrome + FastAPI server stay up; attach with `docker exec` for ad-hoc inspection.
- Agent mode on `clawbench-base` is rejected with a `harness_not_installed` error — use `clawbench-openclaw` or `clawbench-opencode` instead.

If you only care about human mode you only need `clawbench-base`. Each harness image is an additive layer on top of it.

### Ports

| Port | Service         | Purpose                                    |
| ---- | --------------- | ------------------------------------------ |
| 7878 | FastAPI server  | Action/screenshot API, session control     |
| 9223 | CDP (via socat) | Playwright/DevTools connection to Chromium |

## API Endpoints

| Method | Path              | Description                                  |
| ------ | ----------------- | -------------------------------------------- |
| GET    | `/api/status`     | Health check                                 |
| POST   | `/api/action`     | Record a browser action (JSON body)          |
| POST   | `/api/screenshot` | Store a screenshot (base64 PNG in JSON)      |
| POST   | `/api/stop`       | Signal session stop, finalize bookkeeping    |
| POST   | `/api/stop-recording` | Stop ffmpeg recording, finalize MP4      |


## Agent Harnesses

ClawBench supports two interchangeable agent harnesses. Selection is per-run, via `--harness openclaw` (default) or `--harness opencode` on `test-driver/run.py` and `test-driver/batch.py`. The harness is **model-agnostic** — a single entry in `models.yaml` can be benchmarked under either harness with no config changes.

Each harness ships as its own container image, layered on the shared `clawbench-base`:

```
clawbench-base  (Chromium, Xvfb, ffmpeg, noVNC, extension-server, chrome-extension, entrypoint.sh)
    ├── clawbench-openclaw  (adds openclaw + setup-openclaw.sh + ENV HARNESS=openclaw)
    └── clawbench-opencode  (adds opencode-ai + chrome-devtools-mcp + setup-opencode.sh + ENV HARNESS=opencode)
```

`entrypoint.sh` is owned by the base image; both harness images inherit it through `FROM clawbench-base`. The harness is baked into each child image via `ENV HARNESS=…`; the entrypoint reads `$HARNESS` and branches on it, falling through a `command -v <harness>` guard that rejects agent runs on `clawbench-base` (which has no agent binary) with a `harness_not_installed` stop reason.

### Shared Environment Variables

Both harnesses read the same set of environment variables passed by the test driver:

| Variable                          | Example                                                | Description                                          |
| --------------------------------- | ------------------------------------------------------ | ---------------------------------------------------- |
| `MODEL_NAME`                      | `claude-sonnet-4-6`, `gemini-3-flash-preview`          | Model identifier                                     |
| `BASE_URL`                        | `https://api.openai.com/v1`                            | API base URL                                         |
| `API_TYPE`                        | `openai-completions`                                   | `openai-completions`, `openai-responses`, `anthropic-messages`, `google-generative-ai` |
| `API_KEY`                         | `sk-ant-...`, `AIza...`                                | API key (single)                                     |
| `API_KEYS`                        | `["k1","k2"]`                                          | JSON array for round-robin rotation (openclaw only; opencode uses the first entry) |
| `INSTRUCTION`                     | `"Go to example.com and…"`                             | Task prompt for the agent                            |
| `TIME_LIMIT_S`                    | `300`                                                  | Watchdog timeout in seconds                          |
| `THINKING_LEVEL`                  | `off`/`low`/`medium`/`high`/…                          | Reasoning depth. openclaw: passed as `--thinking`. opencode: sets model `reasoning` flag and maps to `providerOptions.openai.reasoningEffort` for openai-compatible providers. |
| `TEMPERATURE`                     | `0.5`                                                  | Sampling temperature (both harnesses)                  |
| `MAX_TOKENS`                      | `4096`                                                 | Max output tokens (openclaw: `--max-tokens`; opencode: `model.options.maxOutputTokens`) |

### Container Lifecycle

The entrypoint (`entrypoint.sh`) orchestrates the following harness-agnostic sequence:

1. **Xvfb** — virtual display at `:99` (1920x1080)
2. **FastAPI server** — data collection API on port 7878, starts ffmpeg screen recording
3. **Chromium** — with Chrome extension loaded, CDP on port 9222
4. **socat** — forwards port 9223 (external) to 9222 (internal CDP)
5. **`/my-info` copy** into the workspace (`/root/workspace/my-info`)
6. **CDP health check** — polls `http://127.0.0.1:9222/json/version` until Chrome is ready
7. **Harness branch** — setup + agent start (see per-harness sections below)
8. **Watchdog** — monitors `/data/actions.jsonl`; stops when the eval interceptor matches (via `/data/.stop-requested`), after 300s of no new actions, or when `TIME_LIMIT_S` is reached
9. **Cleanup** — kills harness processes, calls `POST /api/stop` for bookkeeping, 15s grace period for recording to capture end result, `POST /api/stop-recording` to finalize MP4, exits

### openclaw harness

Uses [OpenClaw](https://github.com/openclaw/openclaw) as the agent driver. OpenClaw has a built-in browser tool (which internally spawns `chrome-devtools-mcp`) and manages its own gateway + agent lifecycle.

**Steps 7–8 (openclaw):**

1. Generate a shared gateway token (`OPENCLAW_GATEWAY_TOKEN`)
2. `setup-openclaw.sh` writes `~/.openclaw/openclaw.json` + `~/.openclaw/agents/main/agent/auth-profiles.json` from env vars
3. `openclaw gateway run` — local mode
4. `openclaw agent --session-id clawbench --message "$INSTRUCTION" --thinking "${THINKING_LEVEL:-medium}" --timeout "$TIMEOUT_MS" --local`
5. On cleanup, the session transcript is copied from `~/.openclaw/agents/main/sessions/clawbench.jsonl` to `/data/agent-messages.jsonl`.

**OpenClaw browser patch.** OpenClaw's `existing-session` driver hardcodes `--autoConnect` when launching chrome-devtools-mcp, which only discovers Chrome via the `DevToolsActivePort` file in the default user data directory. It ignores the `cdpUrl` set in the browser profile config. See [openclaw/openclaw#47879](https://github.com/openclaw/openclaw/issues/47879). Workaround applied in `Dockerfile.openclaw`:

- OpenClaw is pinned to `v2026.3.13`
- A `sed` patch replaces `"--autoConnect"` with `"--browserUrl","http://127.0.0.1:9222"` across all bundled dist files
- Chromium is launched with `--remote-allow-origins=*` (required for chrome-devtools-mcp's internal WebSocket connections on Chrome 132+)

Once [#47879](https://github.com/openclaw/openclaw/issues/47879) is resolved upstream, the version pin and patch can be removed.

### opencode harness

Uses [opencode](https://opencode.ai) (`opencode-ai`) — a general-purpose CLI agent with no native browser tool. Browser control comes from the [`chrome-devtools-mcp`](https://www.npmjs.com/package/chrome-devtools-mcp) package, wired in as a local stdio MCP server in the generated opencode config and pointed at the in-container Chrome CDP (`127.0.0.1:9222`). Because we invoke `chrome-devtools-mcp` directly with `--browserUrl`, the opencode harness does not need the openclaw upstream patch.

**Pinned versions** (`Dockerfile.opencode`): `opencode-ai@1.4.3`, `chrome-devtools-mcp@0.21.0`.

**Steps 7–8 (opencode):**

1. `setup-opencode.sh` writes `~/.config/opencode/opencode.json` with:
   - A custom provider `clawbench` using the right `@ai-sdk/*` adapter for the given `API_TYPE` (see mapping table below), with `options.baseURL` and `options.apiKey` drawn from the env vars.
   - A model entry with `reasoning: true` (unless `THINKING_LEVEL=off`) and `options` carrying `temperature`, `maxOutputTokens`, and `providerOptions.openai.reasoningEffort` (for openai-compatible providers, mapped from `THINKING_LEVEL`).
   - An `mcp.chrome-devtools` entry invoking `chrome-devtools-mcp --browserUrl http://127.0.0.1:9222`.
   - A `permission` policy (see below) mirroring openclaw's `exec` allowlist.
2. `opencode run --format json --model "clawbench/$MODEL_NAME" -- "$INSTRUCTION"` is launched in the background. Its live event stream goes to `/data/opencode-stream.jsonl` purely so we can extract the sessionID from the first event.
3. **On cleanup**, after the agent is killed, `opencode export "$SESSION_ID"` is run to retrieve the **full** transcript — including `reasoning` content parts, which the live `--format json` stream omits. That hierarchical JSON is then **translated into the openclaw JSONL schema** (see [Agent Messages Format](#agent-messages-format-jsonl)) so downstream parsers see a single unified shape regardless of harness. The mapping:
   - session header (session → model_change → thinking_level_change → custom(model-snapshot)) is synthesized from the opencode session info and env vars (`MODEL_NAME`, `API_TYPE`, `THINKING_LEVEL`). Event IDs are fresh 8-char hex and chained via `parentId`.
   - user messages → `{role: user, content: [{type: text, ...}]}`
   - assistant parts → `reasoning` becomes `{type: thinking, thinking, thinkingSignature: "reasoning"}`, `text` stays `{type: text}`, each `tool` becomes `{type: toolCall, id: callID, name: tool, arguments: state.input}`. `step-start` / `step-finish` are dropped (no openclaw analog).
   - each assistant `toolCall` is followed by a synthetic `toolResult` message with `toolCallId`, `toolName`, `isError`, and `content: [{type: text, text: state.output}]`.

   The intermediate `opencode-stream.jsonl` and `opencode-export.json` are deleted after the translation completes.

**API type → npm adapter mapping** (`setup-opencode.sh`):

| ClawBench `api_type`   | opencode `npm`              |
| ---------------------- | --------------------------- |
| `openai-completions`   | `@ai-sdk/openai-compatible` |
| `openai-responses`     | `@ai-sdk/openai`            |
| `anthropic-messages`   | `@ai-sdk/anthropic`         |
| `google-generative-ai` | `@ai-sdk/google`            |

All four adapters are bundled in the `opencode-ai` binary — no additional npm installs.

**Permission policy.** The generated `opencode.json` contains:

```json
"permission": {
  "bash": {
    "*": "deny",
    "ls *": "allow", "cat *": "allow", "find *": "allow", "file *": "allow",
    "jq *": "allow", "cut *": "allow", "uniq *": "allow", "head *": "allow",
    "tail *": "allow", "tr *": "allow", "wc *": "allow", "grep *": "allow",
    "sort *": "allow"
  },
  "edit":     "deny",
  "write":    "deny",
  "webfetch": "deny"
}
```

This mirrors the openclaw harness's `exec` allowlist: bash restricted to 13 safe read-only commands, edits/writes/network fetches denied. Chrome-devtools-mcp tools remain allowed (default), so the browser can still be driven. opencode honors these rules during non-interactive `opencode run` execution and returns an `error` state on denied tool calls.

**Limitations (opencode harness):**

- **Single API key only.** opencode's provider config takes one `apiKey`; if `API_KEYS` is set, `setup-opencode.sh` picks the first entry. Round-robin rotation is openclaw-only.
- **`THINKING_LEVEL` effort mapping is best-effort.** The ClawBench schema values `{off, minimal, low, medium, high, xhigh, adaptive}` are collapsed to opencode's openai-style `reasoningEffort` values `{low, medium, high}` (`off` disables the `reasoning` flag entirely; `minimal`→`low`, `xhigh`→`high`, `adaptive`→`medium`). For `@ai-sdk/anthropic` / `@ai-sdk/google`, `reasoningEffort` is not passed — those providers use their own defaults.
- **Translation from opencode export to openclaw schema is lossy.** opencode's `step-start` / `step-finish` bookkeeping parts and per-message `tokens` / `cost` metadata are dropped during translation. If you need them, parse the raw `opencode export` output directly instead of `agent-messages.jsonl`.

## Synthetic User Profile

Each container has a `/my-info/` directory (read-only) containing a dummy user's identity and credentials:

```
/my-info/
  alex_green_personal_info.json   # Full profile (contact, address, education, work, etc.)
  email_credentials.json          # Auto-generated email + password + login URL
  alex_green_resume.pdf           # Resume PDF with dynamic email in header
```

The `email` field in both the personal info JSON and the resume PDF is updated each run to match the disposable email created for that session. The agent is instructed to read these files when it needs personal details for form filling, registration, etc.

Source templates live in `shared/` (personal info) and `test-driver/resume_template.json` (resume). The PDF is generated at runtime by `test-driver/generate_resume_pdf.py`.

## Tool Restrictions

Both harnesses apply the same effective tool policy: the agent can drive the browser and read files under `./my-info/` in its workspace, but cannot run arbitrary code or make network requests outside the browser.

- **Filesystem reads** are allowed. Each harness has its own built-in `read` tool (opencode calls it `read`; openclaw has an analogous file-read tool) and these are always permitted, so the agent can freely inspect `./my-info/email_credentials.json`, `./my-info/alex_green_personal_info.json`, and `./my-info/alex_green_resume.pdf`.
- **Shell execution** is restricted to a small safe allowlist: `ls`, `cat`, `find`, `file`, `jq`, `cut`, `uniq`, `head`, `tail`, `tr`, `wc`, `grep`, `sort`. Anything else — `curl`, `wget`, `python3`, `node`, etc. — is denied.
- **File writes / edits** are denied entirely.
- **Generic network fetches** (opencode's `webfetch` tool, openclaw's `web_search` tool, etc.) are denied.
- **Browser tools** (openclaw's built-in browser tool, opencode's `chrome-devtools-mcp` MCP server) are allowed — that's the only legitimate way for the agent to do things on the web.

Implementation per harness:

- **openclaw**: `tools.exec.security = "allowlist"` with `safeBins` set in the generated OpenClaw config. See [setup-openclaw.sh](setup-openclaw.sh).
- **opencode**: `permission.bash = {"*": "deny", "ls *": "allow", ...}` plus `edit: "deny"`, `write: "deny"`, `webfetch: "deny"` in the generated opencode config. Chrome-devtools-mcp tools stay at default (allow). See [setup-opencode.sh](setup-opencode.sh) and [opencode harness](#opencode-harness) above.

The agent instruction prompt also explicitly requires browser-only task completion.

## Request Interceptor

The interceptor blocks critical, irreversible HTTP requests (checkout, form submission, review posting, etc.) to prevent the agent from causing real-world side effects during evaluation. It does **not** validate task completion — evaluation is handled separately by evaluators post-session.

### How It Works

1. Mount a JSON config at `/eval-schema.json` in the container
2. The server connects to Chrome via CDP (`Fetch` domain) and intercepts all requests
3. When a request matches the `url_pattern` (regex), `method`, and optional `body`/`params` filters, the request is blocked
4. The blocked request's details are saved to `interception.json`, the agent is killed, and the recording stops

### Schema Format

The eval schema has two required fields (`url_pattern`, `method`) and two optional fields (`body`, `params`) for disambiguation.

```json
{
  "url_pattern": "inbox\\.purelymail\\.com",
  "method": "POST",
  "body": { "_action": "send" }
}
```

The optional `body` and `params` are flat key-value maps — each key must match exactly in the request data. Use them when the same URL + method serves multiple actions (e.g., login vs send on the same endpoint, or different GraphQL operations).

For tasks behind payment walls or other natural blockers (agent has no valid credit card), use the placeholder pattern that never matches:

```json
{
  "url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__",
  "method": "POST"
}
```

### When to Block

The interceptor is only needed for actions that would have **irreversible real-world consequences** without a payment wall:

| Block   | Examples                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Yes** | Public reviews, listings, job applications, contact forms, email sends, appointment bookings, website creation                    |
| **No**  | Purchases, subscriptions, donations (payment wall), cart additions (reversible), searches (reversible), account creation (benign) |


### Interception Output

`/data/interception.json`:

```json
{
  "intercepted": true,
  "request": {
    "url": "https://inbox.purelymail.com/action",
    "method": "POST",
    "params": {},
    "body": {"_action": "send", "_to": "user@example.com"}
  }
}
```

## Test Driver

The test driver (`test-driver/run.py`) automates running test cases end-to-end: creates a disposable email via PurelyMail, launches a container, enforces a time limit, collects results, and cleans up. Test cases are defined in `test-cases/` with a `task.json` validated by `test-cases/task.schema.json`.

```bash
# Interactive menu (configure models, select cases, pick harness, choose run mode):
./run.sh

# Or run directly — openclaw (default):
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf qwen3.5-397b-a17b

# Same model, opencode harness:
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf qwen3.5-397b-a17b --harness opencode

# Human mode (no agent — you control the browser via noVNC):
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf --human

# Batch: all models x cases 1-50, 3 concurrent, harness=opencode
uv run test-driver/batch.py --harness opencode --all-models --case-range 1-50 --max-concurrent 3

```

Output paths are segmented by a `<harness>-<model>` prefix so the same model under different harnesses never collides. For example:

```
test-output/
  openclaw-qwen3.5-397b-a17b/886-...-openclaw-qwen3.5-397b-a17b-20260410-230224/
  opencode-qwen3.5-397b-a17b/886-...-opencode-qwen3.5-397b-a17b-20260410-231144/
```

Each run's `run-meta.json` carries a `harness` field identifying which driver produced the data.

See [test-driver/README.md](test-driver/README.md) for full documentation.

## Human Mode

Human mode lets you perform test cases manually in the browser instead of using an AI agent. This is useful for collecting human baselines, debugging test cases, or verifying that a task is completable.

The container runs the same infrastructure (Xvfb, Chromium, extension, FastAPI server, ffmpeg recording) but instead of launching an agent, it exposes the browser via [noVNC](https://novnc.com/) — a browser-based VNC client. Human mode uses the `clawbench-base` image directly — no agent binary is installed, and no harness build is required.

### Usage

```bash
# Via interactive menu (select "Human mode"):
./run.sh

# Or directly:
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf --human
```

After the container starts, open the noVNC URL printed in the terminal:

```
noVNC ready: http://localhost:6080/vnc.html
```

You'll see the Chromium browser in your web browser. Complete the task manually — all your actions, screenshots, and HTTP requests are recorded just like in agent mode.

### How it ends

The session stops when any of these happen:

- **Eval interceptor matches** — the target HTTP request was detected (task completed)
- **VNC disconnect** — you close the noVNC tab (15s grace period for reconnection)
- **Time limit** — the configured time limit expires

After the session ends, results are collected in the same format as agent runs (actions, screenshots, recording, interception).

## License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

ClawBench uses the following open-source projects:

- [noVNC](https://github.com/novnc/noVNC) (MPL 2.0) — browser-based VNC client for human mode
- [websockify](https://github.com/novnc/websockify) (LGPL 3.0) — WebSocket-to-TCP proxy for VNC
- [OpenClaw](https://github.com/openclaw/openclaw) — AI agent driver for browser automation (openclaw harness)
- [opencode](https://opencode.ai) — general-purpose CLI agent (opencode harness)
- [chrome-devtools-mcp](https://www.npmjs.com/package/chrome-devtools-mcp) — MCP server exposing Chrome DevTools Protocol (used by both harnesses)