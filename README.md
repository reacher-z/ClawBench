# ClawBench

**A real-browser benchmark for evaluating web agents in isolated containers.**

[**Quick Start**](docs/quickstart.md) · [**Documentation**](docs/) · [**Test Cases**](test-cases/README.md) · [**Contributing**](CONTRIBUTING.md)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![Podman](https://img.shields.io/badge/podman-rootless-purple.svg)](https://podman.io/)
[![Test Cases](https://img.shields.io/badge/test_cases-153-green.svg)](test-cases/README.md)

---

## News

- **[2026-04]** Documentation overhaul — new `docs/` tree, troubleshooting guide, and `CONTRIBUTING.md`.
- **[2026-03]** Initial open-source release — 153 test cases, OpenClaw integration, Docker + Podman support.

## Overview

ClawBench runs each web task in an isolated Docker (or rootless Podman) container with a real Chromium browser, a custom recording extension, and an [OpenClaw](https://github.com/openclaw/openclaw) agent. Every DOM event, HTTP request, screenshot, and a full MP4 of the session is captured to `/data`. A request interceptor blocks irreversible actions (checkout, email send, form submit) so agents can be evaluated against real sites without real-world side effects. The benchmark ships with **153 test cases across 27 task categories** — daily life, job search, office tasks, shopping, entertainment, travel, dev, and more.

## Features

- **Real browser, real sites** — Chromium with 4-layer stealth patching, not a headless shell. See [`chrome-extension/README.md`](chrome-extension/README.md).
- **Complete session capture** — DOM events, HTTP requests, per-action screenshots, and a full MP4 recording of every run.
- **Safe by construction** — CDP-level request interceptor blocks irreversible actions (public reviews, job apps, email sends) before they reach the server.
- **153 test cases** across 27 task categories — see the [test case gallery](docs/test_cases.md).
- **Docker and rootless Podman** — auto-detects the runtime; forced via `CONTAINER_ENGINE`.
- **Batch runner** with concurrency control, rolling start, and optional HuggingFace auto-upload.
- **Human mode** via noVNC for collecting human baselines and debugging test cases.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Container (Docker / Podman)                    │
│                                                 │
│  ┌───────────┐   DOM events  ┌──────────────┐   │
│  │ content.js├──────────────►│ background.js│   │
│  └───────────┘               └──┬──────┬────┘   │
│                                 │      │        │
│  ┌──────────┐            ┌──────▼──────▼────┐   │
│  │  Xvfb    │◄──ffmpeg──►│  FastAPI Server  │   │
│  │  :99     │  x11grab   │  :7878           │   │
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

For the full container lifecycle, watchdog stop reasons, and data-flow details, see [`docs/architecture.md`](docs/architecture.md).

## Quick Start

```bash
# 1. Clone
git clone https://github.com/reacher-z/clawbench.git && cd clawbench

# 2. Configure PurelyMail (disposable email per run)
cp .env.example .env
$EDITOR .env                         # fill PURELY_MAIL_API_KEY and PURELY_MAIL_DOMAIN

# 3. Configure at least one model
cp models/models.example.yaml models/models.yaml
$EDITOR models/models.yaml           # replace the placeholder API key

# 4. Launch the interactive menu
./run.sh

# 5. Inspect results in test-output/<model>/<case>-.../data/
```

For a **full 5-minute walkthrough** that ends with a recorded agent run, see [`docs/quickstart.md`](docs/quickstart.md).
For installation prerequisites (Docker/Podman install, PurelyMail signup, model API keys), see [`docs/installation.md`](docs/installation.md).

## System Requirements

| Item              | Minimum                              | Recommended                     |
| ----------------- | ------------------------------------ | ------------------------------- |
| RAM               | 4 GB free                            | 8 GB+ (batch mode)              |
| Disk              | 5 GB (image + one run)               | 20 GB+                          |
| CPU               | 2 cores                              | 4+ cores                        |
| OS                | Linux x86_64, macOS (Docker Desktop) | Linux x86_64                    |
| Container runtime | Docker 24+ or Podman 4+              | Podman (rootless, no sudo)      |
| Python            | 3.11+                                | 3.12                            |
| Other             | `uv`, `ffmpeg` (host), Chrome/Chromium for extension dev | — |

## Documentation

| Doc                                                             | What's in it                                                     |
| --------------------------------------------------------------- | ---------------------------------------------------------------- |
| [`docs/installation.md`](docs/installation.md)                  | OS requirements, Docker/Podman install, PurelyMail signup, model API keys, container build, verification |
| [`docs/quickstart.md`](docs/quickstart.md)                      | 5-minute first-run walkthrough                                  |
| [`docs/architecture.md`](docs/architecture.md)                  | Container lifecycle, CDP, Xvfb, ffmpeg, watchdog stop reasons   |
| [`docs/data_format.md`](docs/data_format.md)                    | `actions.jsonl`, `requests.jsonl`, `agent-messages.jsonl`, `interception.json`, `run-meta.json` |
| [`docs/openclaw_integration.md`](docs/openclaw_integration.md)  | OpenClaw config, env vars, v2026.3.13 browser patch, tool restrictions |
| [`docs/request_interceptor.md`](docs/request_interceptor.md)    | How the interceptor decides what to block                        |
| [`docs/synthetic_user.md`](docs/synthetic_user.md)              | Alex Green profile, disposable email, resume PDF                 |
| [`docs/human_mode.md`](docs/human_mode.md)                      | noVNC-based manual baselines                                     |
| [`docs/test_cases.md`](docs/test_cases.md)                      | Categorical gallery of the 153 cases                             |
| [`docs/evaluation.md`](docs/evaluation.md)                      | Post-hoc PASS/FAIL evaluation with an agentic reviewer           |
| [`docs/troubleshooting.md`](docs/troubleshooting.md)            | Common failure modes: CDP handshake, build errors, auth, more    |
| [`CONTRIBUTING.md`](CONTRIBUTING.md)                            | **Adding new test cases** (the main contributor lever)           |
| [`test-driver/README.md`](test-driver/README.md)                | Full test-driver reference: CLI, batch runner, flags             |
| [`chrome-extension/README.md`](chrome-extension/README.md)      | Extension internals + 4-layer stealth                            |
| [`extension-server/README.md`](extension-server/README.md)      | FastAPI endpoints + ffmpeg recorder                              |

## Acknowledgments

| Project                                                                              | Role                                            | License   |
| ------------------------------------------------------------------------------------ | ----------------------------------------------- | --------- |
| [OpenClaw](https://github.com/openclaw/openclaw)                                     | Agent driver for browser automation             | per upstream |
| [chrome-devtools-mcp](https://github.com/anthropics/anthropic-quickstarts)           | OpenClaw's browser tool backend                 | per upstream |
| [noVNC](https://github.com/novnc/noVNC)                                              | Browser-based VNC client for human mode         | MPL 2.0   |
| [websockify](https://github.com/novnc/websockify)                                    | WebSocket-to-TCP proxy for VNC                  | LGPL 3.0  |
| [FastAPI](https://fastapi.tiangolo.com/) / [uvicorn](https://www.uvicorn.org/)       | Extension server                                | MIT / BSD |
| [Chromium](https://www.chromium.org/)                                                | Browser runtime                                 | BSD       |
| [PurelyMail](https://purelymail.com/)                                                | Disposable email provider for test accounts    | —         |

## License

Apache License 2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE) for third-party notices.
