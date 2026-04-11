# Human Mode

Human mode lets you complete test cases **manually** in the browser instead of using an AI agent. It's the same pipeline — Chromium, the recording extension, the FastAPI server, ffmpeg, the request interceptor — but with noVNC exposed on port 6080 instead of OpenClaw running in the background.

## When to use it

- **Collecting human baselines** for a benchmark paper (how long do humans take, do humans hit the interceptor as expected, etc.).
- **Debugging a new test case** you're authoring — can a human actually complete this? Does the interceptor fire on the right request?
- **Verifying task completability** before spending API credits on agent runs.
- **Capturing the exact terminal HTTP request** so you know what to put in `eval_schema.url_pattern` (see [`request_interceptor.md`](request_interceptor.md#finding-the-right-url-pattern-for-a-new-test-case)).

## Launching human mode

### Via the TUI

```bash
./run.sh
# pick "Human mode", then pick a test case
```

### Via CLI directly

```bash
uv run --project test-driver test-driver/run.py \
    test-cases/886-entertainment-hobbies-experience-topgolf --human
```

## The noVNC URL

After the container starts, the terminal prints:

```
noVNC ready: http://localhost:6080/vnc.html
```

Open that URL in your desktop browser. You'll see Chromium inside your browser tab. Drive it normally — click, type, scroll. Everything is recorded the same way as an agent run.

Tips:

- **Full-screen noVNC** for a cleaner experience (the gear icon in the noVNC toolbar).
- **Resize** your browser tab to the container resolution (1920×1080) for 1:1 pixel mapping.
- **Close the tab** when you're done — human mode detects the VNC disconnect and stops the session (after a 15-second grace period in case you're just reloading).

## How human mode ends

The session stops on any of these:

| Stop reason         | Trigger                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------------- |
| `eval_matched`      | The request interceptor matched the configured `url_pattern` — you triggered the target action. |
| `vnc_disconnected`  | You closed the noVNC tab (15-second grace period for page reloads / reconnection).      |
| `time_limit_exceeded` | The test case's `time_limit` (in minutes, from `task.json`) expired.                    |

After the session ends, results are collected into `test-output/human/<case>-.../data/` in the same format as agent runs. See [`data_format.md`](data_format.md).

## What gets recorded

Exactly what an agent run records:

- `actions.jsonl` — every click, keystroke, scroll, navigation you made
- `requests.jsonl` — every HTTP request the browser sent
- `screenshots/` — one PNG per action (throttled like agent mode)
- `recording.mp4` — full H.264 screen recording
- `interception.json` — the blocked request if the interceptor fired, else a stop-reason fallback

No `agent-messages.jsonl` — that's agent-specific.

## Caveats

- Human mode still **uses a disposable PurelyMail email**. You need valid `PURELY_MAIL_API_KEY` and `PURELY_MAIL_DOMAIN` in `.env`. The email is created and deleted the same way as for agent runs.
- The **request interceptor is active**. If you hit the terminal action, the interceptor blocks the request and the session stops. That's correct behavior and mirrors what the agent will experience.
- Network performance through noVNC depends on your browser tab and local network — expect some input lag over a flaky connection.

## Related reading

- [`installation.md`](installation.md) — make sure ports are right on rootless Podman
- [`request_interceptor.md`](request_interceptor.md) — what the interceptor will block as you click around
- [`troubleshooting.md`](troubleshooting.md#10-podman-rootless-cannot-bind-port-6080-human-mode) — port 6080 binding on rootless Podman
