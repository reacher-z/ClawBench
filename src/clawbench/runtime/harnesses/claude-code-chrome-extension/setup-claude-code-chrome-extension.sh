#!/bin/bash
set -e

# Setup for the claude-code-chrome-extension harness.
# Mirrors setup-claude-code.sh but drops the Playwright MCP config — the
# --chrome flag brings its own browser surface via the Claude in Chrome
# extension + native messaging, so we don't need Playwright at all.

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

# Generate /tmp/claude-code-env.sh + /tmp/litellm-config.yaml.
# Everything routes through LiteLLM on localhost:4000 so any api_type supported
# by the regular claude-code harness keeps working here. Note: the Claude in
# Chrome extension is officially documented as requiring a direct Anthropic
# plan — running against a third-party provider via LiteLLM may be rejected
# by the extension at handshake time. Surfaced as a known risk.
python3 - <<'PYEOF'
import json, os, urllib.request
from pathlib import Path
import yaml

base_url = os.environ["BASE_URL"]
model_name = os.environ["MODEL_NAME"]
api_type = os.environ.get("API_TYPE", "anthropic-messages")

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

resolved_model = model_name
is_openrouter = "openrouter.ai" in base_url
if is_openrouter:
    try:
        req = urllib.request.Request(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        for m in resp.get("data", []):
            if m["id"].endswith(f"/{model_name}") or m["id"] == model_name:
                resolved_model = m["id"]
                break
    except Exception as e:
        print(f"WARN: could not resolve OpenRouter model ID: {e}")

litellm_params = {"api_key": key}
if is_openrouter:
    litellm_params["model"] = f"openrouter/{resolved_model}"
elif api_type == "anthropic-messages":
    litellm_params["model"] = f"anthropic/{model_name}"
    if not base_url.startswith("https://api.anthropic.com"):
        litellm_params["api_base"] = base_url
elif api_type == "google-generative-ai":
    litellm_params["model"] = f"gemini/{model_name}"
    if not base_url.startswith("https://generativelanguage.googleapis.com"):
        litellm_params["api_base"] = base_url
elif api_type in ("openai-completions", "openai-responses"):
    litellm_params["model"] = f"openai/{model_name}"
    litellm_params["api_base"] = base_url
else:
    raise SystemExit(f"ERROR: unsupported api_type for claude-code-chrome-extension: {api_type}")

proxy_config = {
    "model_list": [{
        "model_name": model_name,
        "litellm_params": litellm_params,
    }],
    "litellm_settings": {"drop_params": True},
}
proxy_path = Path("/tmp/litellm-config.yaml")
proxy_path.write_text(yaml.dump(proxy_config, default_flow_style=False))
os.chmod(proxy_path, 0o600)

anthropic_base_url = "http://localhost:4000"
anthropic_api_key = "sk-ant-proxy-placeholder-000000"
print(f"API proxy enabled: {api_type} → litellm ({litellm_params['model']})")

env_path = Path("/tmp/claude-code-env.sh")
env_lines = [
    f'export ANTHROPIC_API_KEY="{anthropic_api_key}"',
    f'export ANTHROPIC_BASE_URL="{anthropic_base_url}"',
]
env_path.write_text("\n".join(env_lines) + "\n")
os.chmod(env_path, 0o600)

print(f"Claude Code (Chrome extension) config: model={model_name}, base_url={anthropic_base_url}")
PYEOF

# Pre-seed the Claude CLI config so interactive mode does not block on the
# first-run theme picker, workspace trust dialog, or Claude-in-Chrome
# onboarding wizard — all of which would otherwise swallow our piped prompt
# before the agent even starts running.
python3 - <<'PYEOF'
import json, os, pathlib
cfg_path = pathlib.Path("/root/.claude.json")
cfg = {}
if cfg_path.exists():
    try:
        cfg = json.loads(cfg_path.read_text())
    except json.JSONDecodeError:
        cfg = {}
cfg.update({
    "hasCompletedOnboarding": True,
    "hasCompletedClaudeInChromeOnboarding": True,
    "hasTrustDialogAccepted": True,
    "theme": "dark",
    "claudeInChromeDefaultEnabled": True,
    "bypassPermissionsModeAccepted": True,
    "skipDangerousModePermissionPrompt": True,
    # Disable self-update at the config level too (belt + suspenders with the
    # env vars in run-harness.sh). Without this, 2.1.110 upgrades to the
    # native installer on first launch, which wipes our cli.js patches.
    "autoUpdates": False,
    "autoUpdaterStatus": "disabled",
})
# The CLI's `customApiKeyResponses.approved` list is keyed by `vE(K)` which is
# just `K.slice(-20)` — the last 20 chars of the API key. Without the hash
# present the CLI pops the "Detected a custom API key in your environment ·
# Do you want to use this API key?" prompt and blocks on the default "No".
placeholder_key = "sk-ant-proxy-placeholder-000000"
api_key_hash = placeholder_key[-20:]
api_responses = cfg.setdefault("customApiKeyResponses", {"approved": [], "rejected": []})
if api_key_hash not in api_responses.get("approved", []):
    api_responses.setdefault("approved", []).append(api_key_hash)
# Workspace trust is tracked per-project under config.projects[path]. Without
# this, the "Is this a project you trust?" dialog eats the piped prompt on
# every run.
workspace = "/root/workspace"
projects = cfg.setdefault("projects", {})
project_entry = projects.setdefault(workspace, {})
project_entry["hasTrustDialogAccepted"] = True
project_entry.setdefault("projectOnboardingSeenCount", 1)
project_entry.setdefault("hasClaudeMdExternalIncludesApproved", True)
project_entry.setdefault("hasClaudeMdExternalIncludesWarningShown", True)
cfg_path.write_text(json.dumps(cfg, indent=2))
os.chmod(cfg_path, 0o600)
print("Seeded /root/.claude.json with onboarding-skip flags")
PYEOF
