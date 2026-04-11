# Data Format

Every ClawBench run produces a directory of artifacts under `test-output/<model>/<case>-.../data/`. These are also present inside the container at `/data/` during the run.

```
data/
  actions.jsonl          # One JSON object per line, every DOM event
  requests.jsonl         # One JSON object per line, every HTTP request
  agent-messages.jsonl   # OpenClaw conversation transcript
  screenshots/           # Timestamped PNGs, one per action
    1710000001234.png
    1710000002345.png
  recording.mp4          # Full session video (H.264, 15 fps)
  interception.json      # Interception result or stop reason
```

And, one level up from `data/`:

```
eval-schema.json         # The schema that was passed to the interceptor
run-meta.json            # Model, timestamp, duration, intercepted flag
```

## `actions.jsonl`

Each line is a JSON object describing one DOM event captured by the Chrome extension. Captured event types: `pageLoad`, `click`, `keydown`, `keyup`, `input`, `scroll`, `change`, `submit`.

```json
{"type": "click", "timestamp": 1710000001234, "url": "https://example.com/", "target": {"tagName": "A", "id": "", "className": "btn", "textContent": "Submit", "xpath": "/html[1]/body[1]/div[1]/a[1]"}, "x": 255, "y": 245}
{"type": "keydown", "timestamp": 1710000002345, "url": "https://example.com/", "target": {"...": "..."}, "key": "Enter"}
{"type": "input", "timestamp": 1710000003456, "url": "https://example.com/", "target": {"...": "..."}, "value": "search query"}
{"type": "pageLoad", "timestamp": 1710000004567, "url": "https://example.com/results", "title": "Results"}
```

### Fields

| Field       | Description                                                            |
| ----------- | ---------------------------------------------------------------------- |
| `type`      | One of the event types above, or `pageLoad`                            |
| `timestamp` | Unix epoch in milliseconds                                             |
| `url`       | Page URL when the event fired                                          |
| `target`    | Metadata about the target element: `tagName`, `id`, `className`, `textContent`, `xpath` |
| `x`, `y`    | Click coordinates (click events only)                                  |
| `key`       | Key name (keydown/keyup only)                                          |
| `value`     | Input value, truncated to 200 chars (input/change only)                |
| `scrollX`, `scrollY` | Scroll position (scroll only)                                 |
| `title`     | Page title (pageLoad only)                                             |

High-frequency events (`scroll`, `input`) are throttled to one every 500 ms. See [`../chrome-extension/README.md`](../chrome-extension/README.md#event-capture) for the extension-side rules.

## `requests.jsonl`

Every HTTP request the browser made during the session, except internal extension/server traffic.

```json
{"timestamp": 1710000001.234, "url": "https://example.com/api?q=test", "method": "POST", "headers": {"Content-Type": "application/json"}, "body": {"action": "send"}, "query_params": {"q": "test"}, "resource_type": "XHR"}
```

| Field           | Description                                                                |
| --------------- | -------------------------------------------------------------------------- |
| `timestamp`     | Unix epoch in seconds (float)                                              |
| `url`           | Full request URL                                                           |
| `method`        | HTTP method (GET, POST, etc.)                                              |
| `headers`       | Request headers (object)                                                   |
| `body`          | Parsed request body: JSON object, form dict, raw string, or `null`        |
| `query_params`  | Parsed URL query parameters (object)                                       |
| `resource_type` | Resource type: Document, Script, Stylesheet, XHR, Fetch, Image, Font, etc. |

Requests to `localhost:7878` and `chrome-extension://` URLs are filtered out.

## `agent-messages.jsonl`

The full OpenClaw conversation transcript. Each line is one of:

- **`type: "session"`** — session metadata (version, id, timestamp)
- **`type: "message"`** — one conversation turn, with `message.role` and `message.content[]`

### Message roles and content types

| `message.role` | Content types                   | Description                        |
| -------------- | ------------------------------- | ---------------------------------- |
| `user`         | `text`                          | The instruction prompt             |
| `assistant`    | `text`, `thinking`, `toolCall`  | Model response, reasoning, actions |
| `toolResult`   | `text`                          | Tool execution results             |

Use this file to audit what the agent actually reasoned about.

## `interception.json`

Written when the interceptor blocks a matching request:

```json
{
  "intercepted": true,
  "request": {
    "url": "https://inbox.purelymail.com/action",
    "method": "POST",
    "params": {},
    "body": {"_action": "send", "_to": "recipient@example.com"}
  }
}
```

Written by the test driver when the interceptor did not fire (the session ended for another reason):

```json
{
  "intercepted": false,
  "stop_reason": "agent_idle",
  "stop_description": "Session stopped: agent went idle (300s no actions) before triggering the interceptor.",
  "request": null
}
```

See [`architecture.md#watchdog-stop-reasons`](architecture.md#watchdog-stop-reasons) for all stop reasons.

## `run-meta.json`

Written by the test driver after the container exits:

```json
{
  "test_case": "886-entertainment-hobbies-experience-topgolf",
  "model": "qwen3.5-397b-a17b",
  "thinking_level": "medium",
  "temperature": null,
  "max_tokens": null,
  "email_used": "cb92784dc43fb0@clawbench.example.com",
  "timestamp": "20260320-040604",
  "time_limit_minutes": 5,
  "duration_seconds": 187,
  "intercepted": true
}
```

## `screenshots/`

One PNG per captured action, named `{timestamp_ms}.png`. Captured by `chrome.tabs.captureVisibleTab` from the extension background worker, throttled to one every 500 ms (like scrolls and inputs).

## `recording.mp4`

Full session video. H.264, 15 fps, recorded by ffmpeg via `x11grab` on Xvfb display `:99`. Started when the extension server boots and finalized on `POST /api/stop-recording` (15 seconds after `POST /api/stop` to let the browser catch any final redraws).

## `eval-schema.json`

Copy of the schema that was passed to the interceptor for this run. Matches the `eval_schema` field from the test case's `task.json`. See [`request_interceptor.md`](request_interceptor.md) for the schema format.
