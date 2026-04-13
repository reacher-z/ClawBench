"""``claw-bench doctor`` — diagnostic checks for a ClawBench install.

Every check is a callable that returns a :class:`CheckResult`. The CLI
layer is responsible for rendering; this module just reports facts.

Split out from the TUI's inline engine probe so we can run the same
checks from CI, from ``claw-bench doctor``, and from inside the TUI
"fix this for me" flow without duplicating code.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from clawbench import __version__
from clawbench import engine as _engine
from clawbench import image as _image
from clawbench import paths as _paths


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str   # "ok" | "warn" | "fail"
    detail: str = ""
    hint: str = ""


def check_version() -> CheckResult:
    return CheckResult("clawbench version", "ok", __version__)


def check_engine() -> CheckResult:
    s = _engine.check_engine()
    if s.ready:
        return CheckResult("container engine", "ok", f"{s.engine} ready")
    level = "fail"
    # ``podman_low_memory`` is a warning — the user can still run, just
    # with reduced reliability on heavier cases.
    if s.status == "podman_low_memory":
        level = "warn"
    return CheckResult(
        "container engine",
        level,
        f"{s.engine or 'none'} / {s.status}",
        _engine.remediation_hint(s),
    )


def check_image() -> CheckResult:
    eng = _engine.detect_engine()
    if eng is None:
        return CheckResult(
            "container image",
            "fail",
            "no container engine — skipped",
        )
    if not _image.image_exists(eng):
        return CheckResult(
            "container image",
            "warn",
            f"'{_image.IMAGE_NAME}' not present",
            "Run `claw-bench build` (or let `claw-bench run` pull on first use).",
        )
    ok, msg = _image.verify_image_version(eng)
    if ok:
        label = _image.image_label(eng) or "unlabeled (legacy)"
        return CheckResult("container image", "ok", label)
    return CheckResult("container image", "warn", msg)


def check_test_cases() -> CheckResult:
    base = _paths.test_cases_dir()
    if not base.exists():
        return CheckResult(
            "bundled test-cases",
            "fail",
            f"not found at {base}",
            "Reinstall the package — data directory is missing from the wheel.",
        )
    count = sum(1 for _ in base.glob("*/task.json"))
    if count == 0:
        return CheckResult("bundled test-cases", "fail", "0 cases found")
    return CheckResult("bundled test-cases", "ok", f"{count} cases available")


def check_models_yaml() -> CheckResult:
    dst = _paths.user_models_yaml()
    if not dst.exists():
        return CheckResult(
            "models.yaml",
            "warn",
            "not yet created",
            "Run `claw-bench configure` to seed from the bundled template.",
        )
    try:
        import yaml
        data = yaml.safe_load(dst.read_text()) or {}
    except Exception as e:
        return CheckResult("models.yaml", "fail", f"parse error: {e}")
    count = len(data) if isinstance(data, dict) else 0
    if count == 0:
        return CheckResult(
            "models.yaml",
            "warn",
            f"{dst} is empty — no models configured",
            "Edit the file (`claw-bench configure`) and add at least one model.",
        )
    return CheckResult("models.yaml", "ok", f"{count} model(s) configured")


def check_output_dir() -> CheckResult:
    out = _paths.default_output_dir()
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return CheckResult("output directory", "fail", str(e))
    if not os.access(out, os.W_OK):
        return CheckResult(
            "output directory",
            "fail",
            f"{out} not writable",
        )
    return CheckResult("output directory", "ok", str(out))


def check_secrets() -> CheckResult:
    """Soft check — PurelyMail key is required for email-dependent cases
    but the wheel ships a working default, so a fresh install already has
    one. Report which source the key will resolve from at runtime."""
    # Mirror the precedence in ``run._load_runtime_env`` so doctor doesn't
    # lie about reality.
    from clawbench.run import DEFAULT_SECRETS

    if os.environ.get("PURELY_MAIL_API_KEY"):
        source = "env"
    elif _env_file_has_key(Path.cwd() / ".env", "PURELY_MAIL_API_KEY"):
        source = "./.env"
    elif _env_file_has_key(_paths.user_secrets_path(), "PURELY_MAIL_API_KEY"):
        source = str(_paths.user_secrets_path())
    elif DEFAULT_SECRETS.get("PURELY_MAIL_API_KEY"):
        source = "wheel default"
    else:
        return CheckResult(
            "PurelyMail API key",
            "warn",
            "not configured",
            "Email-requiring cases will fail. Set PURELY_MAIL_API_KEY or run "
            "`clawbench configure --secrets`.",
        )
    return CheckResult("PurelyMail API key", "ok", f"found in {source}")


def _env_file_has_key(path: Path, key: str) -> bool:
    """``True`` iff ``path`` is a readable ``KEY=VALUE`` file that
    actually defines ``key`` (rather than just existing)."""
    if not path.is_file():
        return False
    try:
        for line in path.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            name = s.split("=", 1)[0].strip()
            if name == key:
                return True
    except OSError:
        pass
    return False


ALL_CHECKS = [
    check_version,
    check_engine,
    check_image,
    check_test_cases,
    check_models_yaml,
    check_output_dir,
    check_secrets,
]


def run_all() -> list[CheckResult]:
    """Run every check in order and return results. Never raises."""
    results: list[CheckResult] = []
    for fn in ALL_CHECKS:
        try:
            results.append(fn())
        except Exception as e:  # pragma: no cover — defensive
            results.append(CheckResult(fn.__name__, "fail", f"unexpected: {e}"))
    return results
