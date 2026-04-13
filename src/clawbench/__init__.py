"""ClawBench: Can AI Agents Complete Everyday Online Tasks?

A benchmark of 153 everyday tasks across 144 live websites in 15 life categories.
This package provides the CLI and test driver for running the benchmark against
frontier AI agents inside an isolated Chromium container.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# We publish under several distribution names on PyPI (the original
# ``claw-bench`` / ``clawbench`` names are currently held by an
# unrelated project, so the user-facing name is one of the aliases
# below). Whichever name the user installed under is the one whose
# metadata will be queryable via ``importlib.metadata``.
__version__ = "0.0.0+unknown"
for _dist in (
    "clawbench-eval",     # primary (README Quick Start)
    "clawbench-cli",
    "nail-clawbench",     # org-prefixed alias
    "clawbench-harness",
    "harness-bench",
    "openclawbench",
    "claw-harness",
    "harnessos",          # second-wave defensive squats
    "r2agent",
    "claw-ai",
    "claw-agent",
    "claw-eval",
    "everyday-bench",     # third-wave research-themed squats
    "everyday-agent",
    "life-bench",
    "realtask-bench",
    "web-harness",
    "task-harness",
    "video-mcq",
    "mcq-bench",
    "vlm-judge",
    "video-judge",
    "nail-bench",
    "nail-agent",
    "nail-eval",
    "nail-group",
    "harness-hub",        # fourth-wave singleton winner
    "claw-bench",         # original primary (blocked; left for future)
    "clawbench",          # original alias  (blocked; left for future)
):
    try:
        __version__ = version(_dist)
        break
    except PackageNotFoundError:
        continue

__all__ = ["__version__"]
