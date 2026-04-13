"""ClawBench: Can AI Agents Complete Everyday Online Tasks?

A benchmark of 153 everyday tasks across 144 live websites in 15 life categories.
This package provides the CLI and test driver for running the benchmark against
frontier AI agents inside an isolated Chromium container.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# We publish under two distribution names on PyPI — ``claw-bench`` (primary)
# and ``clawbench`` (alias) — because PyPI's normalization collapses
# case/punctuation but not hyphenation. Whichever name the user installed
# under is the one whose metadata will be queryable.
__version__ = "0.0.0+unknown"
for _dist in ("claw-bench", "clawbench"):
    try:
        __version__ = version(_dist)
        break
    except PackageNotFoundError:
        continue

__all__ = ["__version__"]
