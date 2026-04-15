"""Container image lifecycle helpers.

The single responsibility here is answering the question: *is the
``clawbench`` image available locally and is it the right version?* —
pulling from the registry when it isn't, and falling back to a local
build when pull fails (offline, rate-limited, arch mismatch).

Why pull-first, build-fallback:

- A first-time ``docker build`` takes 5-10 minutes on a fresh system.
  For users who just typed ``uv tool install clawbench-eval``, that is an awful
  first impression. A prebuilt image on GHCR is an order of magnitude
  faster and already exists on the release pipeline.
- But pulls can fail in ways builds cannot (behind an enterprise proxy,
  no GHCR auth, unsupported arch). Silently falling back to build keeps
  the package usable in those environments instead of hard-erroring.

Version-label check:

- The release CI tags images with ``LABEL org.clawbench.version=<v>``
  matching the pypi version. We warn loudly (but keep going) if the
  local image's label diverges from ``clawbench.__version__`` — the
  single most common post-release footgun is "works locally because I
  have a stale hand-built image that nobody else has."
"""

from __future__ import annotations

import subprocess

from clawbench import __version__
from clawbench.engine import detect_engine

IMAGE_NAME = "clawbench"
REGISTRY_REF = "ghcr.io/reacher-z/claw-bench"
VERSION_LABEL = "org.clawbench.version"


def _engine_or_fail() -> str:
    eng = detect_engine()
    if eng is None:
        raise RuntimeError(
            "No container engine (podman or docker) found on PATH. "
            "Install podman: https://podman.io/docs/installation"
        )
    return eng


def image_exists(engine: str | None = None, ref: str = IMAGE_NAME) -> bool:
    """Return True if ``ref`` is present in the local image store."""
    eng = engine or _engine_or_fail()
    return subprocess.run(
        [eng, "image", "inspect", ref],
        capture_output=True,
    ).returncode == 0


def image_label(engine: str | None = None, ref: str = IMAGE_NAME) -> str | None:
    """Return the ``org.clawbench.version`` label from the local image,
    or ``None`` if the image isn't present or has no label."""
    eng = engine or _engine_or_fail()
    r = subprocess.run(
        [eng, "image", "inspect", "--format",
         "{{ index .Config.Labels \"" + VERSION_LABEL + "\" }}", ref],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None
    label = r.stdout.strip()
    return label or None


def pull_image(
    engine: str | None = None,
    tag: str | None = None,
) -> tuple[bool, str]:
    """Attempt to pull ``ghcr.io/reacher-z/claw-bench:<tag>`` and retag it
    locally as ``clawbench`` so the rest of the code keeps working.

    Returns ``(success, detail)``. ``detail`` is a diagnostic string with
    the pull command's stderr on failure, empty on success.

    ``tag`` defaults to the installed package version; callers that want
    ``:latest`` explicitly can pass it.
    """
    eng = engine or _engine_or_fail()
    use_tag = tag or __version__
    ref = f"{REGISTRY_REF}:{use_tag}"
    r = subprocess.run(
        [eng, "pull", ref],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return False, r.stderr.strip() or r.stdout.strip()
    # Retag so the existing run.py / tui.py code paths that say
    # ``clawbench`` (un-prefixed) keep working.
    tag_r = subprocess.run(
        [eng, "tag", ref, IMAGE_NAME],
        capture_output=True, text=True,
    )
    if tag_r.returncode != 0:
        return False, tag_r.stderr.strip()
    return True, ""


def verify_image_version(engine: str | None = None) -> tuple[bool, str]:
    """Check whether the local image's version label matches the installed
    wheel's version. Returns ``(matches, detail)``:

    - ``(True, "")``   when the label equals ``__version__`` (or when the
      image has no label at all — we treat unlabeled legacy images as OK
      since they predate this scheme and warning on them would be noisy
      for existing users).
    - ``(False, msg)`` when labels mismatch; ``msg`` is user-facing.
    """
    eng = engine or _engine_or_fail()
    if not image_exists(eng):
        return False, f"image '{IMAGE_NAME}' not present locally"
    label = image_label(eng)
    if label is None:
        return True, ""  # legacy image, no label — accept
    if label == __version__:
        return True, ""
    return False, (
        f"image version label '{label}' != package version '{__version__}'. "
        f"Consider `clawbench build --no-cache` to rebuild."
    )
