"""Tests for :mod:`clawbench.paths`.

We resist the urge to mock :mod:`platformdirs` — it's a tiny, well-tested
library and real path resolution is what we care about. Instead we use
``XDG_CONFIG_HOME`` to steer the config dir at the OS level (platformdirs
respects it on Linux) and fall back to monkeypatching ``PlatformDirs``
for the macOS case where XDG is ignored.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from clawbench import paths


def test_bundled_data_dir_resolves_to_real_path():
    d = paths.bundled_data_dir()
    assert d.exists(), f"bundled data dir missing: {d}"
    # Downstream code feeds this into docker build and --load-extension,
    # so it must be a genuine filesystem path, not a Traversable stub.
    assert isinstance(d, Path)


def test_test_cases_dir_has_cases():
    base = paths.test_cases_dir()
    assert base.exists()
    # Regression: we shipped 153 live cases — if the number collapses,
    # the symlink/force-include got broken during packaging.
    assert sum(1 for _ in base.glob("*/task.json")) >= 150


def test_default_output_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWBENCH_OUTPUT_DIR", str(tmp_path / "custom-out"))
    assert paths.default_output_dir() == (tmp_path / "custom-out").resolve()


def test_default_output_dir_cwd_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWBENCH_OUTPUT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    assert paths.default_output_dir() == tmp_path / "claw-output"


@pytest.mark.skipif(sys.platform == "darwin",
                    reason="macOS platformdirs ignores XDG_CONFIG_HOME")
def test_user_config_dir_respects_xdg(monkeypatch, tmp_path):
    # platformdirs caches the dirs object at import time, so we reload
    # the module with the env var in place.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    import importlib
    from clawbench import paths as _p
    importlib.reload(_p)
    try:
        d = _p.user_config_dir()
        assert str(tmp_path) in str(d), d
    finally:
        # Reload without override so later tests see the real dir again.
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        importlib.reload(_p)


def test_user_models_yaml_seeds_on_first_access(monkeypatch, tmp_path):
    # Redirect the config dir by monkey-patching the module-level helper
    # rather than fighting platformdirs.
    fake_dir = tmp_path / "cfg"
    fake_dir.mkdir()
    monkeypatch.setattr(paths, "user_config_dir", lambda: fake_dir)
    dst = paths.user_models_yaml()
    assert dst == fake_dir / "models.yaml"
    assert dst.exists()
    # The file is either the seeded template or the stub; both must be
    # non-empty so the TUI editor has something to open.
    assert dst.read_text().strip()
