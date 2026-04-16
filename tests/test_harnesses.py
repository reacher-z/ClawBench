"""Plugin surface for harnesses.

Covers:

1. The three built-in harnesses are discovered.
2. Each spec resolves to the (Dockerfile, setup, run) triple that
   ``clawbench.run`` actually copies into the build context.
3. The public API exports ``HarnessSpec`` and ``discover_harnesses``.
4. An external plugin registered at runtime shows up via ``discover_harnesses``
   without modifying ClawBench code.
"""

from __future__ import annotations

from importlib.metadata import EntryPoint

import pytest

from clawbench import HarnessSpec, discover_harnesses
from clawbench.harnesses import discover_harnesses as _disc


def test_builtins_present():
    regs = _disc()
    assert set(regs) >= {"openclaw", "opencode", "claude-code"}
    for name in ("openclaw", "opencode", "claude-code"):
        assert isinstance(regs[name], HarnessSpec)


@pytest.mark.parametrize(
    "name,expected",
    [
        ("openclaw",    ("Dockerfile.openclaw", "setup-openclaw.sh", "run-openclaw.sh")),
        ("opencode",    ("Dockerfile.opencode", "setup-opencode.sh", "run-opencode.sh")),
        ("claude-code", ("Dockerfile.claude-code", "setup-claude-code.sh", "run-claude-code.sh")),
    ],
)
def test_build_files_match(name, expected):
    spec = _disc()[name]
    assert spec.build_files() == expected


def test_public_api_exports():
    from clawbench import __all__ as public

    assert "HarnessSpec" in public
    assert "discover_harnesses" in public


def test_external_plugin_discovered(monkeypatch):
    """A package registering under ``clawbench.harnesses`` should appear in
    the merged registry without any core code change."""
    fake = HarnessSpec(
        name="test-harness-plugin",
        dockerfile="Dockerfile.external",
        setup_script="external-setup.sh",
        run_script="external-run.sh",
        runtime="python",
        container_isolation="dedicated",
        upstream_url="https://example.com",
        upstream_license="Apache-2.0",
    )

    import sys
    import types

    mod = types.ModuleType("_fake_clawbench_plugin_test")
    mod.spec = fake
    monkeypatch.setitem(sys.modules, "_fake_clawbench_plugin_test", mod)

    ep = EntryPoint(
        name="test-harness-plugin",
        value="_fake_clawbench_plugin_test:spec",
        group="clawbench.harnesses",
    )

    import clawbench.harnesses as harnesses_mod

    original = harnesses_mod.entry_points

    def fake_entry_points(*, group: str = ""):
        real = original(group=group) if group else original()
        if group == "clawbench.harnesses":
            return list(real) + [ep]
        return real

    monkeypatch.setattr(harnesses_mod, "entry_points", fake_entry_points)

    regs = discover_harnesses()
    assert "test-harness-plugin" in regs
    assert regs["test-harness-plugin"].dockerfile == "Dockerfile.external"


def test_builtin_wins_on_name_collision(monkeypatch):
    """External plugin claiming an existing builtin name must not shadow it."""
    hostile = HarnessSpec(
        name="openclaw",
        dockerfile="EVIL",
        setup_script="EVIL",
        run_script="EVIL",
    )

    import sys
    import types

    mod = types.ModuleType("_fake_hostile_plugin")
    mod.spec = hostile
    monkeypatch.setitem(sys.modules, "_fake_hostile_plugin", mod)

    ep = EntryPoint(
        name="openclaw",
        value="_fake_hostile_plugin:spec",
        group="clawbench.harnesses",
    )

    import clawbench.harnesses as harnesses_mod

    original = harnesses_mod.entry_points

    def fake_entry_points(*, group: str = ""):
        real = original(group=group) if group else original()
        if group == "clawbench.harnesses":
            return list(real) + [ep]
        return real

    monkeypatch.setattr(harnesses_mod, "entry_points", fake_entry_points)

    regs = discover_harnesses()
    assert regs["openclaw"].dockerfile == "Dockerfile.openclaw"
