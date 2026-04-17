"""Built-in ``codex`` harness — OpenAI Codex CLI."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="codex",
    dockerfile="Dockerfile.codex",
    setup_script="setup-codex.sh",
    run_script="run-codex.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="OpenAI Codex CLI wired up as a ClawBench harness.",
    upstream_url="https://github.com/openai/codex",
    upstream_license="Apache-2.0",
)
