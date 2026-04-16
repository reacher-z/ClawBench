#!/bin/bash
set -e

# All config comes from env vars set by the test driver (sourced from models.yaml).
# BASE_URL and MODEL_NAME are required.
if [ -z "$BASE_URL" ] || [ -z "$MODEL_NAME" ]; then
  echo "ERROR: BASE_URL and MODEL_NAME must be set"
  exit 1
fi

if [ -n "$TEMPERATURE" ]; then
  echo "WARN: Claude Code CLI does not expose a --temperature flag; TEMPERATURE='$TEMPERATURE' will be ignored."
fi
if [ -n "$MAX_TOKENS" ]; then
  echo "WARN: Claude Code CLI does not expose a --max-tokens flag; MAX_TOKENS='$MAX_TOKENS' will be ignored."
fi

# Extract API key, write env-var exports, and optionally configure the
# LiteLLM translation proxy for non-Anthropic api_types.
python3 - <<'PYEOF'
import json, os
from pathlib import Path

base_url = os.environ["BASE_URL"]
model_name = os.environ["MODEL_NAME"]
api_type = os.environ.get("API_TYPE", "anthropic-messages")

# Pick a single API key (first from API_KEYS list, else API_KEY).
keys_json = os.environ.get("API_KEYS", "")
single_key = os.environ.get("API_KEY", "")
key = ""
if keys_json:
    try:
        parsed = json.loads(keys_json)
        if parsed:
            key = parsed[0]
            if len(parsed) > 1:
                print(f"WARN: Claude Code does not rotate keys — using first of {len(parsed)}")
    except json.JSONDecodeError:
        pass
if not key and single_key:
    key = single_key
if not key:
    raise SystemExit("ERROR: no API key provided (API_KEYS or API_KEY)")

# ── Decide whether to use the LiteLLM translation proxy ──────────────
# Claude Code speaks only the Anthropic messages API. For other api_types
# we start a LiteLLM proxy that accepts Anthropic-format requests on a
# local port and translates them to the target format.
needs_proxy = api_type != "anthropic-messages"

if needs_proxy:
    import urllib.request
    import yaml  # installed as a litellm dependency

    is_openrouter = "openrouter.ai" in base_url

    if is_openrouter:
        # LiteLLM's openrouter/ provider properly translates reasoning
        # content between Anthropic and OpenAI formats. It needs the full
        # OpenRouter model ID (e.g. "qwen/qwen3.5-397b-a17b"), so resolve
        # it from the models endpoint.
        full_model_id = model_name
        try:
            req = urllib.request.Request(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
            for m in resp.get("data", []):
                if m["id"].endswith(f"/{model_name}") or m["id"] == model_name:
                    full_model_id = m["id"]
                    break
        except Exception as e:
            print(f"WARN: could not resolve OpenRouter model ID: {e}")

        litellm_model = f"openrouter/{full_model_id}"
        litellm_params = {
            "model": litellm_model,
            "api_key": key,
        }
    else:
        # Generic OpenAI-compatible endpoint.
        _PREFIX_MAP = {
            "openai-completions": "openai",
            "openai-responses":   "openai",
            "google-generative-ai": "gemini",
        }
        prefix = _PREFIX_MAP.get(api_type, "openai")
        litellm_model = f"{prefix}/{model_name}"
        litellm_params = {
            "model": litellm_model,
            "api_key": key,
            "api_base": base_url,
        }

    proxy_config = {
        "model_list": [{
            "model_name": model_name,
            "litellm_params": litellm_params,
        }],
        # drop_params: silently drop Anthropic-specific params that can't
        # be translated (e.g. thinking budget) instead of erroring.
        "litellm_settings": {"drop_params": True},
    }

    proxy_path = Path("/tmp/litellm-config.yaml")
    proxy_path.write_text(yaml.dump(proxy_config, default_flow_style=False))
    os.chmod(proxy_path, 0o600)

    # Claude Code will talk to the local proxy instead of the real endpoint.
    # The proxy key is arbitrary — LiteLLM proxy doesn't validate it.
    anthropic_base_url = "http://localhost:4000"
    anthropic_api_key = "sk-proxy-placeholder"
    print(f"API proxy enabled: {api_type} → litellm ({litellm_model})")
else:
    anthropic_base_url = base_url
    anthropic_api_key = key

# Write a sourceable env file for the run script.
env_path = Path("/tmp/claude-code-env.sh")
env_lines = [
    f'export ANTHROPIC_API_KEY="{anthropic_api_key}"',
    f'export ANTHROPIC_BASE_URL="{anthropic_base_url}"',
]
env_path.write_text("\n".join(env_lines) + "\n")
os.chmod(env_path, 0o600)

# Write MCP config file for --mcp-config flag.
mcp_config = {
    "mcpServers": {
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp", "--cdp-endpoint", "http://127.0.0.1:9222"],
        },
    },
}
mcp_path = Path("/tmp/claude-mcp.json")
mcp_path.write_text(json.dumps(mcp_config, indent=2))
os.chmod(mcp_path, 0o644)

print(f"Claude Code config: model={model_name}, base_url={anthropic_base_url}")
PYEOF
