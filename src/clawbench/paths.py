"""Path helpers for the installed package.

Three kinds of locations:

1. **Bundled read-only data** inside the wheel — test cases, chrome extension,
   dockerfile set, personal-info templates. Always accessed via
   :func:`bundled_data_dir` (returns a real ``Path`` so it can be handed to
   subprocess / ``docker build`` without further juggling).

2. **User config** — per-user mutable state. Chosen via :mod:`platformdirs` so
   macOS gets ``~/Library/Application Support/claw-bench`` and Linux gets
   ``~/.config/claw-bench`` (respecting ``XDG_CONFIG_HOME``). Contains
   ``models.yaml``, ``config.json``, optional ``secrets.env``.

3. **Output directory** — where run artifacts land. Defaults to
   ``./claw-output/`` in the caller's current directory, overridable via
   ``--output-dir`` or ``CLAWBENCH_OUTPUT_DIR``.

We also migrate from the pre-package legacy dir ``~/.config/clawbench/`` on
first access so users coming from source installs keep their preferences.
"""

from __future__ import annotations

import os
import shutil
from importlib import resources
from pathlib import Path

from platformdirs import PlatformDirs

_APP_NAME = "claw-bench"
_LEGACY_CONFIG_DIR = Path.home() / ".config" / "clawbench"

_dirs = PlatformDirs(_APP_NAME, appauthor=False)


def bundled_data_dir() -> Path:
    """Return the on-disk path to read-only bundled assets.

    Uses ``importlib.resources.files("clawbench")`` which resolves to a real
    filesystem path when the package is installed normally (wheel or editable).
    We need a real ``Path`` rather than a ``Traversable`` because the
    ``docker build`` context and ``--load-extension`` need a real directory.
    """
    root = resources.files("clawbench") / "data"
    # ``files()`` returns a MultiplexedPath in rare cases (namespace packages);
    # for single-package layouts it yields a PosixPath/WindowsPath directly.
    return Path(str(root))


def test_cases_dir() -> Path:
    return bundled_data_dir() / "test-cases"


def chrome_extension_dir() -> Path:
    return bundled_data_dir() / "chrome-extension"


def extension_server_dir() -> Path:
    return bundled_data_dir() / "extension-server"


def shared_dir() -> Path:
    return bundled_data_dir() / "shared"


def docker_build_dir() -> Path:
    """Directory containing Dockerfiles, entrypoint.sh, and harness scripts."""
    return bundled_data_dir() / "docker"


def bundled_models_yaml() -> Path:
    """Seed template copied into the user config dir on first run.

    We intentionally ship the *example* file, not the developer's live
    ``models.yaml``. The live file in the repo may contain real API keys
    (OpenRouter et al.) committed for local convenience — those must not
    land on PyPI where every wheel is permanently indexed."""
    return bundled_data_dir() / "models" / "models.example.yaml"


def user_config_dir() -> Path:
    """Platform-appropriate per-user config directory (created if missing)."""
    d = Path(_dirs.user_config_dir)
    d.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_config(d)
    return d


def user_models_yaml() -> Path:
    """Path to the user's editable models config. Seeded from the bundled
    template on first access so the file always exists for the TUI editor."""
    dst = user_config_dir() / "models.yaml"
    if not dst.exists():
        src = bundled_models_yaml()
        if src.exists():
            shutil.copyfile(src, dst)
        else:
            dst.write_text("# ClawBench models.yaml\nmodels: {}\n", encoding="utf-8")
    return dst


def user_config_json() -> Path:
    """TUI preferences (theme, last-used options)."""
    return user_config_dir() / "config.json"


def user_secrets_path() -> Path:
    """Optional persisted secrets file (PURELYMAIL_API_KEY etc).

    Not created automatically — the CLI's ``configure --secrets`` writes it
    with chmod 600. ``run`` / ``batch`` load it via python-dotenv if present.
    """
    return user_config_dir() / "secrets.env"


def default_output_dir() -> Path:
    """Default run output directory.

    Order of precedence:
    1. ``CLAWBENCH_OUTPUT_DIR`` environment variable.
    2. ``./claw-output`` in the caller's current working directory.
    """
    env = os.environ.get("CLAWBENCH_OUTPUT_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd() / "claw-output"


def _migrate_legacy_config(new_dir: Path) -> None:
    """One-shot migration from ``~/.config/clawbench/`` to the platformdirs
    location. Copies files that don't already exist at the new location and
    leaves the legacy dir alone so source installs keep working."""
    if not _LEGACY_CONFIG_DIR.is_dir() or new_dir == _LEGACY_CONFIG_DIR:
        return
    for name in ("tui.json", "config.json", "models.yaml"):
        src = _LEGACY_CONFIG_DIR / name
        if not src.exists():
            continue
        # Normalize legacy tui.json filename to config.json going forward.
        dst_name = "config.json" if name == "tui.json" else name
        dst = new_dir / dst_name
        if dst.exists():
            continue
        try:
            shutil.copyfile(src, dst)
        except OSError:
            # Migration is best-effort; the CLI still works without it.
            pass
