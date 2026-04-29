#!/usr/bin/env python3
"""Mock Anthropic meta API for the claude-code-chrome-extension harness.

Interactive Claude Code CLI (used by `--chrome`) makes a dozen preflight calls
to `https://api.anthropic.com/api/…` (profile, organizations, settings,
team_memory, policy_limits, etc.) at startup before the first model turn.
These are hardcoded to a separate `BASE_API_URL` that bypasses
`ANTHROPIC_BASE_URL`, so with a placeholder key they all 401 and the CLI
aborts with "Invalid API key · Fix external API key".

We rewrite `BASE_API_URL` to point at this server (see Dockerfile) and
return canned "everything is fine, you are a subscriber" responses. Any
path we haven't enumerated is answered with `{}` / 200 so a new CLI release
that adds endpoints does not silently break the harness.
"""
from __future__ import annotations

import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

ACCOUNT_UUID = "00000000-0000-4000-a000-000000000001"
ORG_UUID = "00000000-0000-4000-a000-000000000002"

ACCOUNT = {
    "uuid": ACCOUNT_UUID,
    "email_address": "clawbench@clawbench.local",
    "display_name": "ClawBench Harness",
    "full_name": "ClawBench Harness",
}
ORGANIZATION = {
    "uuid": ORG_UUID,
    "name": "ClawBench",
    "organization_type": "claude_max",
    "rate_limit_tier": "default_2025_09",
    "has_extra_usage_enabled": True,
    "subscription_expires_at": None,
    "subscription_created_at": "2025-01-01T00:00:00Z",
    "billing_type": "subscription",
}
PROFILE = {
    "account": ACCOUNT,
    "organization": ORGANIZATION,
    "subscriptionType": "max",
    "rateLimitTier": "default_2025_09",
    "hasExtraUsageEnabled": True,
    "billingType": "subscription",
}


@app.get("/api/hello")
async def hello() -> dict:
    return {"status": "ok", "timestamp": int(time.time())}


@app.get("/api/claude_cli_profile")
async def cli_profile() -> dict:
    return PROFILE


@app.get("/api/oauth/profile")
async def oauth_profile() -> dict:
    return PROFILE


@app.get("/api/oauth/account/settings")
async def oauth_account_settings() -> dict:
    return {"settings": {}}


@app.get("/api/claude_cli/bootstrap")
async def cli_bootstrap() -> dict:
    return {
        "account": ACCOUNT,
        "organization": ORGANIZATION,
        "profile": PROFILE,
        "features": {},
    }


@app.get("/api/claude_code/settings")
async def claude_code_settings() -> dict:
    return {"settings": {}}


@app.get("/api/claude_code/policy_limits")
async def policy_limits() -> dict:
    return {"limits": {}}


@app.get("/api/claude_code/notification/preferences")
async def notif_prefs() -> dict:
    return {"preferences": {}}


@app.get("/api/organizations")
async def organizations() -> dict:
    return {"organizations": [ORGANIZATION]}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def catch_all(path: str, request: Request) -> JSONResponse:
    # Every other meta endpoint — claude_code_penguin_mode, grove_notice_viewed,
    # team_memory, referral/*, admin_requests/*, etc. — returns a harmless 200.
    return JSONResponse({}, status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=4001, log_level="warning")
