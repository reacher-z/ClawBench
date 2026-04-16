"""Built-in ``claude-code`` harness."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="claude-code",
    dockerfile="Dockerfile.claude-code",
    setup_script="setup-claude-code.sh",
    run_script="run-claude-code.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="Claude Code CLI wired up as a ClawBench harness.",
    upstream_url="https://github.com/anthropics/claude-code",
    upstream_license="Apache-2.0",
)
