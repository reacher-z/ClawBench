"""Built-in ``claude-code-chrome-extension`` harness."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="claude-code-chrome-extension",
    dockerfile="Dockerfile.claude-code-chrome-extension",
    setup_script="setup-claude-code-chrome-extension.sh",
    run_script="run-claude-code-chrome-extension.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="Claude Code CLI driving Google Chrome via the Claude in Chrome extension (--chrome).",
    upstream_url="https://code.claude.com/docs/en/chrome",
    upstream_license="Apache-2.0",
)
