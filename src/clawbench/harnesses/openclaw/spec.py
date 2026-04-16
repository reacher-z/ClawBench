"""Built-in ``openclaw`` harness — the reference ClawBench loop."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="openclaw",
    dockerfile="Dockerfile.openclaw",
    setup_script="setup-openclaw.sh",
    run_script="run-openclaw.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="Reference ClawBench harness — Python, CDP, minimal scaffolding.",
    upstream_url="https://github.com/reacher-z/ClawBench",
    upstream_license="Apache-2.0",
)
