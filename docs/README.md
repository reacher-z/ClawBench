# ClawBench Documentation

This directory contains the full ClawBench documentation. The root [`README.md`](../README.md) stays concise — deep dives live here, one file per concept.

## Where to start

- **Brand new?** Read [`installation.md`](installation.md), then [`quickstart.md`](quickstart.md).
- **Adding a test case?** See [`../CONTRIBUTING.md`](../CONTRIBUTING.md) and browse [`test_cases.md`](test_cases.md) for examples.
- **Something broke?** Check [`troubleshooting.md`](troubleshooting.md) first.
- **Want to understand the internals?** Start with [`architecture.md`](architecture.md).

## Index

| Doc                                              | What's in it                                                                 |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| [`installation.md`](installation.md)             | System requirements, Docker/Podman install, PurelyMail signup, model API keys, build, verification |
| [`quickstart.md`](quickstart.md)                 | Minimal 5-minute first-run walkthrough                                       |
| [`architecture.md`](architecture.md)             | Container lifecycle, CDP, Xvfb, ffmpeg, watchdog stop reasons, ports         |
| [`data_format.md`](data_format.md)               | All output artifact formats (`actions.jsonl`, `requests.jsonl`, `agent-messages.jsonl`, `interception.json`, `run-meta.json`, screenshots, MP4) |
| [`openclaw_integration.md`](openclaw_integration.md) | OpenClaw env vars, lifecycle, config generation, multi-key rotation, the v2026.3.13 browser patch, tool restrictions |
| [`request_interceptor.md`](request_interceptor.md) | Interceptor mechanics, schema, when-to-block table, placeholder pattern    |
| [`synthetic_user.md`](synthetic_user.md)         | `/my-info/` layout, Alex Green profile, disposable email lifecycle, resume PDF generation |
| [`human_mode.md`](human_mode.md)                 | noVNC-based manual baselines, stop conditions                                |
| [`test_cases.md`](test_cases.md)                 | Categorical gallery of the 153 cases, naming convention, how to browse      |
| [`evaluation.md`](evaluation.md)                 | Post-hoc PASS/FAIL evaluation with the agentic reviewer prompt              |
| [`troubleshooting.md`](troubleshooting.md)       | 10 common failure modes with symptom → cause → fix                           |

## Component-level references

These READMEs live alongside their source and are not duplicated here:

- [`../test-driver/README.md`](../test-driver/README.md) — full CLI, batch runner, flags, output layout, test-case format
- [`../chrome-extension/README.md`](../chrome-extension/README.md) — extension internals, 4-layer stealth, bot-detection test results
- [`../extension-server/README.md`](../extension-server/README.md) — FastAPI endpoints and ffmpeg screen recorder
