"""Tests for :mod:`clawbench.image` — pull-or-build logic and version
label comparison. Subprocess calls are mocked: these are fast unit
tests, not integration tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from clawbench import image


def _ok(stdout: str = "", stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr=stderr)


def _fail(stderr: str = "boom") -> SimpleNamespace:
    return SimpleNamespace(returncode=1, stdout="", stderr=stderr)


def test_image_exists_true_on_zero_exit():
    with patch("clawbench.image.subprocess.run", return_value=_ok()):
        assert image.image_exists(engine="podman") is True


def test_image_exists_false_on_nonzero_exit():
    with patch("clawbench.image.subprocess.run", return_value=_fail()):
        assert image.image_exists(engine="podman") is False


def test_image_label_returns_none_for_unlabeled():
    with patch("clawbench.image.subprocess.run", return_value=_ok(stdout="  \n")):
        assert image.image_label(engine="podman") is None


def test_image_label_returns_trimmed_string():
    with patch("clawbench.image.subprocess.run", return_value=_ok(stdout="0.1.0\n")):
        assert image.image_label(engine="podman") == "0.1.0"


def test_pull_retags_on_success():
    calls: list[list[str]] = []

    def fake_run(cmd, *a, **kw):
        calls.append(cmd)
        return _ok()

    with patch("clawbench.image.subprocess.run", side_effect=fake_run):
        ok, detail = image.pull_image(engine="podman", tag="0.1.0")
    assert ok
    assert detail == ""
    # One pull then one tag — both must fire.
    assert any(c[:2] == ["podman", "pull"] for c in calls)
    assert any(c[:2] == ["podman", "tag"] for c in calls)


def test_pull_reports_failure_detail():
    with patch("clawbench.image.subprocess.run", return_value=_fail("manifest unknown")):
        ok, detail = image.pull_image(engine="podman", tag="9.9.9")
    assert not ok
    assert "manifest unknown" in detail


def test_verify_version_accepts_unlabeled_legacy_image():
    with patch("clawbench.image.image_exists", return_value=True), \
         patch("clawbench.image.image_label", return_value=None):
        ok, detail = image.verify_image_version(engine="podman")
    assert ok
    assert detail == ""


def test_verify_version_flags_mismatch():
    with patch("clawbench.image.image_exists", return_value=True), \
         patch("clawbench.image.image_label", return_value="9.9.9"):
        ok, detail = image.verify_image_version(engine="podman")
    assert not ok
    assert "9.9.9" in detail


def test_verify_version_requires_image_present():
    with patch("clawbench.image.image_exists", return_value=False):
        ok, detail = image.verify_image_version(engine="podman")
    assert not ok
    assert "not present" in detail
