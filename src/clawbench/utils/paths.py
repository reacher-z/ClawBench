"""Shared filesystem paths for the source-layout package."""

from pathlib import Path


def _find_project_root() -> Path:
    """Find the ClawBench checkout when running from source or an installed wheel."""
    for base in (Path.cwd(), *Path.cwd().parents):
        if (base / "models").is_dir() and (base / "test-cases").is_dir():
            return base
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _find_project_root()
HARNESS_ROOT = PROJECT_ROOT / "src" / "harnesses"
