"""Generate and build alias distributions of the ``claw-bench`` package.

PyPI name squatting / similarity-check edge cases mean we publish the
same package contents under several distribution names so that any
reasonable ``pip install <guess>`` reaches us. Each alias directory is
generated from a template pyproject.toml with the ``name`` field
substituted; the code itself lives in one place at ``src/clawbench/``
and is symlinked in.

Usage:
    python scripts/build-aliases.py           # build all aliases
    python scripts/build-aliases.py --publish # also upload via `uv publish`
                                              # (reads UV_PUBLISH_TOKEN)

The first alias (``clawbench``) is the historical one already committed
under ``packaging/clawbench/`` and is left alone — this script only
materializes the *additional* names under ``packaging/aliases/``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import re
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover — only on 3.10-
    tomllib = None

REPO_ROOT = Path(__file__).resolve().parent.parent
ALIASES_DIR = REPO_ROOT / "packaging" / "aliases"


def root_version() -> str:
    """Read the version from the root ``pyproject.toml``.

    All alias distributions share a single version so a release tag
    bumps one place, not seven. The root package name (``claw-bench``)
    is currently blocked on PyPI, but the file is still the source of
    truth for the project's version number.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text()
    if tomllib is not None:
        return tomllib.loads(text)["project"]["version"]
    # Fallback for pre-3.11 interpreters: the version line is unique
    # and trivially parseable; we don't need a full TOML parser just
    # to bootstrap a build script.
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise RuntimeError("could not find version in root pyproject.toml")
    return m.group(1)

# Alias distribution names successfully registered on PyPI.
#
# First wave (packaging PR): clawbench-eval, clawbench-cli, openclawbench,
# clawbench-harness, claw-harness, nail-clawbench. ``harness-bench`` was
# also in this wave but has since been handed over to the HarnessBench
# project (its own repo; owns the name on PyPI going forward).
#
# Second wave (adjacent harness/agent names): harnessos, r2agent, claw-ai,
# claw-agent, claw-eval.
#
# Third wave (research-themed squats): everyday-bench, everyday-agent,
# life-bench, realtask-bench, web-harness, task-harness, video-mcq,
# mcq-bench, vlm-judge, video-judge, nail-bench, nail-agent, nail-eval,
# nail-group.
#
# Names we tried and couldn't take:
#   - 403 (already owned): harness, browser-use, computer-use, claw,
#     clawbot, openclaw, claw-ops, agent-harness
#   - 400 similarity (too close to something we just took or pre-existing):
#     openclaw-bench, claw-bench-harness, harnessbench, harness-os, clawai,
#     clawagent, claweval, lifebench, agentharness, webharness, taskharness,
#     videomcq, mcqbench
# For hyphen/underscore variants of names we DID take (``claw-ai`` ↔
# ``claw_ai``), PEP 503 normalization means pip resolves them to the same
# distribution anyway — so ``pip install claw_ai`` still lands on our
# package.
ALIAS_NAMES = [
    # "harness-bench" was split off into its own project (HarnessBench):
    # https://github.com/reacher-z/HarnessBench — don't re-claim as an alias.
    "clawbench-eval",
    "clawbench-cli",
    "openclawbench",
    "clawbench-harness",
    "claw-harness",
    "nail-clawbench",
    "harnessos",
    "r2agent",
    "claw-ai",
    "claw-agent",
    "claw-eval",
    "everyday-bench",
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
    # Fourth wave — harness-hub was the only slot the permutation sweep
    # cracked. Wave 5 (computer/browser/harness/claw × bench/eval/agent/
    # design, plus agentic/operator/mcp/sandbox/runtime/swarm/rollout/
    # deep-research hot-word combos, 75 candidates) returned zero: the
    # AI-agent generic-permutation namespace is effectively fully claimed
    # on PyPI.
    "harness-hub",
    "r2-harness",
    "scaling-law",
]
# Exhaustive negative result: waves 4-8 tried ~200 additional permutations
# (generic {computer|browser|harness|claw} × {bench|eval|agent|design},
# agent-ecosystem hot words like mcp/operator/agentic/sandbox/runtime,
# unusual noun-noun compounds, numeric suffixes, project-ish compounds).
# Only ``harness-hub`` stuck. Everything else was either 403 already-owned
# or 400 similarity-blocked. Don't waste cycles retrying generic forms —
# the AI-agent namespace is saturated on PyPI. If a specific name matters,
# check pypi.org first rather than adding it here speculatively.

