"""Container engine detection and diagnostics.

Extracted from ``test-driver/tui.py`` (previously lines 900-990). The probe
order is **podman first, docker second** because:

- Podman is license-free; Docker Desktop requires a paid license in
  commercial/academic settings beyond a certain org size.
- On Linux podman runs rootless with no daemon — better default for a
  research tool.
- Both engines can pull the same OCI image from GHCR, so there is no
  functional reason to prefer docker.

Users can still force an engine via the ``CONTAINER_ENGINE`` env var
(values ``docker`` or ``podman``).
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class EngineStatus:
    """Result of :func:`check_engine`.

    ``engine`` is the resolved binary (``podman`` / ``docker``) or ``None``
    if nothing was found. ``status`` is one of the string codes documented
    on :func:`check_engine`. ``detail`` is free-form diagnostic text safe
    to show the user (typically stderr from a failed probe)."""

    engine: str | None
    status: str
    detail: str = ""

    @property
    def ready(self) -> bool:
        return self.status == "ready"


_VALID_ENGINES = ("podman", "docker")


def detect_engine() -> str | None:
    """Return the preferred engine binary on PATH, or ``None``.

    Priority:
    1. ``CONTAINER_ENGINE`` env var (if set to ``podman`` or ``docker`` and
       that binary is on PATH).
    2. Podman if installed.
    3. Docker if installed.
    """
    env = os.environ.get("CONTAINER_ENGINE", "").strip().lower()
    if env in _VALID_ENGINES and shutil.which(env):
        return env
    for cmd in _VALID_ENGINES:
        if shutil.which(cmd):
            return cmd
    return None


def check_engine() -> EngineStatus:
    """Probe the container engine and classify the result.

    Status codes:

    - ``ready``                  engine installed and daemon/VM responsive.
    - ``not_installed``          neither podman nor docker on PATH.
    - ``podman_no_machine``      podman installed, no VM initialized.
    - ``podman_machine_stopped`` podman VM exists but is not running.
    - ``podman_low_memory``      VM has < 4 GB RAM; agent will OOM.
    - ``docker_not_running``     docker CLI works but daemon unreachable.
    - ``unknown_error``          something else; ``detail`` carries stderr.
    """
    engine = detect_engine()
    if engine is None:
        return EngineStatus(None, "not_installed")

    if engine == "podman":
        return _check_podman()
    return _check_docker()


def _check_podman() -> EngineStatus:
    # On macOS/Windows, podman needs a helper VM. Inspect it before probing
    # the daemon so we can offer a specific remediation.
    if platform.system() in ("Darwin", "Windows"):
        try:
            r = subprocess.run(
                ["podman", "machine", "list", "--format", "json"],
                capture_output=True, text=True, timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return EngineStatus("podman", "unknown_error", str(e))
        if r.returncode != 0:
            return EngineStatus("podman", "unknown_error", r.stderr.strip())
        try:
            machines = json.loads(r.stdout or "[]")
        except json.JSONDecodeError:
            machines = []
        if not machines:
            return EngineStatus("podman", "podman_no_machine")
        if not any(m.get("Running") for m in machines):
            return EngineStatus("podman", "podman_machine_stopped")
        # VM running — fall through and verify the socket.

    try:
        r = subprocess.run(
            ["podman", "ps"], capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return EngineStatus("podman", "unknown_error", str(e))
    if r.returncode != 0:
        err = r.stderr.strip()
        if "unable to connect to Podman socket" in err:
            return EngineStatus("podman", "podman_machine_stopped", err)
        return EngineStatus("podman", "unknown_error", err)

    # VM memory check — ClawBench needs >=4 GB for Chrome + gateway + agent.
    if platform.system() in ("Darwin", "Windows"):
        try:
            mi = subprocess.run(
                ["podman", "machine", "inspect", "--format",
                 "{{.Resources.Memory}}"],
                capture_output=True, text=True, timeout=10,
            )
            mem_mb = int(mi.stdout.strip())
            if mem_mb < 4096:
                return EngineStatus("podman", "podman_low_memory", str(mem_mb))
        except (ValueError, subprocess.TimeoutExpired):
            pass  # non-critical — skip if unreadable

    return EngineStatus("podman", "ready")


def _check_docker() -> EngineStatus:
    try:
        r = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return EngineStatus("docker", "unknown_error", str(e))
    if r.returncode != 0:
        return EngineStatus("docker", "docker_not_running", r.stderr.strip())
    return EngineStatus("docker", "ready")


def remediation_hint(status: EngineStatus) -> str:
    """Return a short human-readable hint for a non-ready status."""
    s = status.status
    if s == "ready":
        return ""
    if s == "not_installed":
        return (
            "Install a container engine. Recommended: podman.\n"
            "  macOS:   brew install podman && podman machine init && podman machine start\n"
            "  Linux:   sudo apt install podman   (or dnf, pacman, etc.)\n"
            "  Fallback: Docker Desktop from https://docker.com"
        )
    if s == "podman_no_machine":
        return "Run `podman machine init` then `podman machine start`."
    if s == "podman_machine_stopped":
        return "Run `podman machine start`."
    if s == "podman_low_memory":
        mem = status.detail or "?"
        return (
            f"Podman VM has only {mem} MB RAM; ClawBench needs >=4 GB.\n"
            "Stop the VM and recreate with more memory:\n"
            "  podman machine stop && podman machine rm\n"
            "  podman machine init --memory=8192 && podman machine start"
        )
    if s == "docker_not_running":
        if platform.system() == "Darwin":
            return "Docker daemon is not running. Try: open -a Docker"
        return "Docker daemon is not running. Start the docker service."
    return status.detail or "Unknown engine error."
