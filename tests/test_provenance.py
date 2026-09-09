"""Run provenance: which code, corpus, and agent build produced a trace."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from clawbench.runner.run_support import provenance
from clawbench.utils.paths import ASSET_ROOT


@pytest.fixture(autouse=True)
def _clear_provenance_caches() -> None:
    for fn in (
        provenance.clawbench_version,
        provenance._repo_root,
        provenance.clawbench_commit,
        provenance._corpus_commit,
        provenance.harness_pins,
    ):
        fn.cache_clear()


# ---------------------------------------------------------------------------
# Harness pins
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("harness", "package"),
    [
        ("openclaw", "openclaw"),
        ("opencode", "opencode-ai"),
        ("claude-code", "@anthropic-ai/claude-code"),
        ("browser-use", "browser-use"),
    ],
)
def test_bundled_harnesses_report_their_pinned_agent(
    harness: str, package: str
) -> None:
    pins = provenance.harness_pins(harness)

    assert package in pins, f"{harness} Dockerfile pin not detected: {pins}"
    assert pins[package][0].isdigit()
    assert provenance.harness_meta(harness, None)["agent_version"] == pins[package]


def test_base_image_lines_are_not_mistaken_for_agent_pins() -> None:
    """`FROM node:24-slim` and `COPY --from=...uv:0.11.6` are not agent pins."""
    pins = provenance.harness_pins("opencode")

    assert "node" not in pins
    assert "uv" not in pins
    assert pins["@playwright/mcp"] == "0.0.70"


def test_harness_without_pins_reports_nothing_rather_than_guessing() -> None:
    meta = provenance.harness_meta("null", "sha256:abc")

    assert meta["pinned_versions"] is None
    assert meta["agent_version"] is None
    assert meta["image_id"] == "sha256:abc"


def test_human_and_unknown_harnesses_are_safe() -> None:
    assert provenance.harness_pins("human") == {}
    assert provenance.harness_pins("not-a-harness") == {}


def test_pip_pins_are_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    harness_dir = tmp_path / "demo"
    harness_dir.mkdir()
    (harness_dir / "Dockerfile.demo").write_text(
        "FROM python:3.11-slim\nRUN pip install demo-agent==2.4.1 helper-plugin==0.9\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(provenance, "HARNESS_ROOT", tmp_path)

    pins = provenance.harness_pins("demo")

    assert pins == {"demo-agent": "2.4.1", "helper-plugin": "0.9"}
    assert provenance.harness_meta("demo", None)["agent_version"] == "2.4.1"


# ---------------------------------------------------------------------------
# Corpus revision
# ---------------------------------------------------------------------------


def test_bundled_task_reports_its_suite_and_path() -> None:
    task_dir = ASSET_ROOT / "test-cases" / "v2" / "example-task"

    corpus = provenance.corpus_meta(task_dir)

    assert corpus["suite"] == "v2"
    assert corpus["path"] == "test-cases/v2"


def test_external_cases_dir_claims_no_revision(tmp_path: Path) -> None:
    """An explicit --cases-dir has a history that is not ClawBench's to claim."""
    corpus = provenance.corpus_meta(tmp_path / "my-suite" / "task-1")

    assert corpus["suite"] == "my-suite"
    assert corpus["path"] is None
    assert corpus["revision"] is None


def test_missing_task_dir_is_all_null() -> None:
    assert provenance.corpus_meta(None) == {
        "suite": None,
        "path": None,
        "revision": None,
    }


# ---------------------------------------------------------------------------
# ClawBench revision
# ---------------------------------------------------------------------------


def test_commit_lookup_outside_a_checkout_is_null_not_a_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A PyPI install has no git repository; that must not fail a run."""
    monkeypatch.setattr(provenance, "SOURCE_ROOT", None)
    provenance._repo_root.cache_clear()
    provenance.clawbench_commit.cache_clear()

    assert provenance.clawbench_commit() == {
        "commit": None,
        "branch": None,
        "dirty": None,
    }


def test_missing_git_binary_is_null_not_a_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_git(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", no_git)

    assert provenance._git(Path("."), "rev-parse", "HEAD") is None


def test_dirty_is_null_when_the_lookup_itself_failed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unknown is not the same claim as clean."""
    monkeypatch.setattr(provenance, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(provenance, "_git", lambda *args: None)
    provenance.clawbench_commit.cache_clear()

    assert provenance.clawbench_commit()["dirty"] is None


def test_clean_and_dirty_trees_are_distinguished(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(provenance, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        provenance,
        "_git",
        lambda repo, *args: "" if args[0] == "status" else "abc123",
    )
    provenance.clawbench_commit.cache_clear()
    assert provenance.clawbench_commit()["dirty"] is False

    monkeypatch.setattr(
        provenance,
        "_git",
        lambda repo, *args: " M file" if args[0] == "status" else "abc123",
    )
    provenance.clawbench_commit.cache_clear()
    assert provenance.clawbench_commit()["dirty"] is True


# ---------------------------------------------------------------------------
# The assembled block
# ---------------------------------------------------------------------------


def test_provenance_block_has_a_stable_shape() -> None:
    block = provenance.make_provenance(
        harness="openclaw",
        harness_image_id="sha256:abc",
        task_dir=ASSET_ROOT / "test-cases" / "v2" / "example-task",
    )

    assert set(block) == {
        "clawbench_version",
        "commit",
        "branch",
        "dirty",
        "corpus",
        "harness",
    }
    assert set(block["corpus"]) == {"suite", "path", "revision"}
    assert set(block["harness"]) == {
        "name",
        "image_id",
        "pinned_versions",
        "agent_version",
    }
    assert block["harness"]["name"] == "openclaw"
