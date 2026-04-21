"""Built-in ``claw-code`` harness — ultraworkers' Rust CLI agent."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="claw-code",
    dockerfile="Dockerfile.claw-code",
    setup_script="setup-claw-code.sh",
    run_script="run-claw-code.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="claw-code CLI (ultraworkers) wired up as a ClawBench harness.",
    upstream_url="https://github.com/ultraworkers/claw-code",
    upstream_license="MIT",
)
