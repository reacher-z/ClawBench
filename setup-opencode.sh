#!/bin/bash
set -e

# All config comes from env vars set by the test driver (sourced from models.yaml).
# BASE_URL, API_TYPE, and MODEL_NAME are required.
if [ -z "$BASE_URL" ] || [ -z "$API_TYPE" ] || [ -z "$MODEL_NAME" ]; then
  echo "ERROR: BASE_URL, API_TYPE, and MODEL_NAME must be set"
  exit 1
fi

# Map ClawBench api_type → opencode npm adapter package.
# All four adapters are bundled in the opencode-ai binary — no extra installs.
case "$API_TYPE" in
  openai-completions)
    NPM_PKG="@ai-sdk/openai-compatible"
    ;;
  openai-responses)
    NPM_PKG="@ai-sdk/openai"
    ;;
  anthropic-messages)
    NPM_PKG="@ai-sdk/anthropic"
    ;;
  google-generative-ai)
    NPM_PKG="@ai-sdk/google"
    ;;
  *)
    echo "ERROR: opencode harness does not support API_TYPE='$API_TYPE'" >&2
    echo "Supported: openai-completions, openai-responses, anthropic-messages, google-generative-ai" >&2
    exit 1
    ;;
esac
export NPM_PKG

mkdir -p ~/.config/opencode

# Generate opencode.json via Python for safe JSON escaping.
python3 - <<'PYEOF'
import json, os

npm_pkg  = os.environ["NPM_PKG"]
base_url = os.environ["BASE_URL"]
model    = os.environ["MODEL_NAME"]

# Per-call knobs — all optional.
thinking    = (os.environ.get("THINKING_LEVEL") or "").strip()
temperature = (os.environ.get("TEMPERATURE") or "").strip()
max_tokens  = (os.environ.get("MAX_TOKENS") or "").strip()

# Pick a single key: prefer first entry of API_KEYS json list, else API_KEY.
# Multi-key rotation is openclaw-only for MVP.
keys_json  = os.environ.get("API_KEYS", "")
single_key = os.environ.get("API_KEY", "")
try:
    keys = json.loads(keys_json) if keys_json else []
except json.JSONDecodeError:
    keys = []
api_key = keys[0] if keys else single_key
if not api_key:
    raise SystemExit("ERROR: no api_key or api_keys set for opencode harness")

# Reasoning / thinking:
# THINKING_LEVEL ∈ {off, minimal, low, medium, high, xhigh, adaptive} (ClawBench schema).
# opencode model entry has a boolean `reasoning` flag that declares capability.
# For effort control, we pass providerOptions.openai.reasoningEffort which the
# @ai-sdk/openai and @ai-sdk/openai-compatible adapters honor (mapped to
# OpenAI-style reasoning_effort in the request body).
EFFORT_MAP = {
    "minimal": "low",
    "low":     "low",
    "medium":  "medium",
    "high":    "high",
    "xhigh":   "high",
    "adaptive": "medium",
}
reasoning_enabled = thinking != "off"
effort = EFFORT_MAP.get(thinking) if reasoning_enabled else None

# Per-call options (temperature, maxOutputTokens, providerOptions).
call_opts: dict = {}
if temperature:
    try:
        call_opts["temperature"] = float(temperature)
    except ValueError:
        pass
if max_tokens:
    try:
        call_opts["maxOutputTokens"] = int(max_tokens)
    except ValueError:
        pass
if effort and npm_pkg in ("@ai-sdk/openai", "@ai-sdk/openai-compatible"):
    call_opts.setdefault("providerOptions", {}).setdefault("openai", {})["reasoningEffort"] = effort

# Build the model entry.
model_entry: dict = {"id": model, "name": model}
if reasoning_enabled:
    model_entry["reasoning"] = True
if call_opts:
    model_entry["options"] = call_opts

config = {
    "$schema": "https://opencode.ai/config.json",
    "model": f"clawbench/{model}",
    "provider": {
        "clawbench": {
            "npm": npm_pkg,
            "name": "ClawBench",
            "options": {
                "baseURL": base_url,
                "apiKey": api_key,
            },
            "models": {
                model: model_entry,
            },
        },
    },
    # chrome-devtools-mcp is installed globally in Dockerfile.opencode.
    # --browserUrl points it at the in-container Chrome CDP (9222).
    "mcp": {
        "chrome-devtools": {
            "type": "local",
            "command": [
                "chrome-devtools-mcp",
                "--browserUrl", "http://127.0.0.1:9222",
            ],
            "enabled": True,
        },
    },
    # Mirror openclaw's exec allowlist: bash restricted to safe read-only
    # commands; writes, edits, and network fetches denied. Chrome-devtools-mcp
    # tools stay at default (allow) so the browser can be driven.
    "permission": {
        "bash": {
            "*":      "deny",
            "ls *":   "allow",
            "cat *":  "allow",
            "find *": "allow",
            "file *": "allow",
            "jq *":   "allow",
            "cut *":  "allow",
            "uniq *": "allow",
            "head *": "allow",
            "tail *": "allow",
            "tr *":   "allow",
            "wc *":   "allow",
            "grep *": "allow",
            "sort *": "allow",
        },
        "edit":     "deny",
        "write":    "deny",
        "webfetch": "deny",
    },
    "autoupdate": False,
}

path = os.path.expanduser("~/.config/opencode/opencode.json")
with open(path, "w") as f:
    json.dump(config, f, indent=2)
os.chmod(path, 0o600)

print(f"Wrote opencode config: {path}")
print(f"  provider:    {npm_pkg}")
print(f"  model:       {model}")
print(f"  reasoning:   {reasoning_enabled}{' (effort=' + effort + ')' if effort else ''}")
if temperature: print(f"  temperature: {temperature}")
if max_tokens:  print(f"  maxOutput:   {max_tokens}")
PYEOF
