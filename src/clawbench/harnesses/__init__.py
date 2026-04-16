"""ClawBench harness plugin surface.

Third-party packages register additional harnesses under the
``clawbench.harnesses`` entry-point group:

    [project.entry-points."clawbench.harnesses"]
    my-harness = "my_package.my_harness:spec"

The exported ``spec`` must be a :class:`HarnessSpec` instance. This module
merges built-in harnesses with any discovered entry points and returns a
``dict[name, HarnessSpec]``. The built-ins always win on name conflict so
a third-party plugin cannot accidentally (or maliciously) shadow
``openclaw`` / ``opencode`` / ``claude-code``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import Sequence


@dataclass(frozen=True)
class HarnessSpec:
    """Metadata for a ClawBench harness.

    ``dockerfile``, ``setup_script`` and ``run_script`` are resolved by the
    runner at build-context-preparation time: built-in harnesses find them
    under ``src/clawbench/data/docker/``; external plugins ship them inside
    their own package and declare absolute paths via ``resolve_build_files``.
    """

    name: str
    dockerfile: str
    setup_script: str
    run_script: str
    runtime: str = "python"
    container_isolation: str = "shared"
    requires_credentials: Sequence[str] | None = None
    description: str = ""
    upstream_url: str = ""
    upstream_license: str = ""
    build_files_key: str | None = field(default=None)

    def build_files(self) -> tuple[str, str, str]:
        """Return the (Dockerfile, setup, run) triple relative to the build
        context. ClawBench's runner copies these into the build context
        alongside ``Dockerfile.base`` and ``entrypoint.sh``."""
        return (self.dockerfile, self.setup_script, self.run_script)


def _builtin_specs() -> dict[str, HarnessSpec]:
    """Return the three harnesses shipped with ClawBench itself."""
    from clawbench.harnesses.openclaw import spec as openclaw_spec
    from clawbench.harnesses.opencode import spec as opencode_spec
    from clawbench.harnesses.claude_code import spec as claude_code_spec

    return {
        openclaw_spec.name: openclaw_spec,
        opencode_spec.name: opencode_spec,
        claude_code_spec.name: claude_code_spec,
    }


def discover_harnesses() -> dict[str, HarnessSpec]:
    """Return every registered harness, keyed by its ``name``.

    Built-in harnesses are loaded unconditionally. External harnesses are
    discovered via ``importlib.metadata.entry_points(group="clawbench.harnesses")``.
    If an external entry point fails to import we log and skip rather than
    crashing the whole CLI — the hard-coded built-ins must always work.
    """
    result = _builtin_specs()

    eps = entry_points(group="clawbench.harnesses")
    for ep in eps:
        try:
            spec = ep.load()
        except Exception:
            # Deliberately swallow: a broken plugin should not brick the CLI.
            continue
        if not isinstance(spec, HarnessSpec):
            continue
        # Built-ins always win.
        result.setdefault(spec.name, spec)
    return result


__all__ = ["HarnessSpec", "discover_harnesses"]
