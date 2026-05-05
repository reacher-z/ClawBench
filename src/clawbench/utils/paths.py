"""Shared filesystem paths for source checkouts and installed packages."""

from pathlib import Path
import os
import shutil


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_ROOT = PACKAGE_ROOT / "_bundled"
RUNTIME_ROOT = PACKAGE_ROOT / "runtime"


def _source_root() -> Path | None:
    root = PACKAGE_ROOT.parents[1]
    if (root / "pyproject.toml").is_file() and (root / "test-cases").is_dir():
        return root
    return None


SOURCE_ROOT = _source_root()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _find_workspace_root() -> Path:
    """Find the mutable workspace for .env, models.yaml, and outputs."""
    env_root = Path.cwd()
    if raw := os.environ.get("CLAWBENCH_WORKSPACE"):
        return Path(raw).expanduser().resolve()

    for base in (Path.cwd(), *Path.cwd().parents):
        if (base / ".env").is_file() or (base / "models" / "models.yaml").is_file():
            return base.resolve()

    if SOURCE_ROOT is not None and _is_relative_to(Path.cwd().resolve(), SOURCE_ROOT):
        return SOURCE_ROOT

    return env_root.resolve()


WORKSPACE_ROOT = _find_workspace_root()
ASSET_ROOT = SOURCE_ROOT if SOURCE_ROOT is not None else BUNDLED_ROOT
DOCKER_CONTEXT_ROOT = RUNTIME_ROOT
HARNESS_ROOT = RUNTIME_ROOT / "harnesses"
SHARED_ROOT = RUNTIME_ROOT / "shared"

# Backwards-compatible name for callers that mean "where mutable run files live".
PROJECT_ROOT = WORKSPACE_ROOT


def asset_path(*parts: str) -> Path:
    return ASSET_ROOT.joinpath(*parts)


def workspace_path(*parts: str) -> Path:
    return WORKSPACE_ROOT.joinpath(*parts)


def bundled_path(*parts: str) -> Path:
    return BUNDLED_ROOT.joinpath(*parts)


def ensure_workspace_templates() -> None:
    """Copy safe editable templates into the workspace if bundled/source copies exist."""
    copies = [
        (
            asset_path("models", "models.example.yaml"),
            workspace_path("models", "models.example.yaml"),
        ),
        (
            asset_path("models", "model.schema.json"),
            workspace_path("models", "model.schema.json"),
        ),
    ]
    for src, dst in copies:
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
