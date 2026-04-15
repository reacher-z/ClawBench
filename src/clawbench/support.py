"""User-facing 'support us' prompts shared across run / batch / tui.

A benchmark repo lives or dies by community reach. The cost of a one-line
star prompt at end-of-run is trivial; the star rate from a user who just
saw their run succeed is the highest we'll ever get.
"""

from __future__ import annotations

import os
import sys

_STAR_URL = "https://github.com/reacher-z/ClawBench"


def star_prompt_enabled() -> bool:
    """Honor ``NO_COLOR``-style opt-out for non-interactive or CI use."""
    if os.environ.get("CLAWBENCH_NO_STAR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def print_star_prompt() -> None:
    """Plain-stdout variant — used from run.py / batch.py after completion."""
    if not star_prompt_enabled():
        return
    print()
    print(f"  If ClawBench helped, please star us: {_STAR_URL}")


def rich_star_prompt(console) -> None:
    """Rich-console variant — used from the TUI so it themes correctly."""
    if not star_prompt_enabled():
        return
    console.print()
    console.print(
        f"  [dim]If ClawBench helped, please [bold]star us[/]: "
        f"[link={_STAR_URL}]{_STAR_URL}[/][/]"
    )
