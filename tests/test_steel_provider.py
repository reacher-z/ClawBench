"""End-to-end test of the Steel browser provider.

This is the load-bearing integration test: it runs an actual ClawBench
case through `clawbench run --browser=steel` against a real Steel session
and asserts the rich-artifact contract holds. Gated on $STEEL_API_KEY so
CI on forks without secrets just skips it.

Per CLAUDE.md project policy: no mocks. We use real Steel + real container.
The container build is expected to already be present (the test passes
``--no-build`` to keep the per-run cost down — run ``clawbench run --help``
once with a normal harness to populate the image cache, then this test).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


STEEL_API_KEY = os.environ.get("STEEL_API_KEY", "").strip()
RUN_LIVE = os.environ.get("CLAWBENCH_RUN_STEEL_INTEGRATION_TEST", "").strip() == "1"

# This test is opt-in. It needs a real Steel API key, a configured model
# in ~/.../claw-bench/models.yaml, AND at least one harness image already
# built locally (since it passes --no-build to keep the test fast). We
# require an explicit env-var opt-in so a casual `pytest` doesn't burn
# Steel credits or attempt a 5-minute container run by accident.
pytestmark = pytest.mark.skipif(
    not (STEEL_API_KEY and RUN_LIVE),
    reason="set STEEL_API_KEY + CLAWBENCH_RUN_STEEL_INTEGRATION_TEST=1 to run",
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def _pick_test_case() -> Path:
    """Pick a fast, network-light test case for the smoke run."""
    candidates = sorted((REPO_ROOT / "test-cases").glob("001-*"))
    if not candidates:
        pytest.skip("no test-cases/001-* directory found")
    return candidates[0]


def _pick_harness() -> str:
    """Use a Python-only harness so the test doesn't depend on Node tooling
    being preinstalled in the container build cache."""
    return os.environ.get("CLAWBENCH_TEST_HARNESS", "browser-use")


def _pick_model() -> str:
    return os.environ.get("CLAWBENCH_TEST_MODEL", "claude-sonnet-4-6")


def test_steel_run_produces_rich_artifacts(tmp_path):
    case_dir = _pick_test_case()
    harness = _pick_harness()
    model = _pick_model()

    out_dir = tmp_path / "claw-output"
    cmd = [
        sys.executable, "-m", "clawbench", "run",
        str(case_dir), model,
        "--output-dir", str(out_dir),
        "--no-build",
        "--no-upload",
        "--harness", harness,
        "--browser", "steel",
    ]

    env = {**os.environ, "STEEL_API_KEY": STEEL_API_KEY}
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)

    # Locate the per-run output directory (run.py adds <model>/<run-name>/)
    run_dirs = list(out_dir.rglob("run-meta.json"))
    assert run_dirs, (
        f"no run-meta.json produced. stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    run_dir = run_dirs[0].parent

    # 1) run-meta.json carries the Steel viewer URL
    meta = json.loads((run_dir / "run-meta.json").read_text())
    assert meta["browser"] == "steel"
    assert "steel_session_id" in meta
    # The session viewer URL is the user-facing replay link; if Steel
    # didn't return one, the rest of the rich-artifact promise breaks.
    assert "steel_session_viewer_url" in meta or "steel_debug_url" in meta

    # 2) Steel artifacts directory exists with the expected files
    steel_dir = run_dir / "data" / "steel"
    assert steel_dir.is_dir()
    assert (steel_dir / "session.json").exists()

    session_blob = json.loads((steel_dir / "session.json").read_text())
    assert session_blob.get("id"), "session.json missing id"
    # Status post-run should be Released (we release in the shim shutdown)
    # or Failed (if Steel/network had a hiccup). Either way it shouldn't
    # be "Live" by the time the artifact collector ran.
    status = (session_blob.get("status") or "").lower()
    assert status in ("released", "failed", "expired"), (
        f"unexpected steel session status: {status}"
    )

    # browser-version is captured opportunistically; if Steel's CDP refused
    # the Browser.getVersion call (rare), the file may be empty {} but
    # should still exist.
    assert (steel_dir / "browser-version.json").exists()

    # 3) interception.json is present either way (real intercept or
    #    ensure_interception's stop-reason fallback).
    assert (run_dir / "data" / "interception.json").exists()
