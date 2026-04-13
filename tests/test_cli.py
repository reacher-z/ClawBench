"""Smoke tests for the click CLI surface.

We use click's ``CliRunner`` so we don't spawn subprocesses. These are
intentionally shallow — they verify that the command tree is correctly
wired and exits cleanly, not that the underlying run/batch logic is
correct. The latter belongs in integration tests with a real engine.
"""

from __future__ import annotations

from click.testing import CliRunner

from clawbench import __version__
from clawbench.cli import main


def test_help_lists_all_subcommands():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    out = result.output
    for cmd in ("tui", "run", "batch", "build", "cases", "models",
                "configure", "doctor", "version"):
        assert cmd in out, f"{cmd!r} missing from --help"


def test_version_flag_matches_package():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_subcommand_matches_package():
    result = CliRunner().invoke(main, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_cases_subcommand_lists_bundled_cases():
    result = CliRunner().invoke(main, ["cases"])
    assert result.exit_code == 0
    assert "case(s)" in result.output


def test_configure_show_prints_paths():
    result = CliRunner().invoke(main, ["configure", "--show"])
    assert result.exit_code == 0
    assert "models.yaml" in result.output
    assert "config.json" in result.output
    assert "secrets.env" in result.output
