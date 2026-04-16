"""Built-in ``opencode`` harness."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="opencode",
    dockerfile="Dockerfile.opencode",
    setup_script="setup-opencode.sh",
    run_script="run-opencode.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="opencode coding-agent harness wired up for ClawBench.",
    upstream_url="https://github.com/opencode-ai/opencode",
    upstream_license="Apache-2.0",
)
