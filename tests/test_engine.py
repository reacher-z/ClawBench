"""Tests for :mod:`clawbench.engine`.

Real container probes are expensive and environment-dependent, so we
mock :mod:`shutil.which` for the priority test and :mod:`subprocess.run`
for the status probes. The engine module is thin glue — testing the
glue, not the kernel, is the point."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from clawbench import engine


# ---------------------------------------------------------------------------
# Priority (podman-first, env override wins)
# ---------------------------------------------------------------------------

def test_env_override_wins_when_on_path(monkeypatch):
    monkeypatch.setenv("CONTAINER_ENGINE", "docker")
    with patch("clawbench.engine.shutil.which", side_effect=lambda x: f"/bin/{x}"):
        assert engine.detect_engine() == "docker"


def test_env_override_ignored_when_not_on_path(monkeypatch):
    monkeypatch.setenv("CONTAINER_ENGINE", "docker")
    with patch("clawbench.engine.shutil.which",
               side_effect=lambda x: None if x == "docker" else f"/bin/{x}"):
        # podman is next in priority; env override for docker fails silently.
        assert engine.detect_engine() == "podman"


def test_env_override_junk_is_ignored(monkeypatch):
    monkeypatch.setenv("CONTAINER_ENGINE", "butterflies")
    with patch("clawbench.engine.shutil.which", side_effect=lambda x: f"/bin/{x}"):
        # Invalid value: falls back to probe, which finds podman first.
        assert engine.detect_engine() == "podman"


def test_podman_preferred_over_docker(monkeypatch):
    monkeypatch.delenv("CONTAINER_ENGINE", raising=False)
    with patch("clawbench.engine.shutil.which", side_effect=lambda x: f"/bin/{x}"):
        assert engine.detect_engine() == "podman"


def test_docker_fallback_when_no_podman(monkeypatch):
    monkeypatch.delenv("CONTAINER_ENGINE", raising=False)
    with patch("clawbench.engine.shutil.which",
               side_effect=lambda x: None if x == "podman" else "/bin/docker"):
        assert engine.detect_engine() == "docker"


def test_detect_returns_none_when_nothing_installed(monkeypatch):
    monkeypatch.delenv("CONTAINER_ENGINE", raising=False)
    with patch("clawbench.engine.shutil.which", return_value=None):
        assert engine.detect_engine() is None


# ---------------------------------------------------------------------------
# check_engine — classification
# ---------------------------------------------------------------------------

def test_check_engine_reports_not_installed_when_empty():
    with patch("clawbench.engine.detect_engine", return_value=None):
        s = engine.check_engine()
        assert s.engine is None
        assert s.status == "not_installed"
        assert not s.ready


def test_remediation_hint_covers_every_status():
    # Every documented status code should have a non-empty hint so the
    # TUI never shows a blank fix suggestion.
    for status in [
        "not_installed",
        "podman_no_machine",
        "podman_machine_stopped",
        "podman_low_memory",
        "docker_not_running",
    ]:
        r = engine.EngineStatus("podman", status, "123")
        assert engine.remediation_hint(r), f"missing hint for {status}"


def test_remediation_hint_empty_for_ready():
    s = engine.EngineStatus("podman", "ready", "")
    assert engine.remediation_hint(s) == ""
