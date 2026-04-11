# OpenClaw Integration

ClawBench uses [OpenClaw](https://github.com/openclaw/openclaw) as the agent driver. OpenClaw handles the model API calls, tool dispatch, and conversation loop; ClawBench provides the isolated browser environment, records every action, and enforces safety boundaries.

This doc covers how the two are wired together.

## Environment variables

The test driver passes these to the container as environment variables; `setup-openclaw.sh` then writes them into OpenClaw's config at runtime.

| Variable          | Example                                           | Description                                                 |
| ----------------- | ------------------------------------------------- | ----------------------------------------------------------- |
| `MODEL_NAME`      | `claude-sonnet-4-6`, `gemini-3-flash-preview`     | Model identifier                                            |
| `BASE_URL`        | `https://api.openai.com/v1`                       | API base URL                                                |
| `API_TYPE`        | `openai-completions`                              | `openai-completions`, `openai-responses`, `anthropic-messages`, `google-generative-ai` |
| `API_KEY`         | `sk-ant-...`, `AIza...`                           | Single API key                                              |
| `API_KEYS`        | `["key1","key2"]`                                 | Multiple keys for round-robin (takes precedence over `API_KEY`) |
| `INSTRUCTION`     | `"Go to example.com and..."`                      | Task prompt for the agent                                   |
| `TIME_LIMIT_S`    | `300`                                             | Watchdog timeout in seconds (default: 600)                  |
| `THINKING_LEVEL`  | `high`, `low`, `off`                              | Reasoning depth (default: `medium`)                         |
| `TEMPERATURE`     | `0.5`                                             | Sampling temperature (optional)                             |
| `MAX_TOKENS`      | `4096`                                            | Max output tokens (optional)                                |

## Container lifecycle with OpenClaw

The full sequence is in [`architecture.md`](architecture.md#container-lifecycle-agent-mode). The OpenClaw-specific steps are:

1. **`setup-openclaw.sh`** reads the environment variables above and writes:
   - `~/.openclaw/openclaw.json` — gateway config, browser profile, model provider
   - `~/.openclaw/agents/main/agent/auth-profiles.json` — API key credentials
2. **CDP health check** waits up to 30 seconds for `http://127.0.0.1:9222/json/version` to respond.
3. **Gateway** (`openclaw gateway --local`) starts in the background, logs to `/data/gateway.log`.
4. **Agent** (`openclaw agent --session-id clawbench --message "$INSTRUCTION" --local`) starts and begins acting.
5. **Watchdog** monitors `/data/actions.jsonl` for idle, `/data/.stop-requested` for eval matches, and `TIME_LIMIT_S` for the hard deadline.
6. **Cleanup** kills OpenClaw processes, then signals the extension server to stop.

## Configuration files generated at runtime

`setup-openclaw.sh` is the source of truth for what OpenClaw sees. It generates two files:

### `~/.openclaw/openclaw.json`

- Gateway: `localMode: true`, port 18789
- Tool restrictions: `exec` set to `allowlist` with only read-only shell utilities (see below)
- Agent defaults: workspace path, default model
- Browser profile: `cdpUrl: "http://127.0.0.1:9222"` — points at the in-container Chromium
- Model provider: `baseUrl` and `api` type passed directly from `BASE_URL` and `API_TYPE`, plus `thinking_level`, `temperature`, and `max_tokens` if set

### `~/.openclaw/agents/main/agent/auth-profiles.json`

API key credentials for the configured provider. Supports:

- Single key via `API_KEY` (most common)
- Multiple keys via `API_KEYS` as a JSON array — `setup-openclaw.sh` builds a round-robin profile for rate-limited providers

## The v2026.3.13 browser patch

OpenClaw's built-in browser tool uses [chrome-devtools-mcp](https://github.com/anthropics/anthropic-quickstarts/tree/main/chrome-devtools-mcp) to control the browser. As of `v2026.3.13`, the `existing-session` driver hardcodes `--autoConnect` when launching chrome-devtools-mcp, which only discovers Chrome via the `DevToolsActivePort` file in the default user data directory. It ignores the `cdpUrl` set in the browser profile config and never passes `--browserUrl` to chrome-devtools-mcp.

This means the browser tool cannot connect to our Chromium instance running on port 9222. See [openclaw/openclaw#47879](https://github.com/openclaw/openclaw/issues/47879).

### Workaround applied in the Dockerfile

- OpenClaw is pinned to `v2026.3.13`
- A `sed` patch replaces `"--autoConnect"` with `"--browserUrl","http://127.0.0.1:9222"` across all bundled dist files
- Chromium is launched with `--remote-allow-origins=*` (required for chrome-devtools-mcp's internal WebSocket connections on Chrome 132+)

Once [#47879](https://github.com/openclaw/openclaw/issues/47879) is resolved upstream, the version pin and the `sed` patch can be removed. If the patch is missing (e.g., someone bumped the version without re-applying), the agent will get `agent_idle` with zero actions — see [`troubleshooting.md`](troubleshooting.md).

## Tool restrictions

The `exec` tool is set to `allowlist` security mode in the generated config. Only safe, read-only commands are permitted:

```
ls, cat, find, file, grep, sort, head, tail, jq, cut, uniq, tr, wc
```

Commands that could bypass the browser (`curl`, `python`, `node`, `wget`, anything that opens a socket) are blocked. The agent uses `cat` to read files in `/my-info/` (the core files are listed in the instruction prompt, but `ls` is still available for extra-info discovery).

The agent instruction prompt also explicitly requires browser-only task completion — the combination of prompt + allowlist is belt-and-suspenders against the agent "cheating" via shell.

## Multi-key rotation

For rate-limited providers you can supply multiple keys and `setup-openclaw.sh` will build an OpenClaw profile that rotates through them:

```yaml
# models/models.yaml
my-model:
  base_url: https://api.example.com/v1
  api_type: openai-completions
  api_keys:
    - "key-1"
    - "key-2"
    - "key-3"
```

`api_keys` takes precedence over `api_key` if both are set.

## Related reading

- [`architecture.md`](architecture.md) — the full container lifecycle
- [`request_interceptor.md`](request_interceptor.md) — the safety layer between the agent and the real internet
- [`synthetic_user.md`](synthetic_user.md) — the `/my-info/` directory the agent reads for personal details
- [`troubleshooting.md`](troubleshooting.md) — common failure modes
