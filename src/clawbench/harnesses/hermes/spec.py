"""Built-in ``hermes`` harness - Nous Research Hermes Agent."""

from __future__ import annotations

from clawbench.harnesses import HarnessSpec


spec = HarnessSpec(
    name="hermes",
    dockerfile="Dockerfile.hermes",
    setup_script="setup-hermes.sh",
    run_script="run-hermes.sh",
    runtime="python",
    container_isolation="shared",
    requires_credentials=None,
    description="Hermes Agent wired up as a ClawBench harness with native CDP browser tools.",
    upstream_url="https://github.com/NousResearch/hermes-agent",
    upstream_license="MIT",
)
