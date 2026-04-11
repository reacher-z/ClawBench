# Architecture

ClawBench runs every benchmark session inside a container that bundles the browser, the recording infrastructure, and the agent. This document explains what starts, in what order, and how the pieces talk.

## High-level diagram

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

## Components

| Component         | Role                                                                                    | Source                                          |
| ----------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Xvfb**          | Virtual X11 display `:99` (1920×1080) — provides a framebuffer for headless operation.  | started in `entrypoint.sh`                      |
| **Chromium**      | Real browser, launched with the ClawBench extension and CDP enabled on port 9222.      | `entrypoint.sh` (flags), [`chrome-extension/`](../chrome-extension/) |
| **Chrome extension** | Listens for DOM events in every tab and posts actions + throttled screenshots to the extension server. | [`chrome-extension/README.md`](../chrome-extension/README.md) |
| **Extension server** | FastAPI app on port 7878 that records actions/screenshots, tails the CDP Fetch stream for request logging and interception, and runs ffmpeg to record the Xvfb display to MP4. | [`extension-server/README.md`](../extension-server/README.md) |
| **socat**         | Forwards external port 9223 to internal port 9222 so tools outside the container can attach to CDP without exposing it to page JavaScript. | `entrypoint.sh` |
| **OpenClaw gateway** | Local-mode process that manages agent execution and tool calls.                      | [OpenClaw](https://github.com/openclaw/openclaw), launched by `entrypoint.sh` |
| **OpenClaw agent** | The LLM-driven agent itself. Connects to the gateway, reads the instruction, and drives Chrome via the browser tool. | [`openclaw_integration.md`](openclaw_integration.md) |
| **Watchdog**      | A shell loop in `entrypoint.sh` that tails `actions.jsonl`, watches for eval-interceptor matches, and enforces the time limit. | `entrypoint.sh` |

## Container lifecycle (agent mode)

The entrypoint orchestrates components in this order:

1. **Mount `/data`** — output directory for all artifacts.
2. **Start Xvfb** on display `:99`.
3. **Start the extension server** on port 7878. It kicks off the ffmpeg recording of `:99` to `/data/recording.mp4` (H.264, 15 fps) and opens a CDP websocket to Chromium for request interception.
4. **Start Chromium** with the extension loaded, stealth flags applied, and `--remote-debugging-port=9222`. See [`chrome-extension/README.md`](../chrome-extension/README.md#layer-1-chrome-launch-flags-entrypointsh) for the flag rationale.
5. **Start `socat`** to forward 9223 → 9222.
6. **Run `setup-openclaw.sh`** — generates `~/.openclaw/openclaw.json` and `~/.openclaw/agents/main/agent/auth-profiles.json` from the `MODEL_NAME`, `BASE_URL`, `API_TYPE`, and `API_KEY(S)` environment variables.
7. **CDP health check** — polls `http://127.0.0.1:9222/json/version` for up to 30 seconds until Chrome is ready.
8. **Copy `/my-info/` into the agent workspace** — synthetic user profile, disposable email credentials, resume PDF.
9. **Start the OpenClaw gateway** in local mode.
10. **Start the OpenClaw agent** with the session ID and the assembled instruction.
11. **Watchdog loop** — monitors `/data/actions.jsonl` for idle, checks `/data/.stop-requested` for interceptor matches, and enforces `TIME_LIMIT_S`.
12. **Cleanup** — kill OpenClaw processes, `POST /api/stop` for bookkeeping, sleep 15s to let the recording capture the final frame, `POST /api/stop-recording` to finalize the MP4, exit.

The host-side test driver (`test-driver/run.py`) then copies `/data` out of the container, writes `run-meta.json`, deletes the disposable email, and removes the container.

## Human mode

Human mode replaces steps 6–11 with a VNC path. Instead of launching OpenClaw, the entrypoint starts `x11vnc` and `websockify`, exposing the framebuffer on `localhost:6080` through noVNC. See [`human_mode.md`](human_mode.md).

## Watchdog stop reasons

The watchdog writes a stop reason to `/data/.stop-reason` when it ends the session. This value ends up in `interception.json` when the interceptor did not fire.

| `stop_reason`           | Meaning                                                                                      |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| `eval_matched`          | The interceptor matched the configured `url_pattern` and stopped the session (the common success path). |
| `agent_idle`            | 300 seconds elapsed with no new entries in `actions.jsonl`. The agent is stuck.              |
| `agent_exited`          | The OpenClaw agent process exited before the interceptor fired.                              |
| `time_limit_exceeded`   | `TIME_LIMIT_S` was reached.                                                                  |
| `chrome_cdp_timeout`    | Chromium never became reachable on the CDP port within 30 seconds.                           |
| `gateway_failed`        | The OpenClaw gateway failed to start. Check `/data/gateway.log`.                             |
| `vnc_disconnected`      | (human mode) The noVNC tab closed and the 15s reconnection grace period expired.             |

See [`troubleshooting.md`](troubleshooting.md) for diagnosing each one.

## Ports

| Port | Direction          | Service         | Purpose                                                                 |
| ---- | ------------------ | --------------- | ----------------------------------------------------------------------- |
| 7878 | container-internal | FastAPI server  | Action/screenshot API, session control                                  |
| 9222 | container-internal | CDP             | Page JavaScript must **not** see this; bound to `127.0.0.1` for stealth |
| 9223 | container-external | `socat` → 9222  | External DevTools/Playwright connection to Chromium                     |
| 6080 | host-exposed       | noVNC           | Human mode only                                                         |

## API endpoints

The extension server exposes these routes on port 7878 (container-internal). See [`extension-server/README.md`](../extension-server/README.md) for the authoritative reference.

| Method | Path                  | Description                                 |
| ------ | --------------------- | ------------------------------------------- |
| GET    | `/api/status`         | Health check                                |
| POST   | `/api/action`         | Record a browser action (JSON body)         |
| POST   | `/api/screenshot`     | Store a screenshot (base64 PNG in JSON)     |
| POST   | `/api/stop`           | Signal session stop, finalize bookkeeping   |
| POST   | `/api/stop-recording` | Stop ffmpeg recording, finalize MP4         |

## Related reading

- [`data_format.md`](data_format.md) — the artifacts produced in `/data`
- [`openclaw_integration.md`](openclaw_integration.md) — what the agent side looks like
- [`request_interceptor.md`](request_interceptor.md) — the CDP-level interception path
- [`../chrome-extension/README.md`](../chrome-extension/README.md) — extension internals and stealth
