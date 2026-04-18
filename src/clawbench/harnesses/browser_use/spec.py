"""Built-in ``browser-use`` harness — Python framework with native LLM wrappers."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="browser-use",
    dockerfile="Dockerfile.browser-use",
    setup_script="setup-browser-use.sh",
    run_script="run-browser-use.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="browser-use Python framework wired up as a ClawBench harness.",
    upstream_url="https://github.com/browser-use/browser-use",
    upstream_license="MIT",
)
