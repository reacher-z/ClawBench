"""Which exact code, corpus, and agent produced a run.

`run-meta.json` already records *what* was run — task, model, harness name,
image ids. It does not record the revisions those names resolved to, so two
runs of "openclaw on v2" a month apart are indistinguishable in the artifact
even when the agent, the corpus, and ClawBench itself all moved.

This module fills that gap: the ClawBench version and commit, the corpus
revision, and the agent versions pinned by the harness image. Every lookup is
best-effort and returns ``None`` rather than raising — a PyPI install has no
git repository, a container host may have no `git` at all, and a missing
provenance field must never fail a run that otherwise succeeded.

Results are cached because a batch run builds one of these per task and the
answers cannot change inside a single process.
"""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from clawbench.utils.paths import ASSET_ROOT, HARNESS_ROOT, SOURCE_ROOT

_GIT_TIMEOUT_S = 10

# Version pins declared in a harness Dockerfile: `pkg@1.2.3` for npm and
# `pkg==1.2.3` for pip. This reads the pins the image was built from rather
# than asking the agent for its version, which would need a running container.
_NPM_PIN_RE = re.compile(r"(?<![\w@/])((?:@[\w.-]+/)?[\w.-]+)@(\d[\w.+-]*)")
_PIP_PIN_RE = re.compile(r"([\w.-]+)==(\d[\w.+-]*)")
# Lines that pin something without installing an agent.
_PIN_SKIP_RE = re.compile(r"^\s*(#|FROM |COPY |ENV |LABEL )", re.IGNORECASE)


def _git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


@lru_cache(maxsize=1)
def clawbench_version() -> str | None:
    try:
        return version("clawbench-eval")
    except PackageNotFoundError:
        return None


@lru_cache(maxsize=1)
def _repo_root() -> Path | None:
    """The ClawBench git checkout, when running from source rather than a wheel."""
    if SOURCE_ROOT is None or not (SOURCE_ROOT / ".git").exists():
        return None
    return SOURCE_ROOT


@lru_cache(maxsize=1)
def clawbench_commit() -> dict[str, Any]:
    """Commit, branch, and dirty state of the ClawBench checkout."""
    repo = _repo_root()
    if repo is None:
        return {"commit": None, "branch": None, "dirty": None}
    status = _git(repo, "status", "--porcelain")
    return {
        "commit": _git(repo, "rev-parse", "HEAD"),
        "branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        # `git status` succeeding with no output means a clean tree; a failed
        # lookup returns None, which is not the same claim as "clean".
        "dirty": (status != "") if status is not None else None,
    }


def _relative_to_assets(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(ASSET_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return None


@lru_cache(maxsize=8)
def _corpus_commit(suite_path: str) -> str | None:
    """Last commit that touched this corpus directory."""
    repo = _repo_root()
    if repo is None:
        return None
    return _git(repo, "log", "-1", "--format=%H", "--", suite_path)


def corpus_meta(task_dir: Path | None) -> dict[str, Any]:
    """Which corpus a task came from, and at which revision.

    A task outside the bundled corpora (an explicit ``--cases-dir``) reports
    its suite name but no revision — its history is not ClawBench's to claim.
    """
    if task_dir is None:
        return {"suite": None, "path": None, "revision": None}
    relative = _relative_to_assets(task_dir)
    if relative is None:
        return {"suite": task_dir.parent.name, "path": None, "revision": None}
    # e.g. "test-cases/v2/v2-047-daily-life-personal-care-taskrabbit"
    parts = relative.split("/")
    suite_path = "/".join(parts[:2])
    return {
        "suite": parts[1] if len(parts) > 1 else parts[0],
        "path": suite_path,
        "revision": _corpus_commit(suite_path),
    }


@lru_cache(maxsize=32)
def harness_pins(harness: str) -> dict[str, str]:
    """Agent and plugin versions pinned by a harness Dockerfile.

    Reads the pins the image was built from — `opencode-ai@1.4.4`,
    `@playwright/mcp@0.0.70`, `pip install foo==1.2` — so a trace records the
    exact agent build it used. Returns an empty mapping for a harness with no
    version pins, or one whose Dockerfile cannot be read.
    """
    if harness in ("human", ""):
        return {}
    try:
        from clawbench.runner.run_support.harness_registry import HARNESS_REGISTRY

        dockerfile = HARNESS_REGISTRY.harness_dockerfiles.get(harness)
    except (ImportError, ValueError):
        dockerfile = None
    if dockerfile is None:
        candidates = sorted(HARNESS_ROOT.glob(f"{harness}/Dockerfile.*"))
        dockerfile = candidates[0] if candidates else None
    if dockerfile is None or not dockerfile.is_file():
        return {}
    try:
        text = dockerfile.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    pins: dict[str, str] = {}
    for line in text.splitlines():
        if _PIN_SKIP_RE.match(line):
            continue
        for pattern in (_NPM_PIN_RE, _PIP_PIN_RE):
            for name, pinned in pattern.findall(line):
                pins.setdefault(name, pinned)
    return pins


def _agent_version(harness: str, pins: dict[str, str]) -> str | None:
    """The pin that is the agent itself, not one of its plugins.

    Package names rarely equal the harness name exactly (`opencode` ships as
    `opencode-ai`), so fall back to the pin whose package name contains it.
    """
    if harness in pins:
        return pins[harness]
    for name, pinned in pins.items():
        if harness in name:
            return pinned
    return None


def harness_meta(harness: str, image_id: str | None) -> dict[str, Any]:
    pins = harness_pins(harness)
    return {
        "name": harness,
        "image_id": image_id,
        "pinned_versions": pins or None,
        # Named separately because it is the one a leaderboard row cites.
        "agent_version": _agent_version(harness, pins),
    }


def make_provenance(
    *,
    harness: str,
    harness_image_id: str | None,
    task_dir: Path | None,
) -> dict[str, Any]:
    """The provenance block written into ``run-meta.json``."""
    return {
        "clawbench_version": clawbench_version(),
        **clawbench_commit(),
        "corpus": corpus_meta(task_dir),
        "harness": harness_meta(harness, harness_image_id),
    }