PYPROJECT_TEMPLATE = '''\
# Auto-generated by scripts/build-aliases.py — DO NOT EDIT BY HAND.
# Alias distribution of ``claw-bench``; identical package contents.
# The ``src/clawbench`` directory is a symlink to the real source.

[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "{dist_name}"
version = "{version}"
description = "ClawBench: Can AI Agents Complete Everyday Online Tasks? (alias of claw-bench)"
readme = "README.md"
license = {{ file = "LICENSE" }}
requires-python = ">=3.11"
authors = [
    {{ name = "Yuxuan Zhang" }},
    {{ name = "The ClawBench Authors" }},
]
keywords = [
    "benchmark",
    "ai-agents",
    "browser-automation",
    "web-agents",
    "computer-use",
    "browser-use",
    "evaluation",
    "llm",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "click>=8.1",
    "fpdf2>=2.8",
    "huggingface_hub>=0.27",
    "platformdirs>=4.0",
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
    "questionary>=2.0",
    "rich>=13.0",
]

[project.scripts]
claw-bench = "clawbench.cli:main"
clawbench = "clawbench.cli:main"
clawbench-eval = "clawbench.cli:main"

[project.urls]
Homepage = "https://claw-bench.com"
Repository = "https://github.com/reacher-z/ClawBench"
Paper = "https://arxiv.org/abs/2604.08523"
Dataset = "https://huggingface.co/datasets/NAIL-Group/ClawBench"

[tool.hatch.build.targets.wheel]
packages = ["src/clawbench"]
exclude = [
    "src/clawbench/data/models/models.yaml",
]
'''


def materialize(name: str) -> Path:
    """Create ``packaging/aliases/<name>/`` with pyproject + symlinks."""
    d = ALIASES_DIR / name
    if d.exists():
        shutil.rmtree(d)
    (d / "src").mkdir(parents=True)
    # Symlink the real source — one source of truth, no drift.
    (d / "src" / "clawbench").symlink_to(REPO_ROOT / "src" / "clawbench")
    # Copy README / LICENSE so PyPI long-description renders.
    shutil.copyfile(REPO_ROOT / "README.md", d / "README.md")
    shutil.copyfile(REPO_ROOT / "LICENSE", d / "LICENSE")
    (d / "pyproject.toml").write_text(
        PYPROJECT_TEMPLATE.format(dist_name=name, version=root_version()),
        encoding="utf-8",
    )
    return d


def build(d: Path) -> Path:
    subprocess.run(["uv", "build", "--wheel"], cwd=d, check=True,
                   capture_output=True)
    wheels = sorted((d / "dist").glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"no wheel produced in {d}")
    return wheels[-1]


def publish(wheel: Path, token: str) -> tuple[bool, str]:
    env = dict(os.environ, UV_PUBLISH_TOKEN=token)
    r = subprocess.run(
        ["uv", "publish", str(wheel)],
        env=env, capture_output=True, text=True,
    )
    ok = r.returncode == 0
    detail = (r.stdout + r.stderr).strip()
    return ok, detail


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--publish", action="store_true",
                   help="Upload each built wheel via `uv publish`.")
    args = p.parse_args()

    if args.publish and not os.environ.get("UV_PUBLISH_TOKEN"):
        print("ERROR: UV_PUBLISH_TOKEN env var required with --publish")
        return 2

    token = os.environ.get("UV_PUBLISH_TOKEN", "")
    ALIASES_DIR.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, str, str]] = []
    for name in ALIAS_NAMES:
        print(f"\n=== {name} ===")
        d = materialize(name)
        try:
            wheel = build(d)
        except subprocess.CalledProcessError as e:
            err = (e.stderr.decode() if e.stderr else "") or str(e)
            results.append((name, "build_failed", err[:200]))
            print(f"  BUILD FAILED: {err[:200]}")
            continue
        print(f"  built: {wheel.name} ({wheel.stat().st_size // 1024} KB)")
        if not args.publish:
            results.append((name, "built", str(wheel)))
            continue
        ok, detail = publish(wheel, token)
        if ok:
            results.append((name, "published", ""))
            print(f"  PUBLISHED to PyPI")
        else:
            # Extract the server's actual error for readability.
            tail = detail.splitlines()[-3:] if detail else ["(no output)"]
            results.append((name, "publish_failed", "\n".join(tail)))
            print(f"  PUBLISH FAILED:")
            for line in tail:
                print(f"    {line}")

    print("\n--- summary ---")
    for name, status, detail in results:
        marker = {"published": "OK", "built": "--", "build_failed": "XX",
                  "publish_failed": "XX"}.get(status, "??")
        print(f"  [{marker}] {name}: {status}")
    fails = sum(1 for _, s, _ in results if s.endswith("_failed"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
