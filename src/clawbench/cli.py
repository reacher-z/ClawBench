"""``clawbench`` command-line entry point (click-based).

Design notes:

- Bare ``clawbench`` launches the TUI. This preserves muscle memory from
  the old ``./run.sh`` and keeps the zero-friction experience for users
  who just typed ``uv tool install clawbench-eval`` and hit enter.
- Every power-user action has an explicit subcommand so scripts don't
  need to navigate a menu (``run``, ``batch``, ``build``, ``cases``,
  ``models``, ``configure``, ``doctor``, ``version``).
- Subcommands are thin wrappers that delegate to the module-level
  ``main()`` functions in :mod:`clawbench.run` / :mod:`clawbench.batch`.
  Those modules still accept argparse argv so they can be invoked
  in-process *and* via ``python -m clawbench run ...`` from the batch
  runner's subprocess fan-out — one code path, two callers.

Subcommand surface intentionally kept small. Every flag the TUI exposes
is reachable from the CLI, but we don't duplicate every internal toggle
that ``run.py``/``batch.py`` support as argparse args — click just
forwards through to them via ``extra_args``.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import click

from clawbench import __version__
from clawbench import doctor as _doctor
from clawbench import paths as _paths
from clawbench.run import DEFAULT_SECRETS


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _echo_result(r: _doctor.CheckResult) -> None:
    """Render a single doctor CheckResult with color-coded status."""
    symbol = {"ok": "[OK]  ", "warn": "[WARN]", "fail": "[FAIL]"}.get(r.status, "[?]")
    color = {"ok": "green", "warn": "yellow", "fail": "red"}.get(r.status, "white")
    click.echo(f"  {click.style(symbol, fg=color)}  {r.name}: {r.detail}")
    if r.hint and r.status != "ok":
        for line in r.hint.splitlines():
            click.echo(f"        {click.style(line, dim=True)}")


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, "-V", "--version", prog_name="clawbench")
@click.pass_context
def main(ctx: click.Context) -> None:
    """ClawBench — benchmark AI agents on 153 everyday web tasks.

    Run without a subcommand to launch the interactive TUI. Use
    ``clawbench run``, ``batch``, ``build``, ``doctor``, etc. for
    scripting.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand → TUI.
        from clawbench import tui
        tui.main()


# ---------------------------------------------------------------------------
# tui
# ---------------------------------------------------------------------------

@main.command("tui")
def tui_cmd() -> None:
    """Launch the interactive TUI (default action if no subcommand given)."""
    from clawbench import tui
    tui.main()


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

@main.command(
    "run",
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "help_option_names": ["-h", "--help"],
    },
)
@click.argument("test_case_dir", type=click.Path(path_type=Path))
@click.argument("model", required=False)
@click.option("--human", is_flag=True, help="Human mode: expose Chrome via noVNC instead of running an agent.")
@click.option("--output-dir", type=click.Path(path_type=Path), default=None,
              help="Directory to write output to (default: ./claw-output).")
@click.option("--no-build", is_flag=True, help="Skip building the container image.")
@click.option("--no-upload", is_flag=True, help="Skip HuggingFace upload even if configured.")
@click.option("--harness", type=click.Choice(["openclaw", "opencode"]), default=None,
              help="Coding-agent harness (default: openclaw).")
@click.pass_context
def run_cmd(
    ctx: click.Context,
    test_case_dir: Path,
    model: str | None,
    human: bool,
    output_dir: Path | None,
    no_build: bool,
    no_upload: bool,
    harness: str | None,
) -> None:
    """Run a single test case against a model (or in --human mode)."""
    from clawbench import run as _run
    # Accept three forms for the case argument:
    #   (a) an absolute / already-existing path (user points at their own case),
    #   (b) ``test-cases/<name>`` relative to the project (dev convenience),
    #   (c) a bare case name like ``006-daily-life-food-uber-eats`` — looked up
    #       inside the wheel's bundled test-cases. This is the common case from
    #       the TUI, which passes only the case name.
    resolved = test_case_dir
    if not resolved.exists():
        bundled = _paths.test_cases_dir() / test_case_dir.name
        if bundled.exists():
            resolved = bundled
    argv: list[str] = [str(resolved)]
    if model:
        argv.append(model)
    if human:
        argv.append("--human")
    if output_dir:
        argv += ["--output-dir", str(output_dir)]
    if no_build:
        argv.append("--no-build")
    if no_upload:
        argv.append("--no-upload")
    if harness:
        argv += ["--harness", harness]
    argv += list(ctx.args)
    _run.main(argv)


# ---------------------------------------------------------------------------
# batch
# ---------------------------------------------------------------------------

@main.command(
    "batch",
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "help_option_names": ["-h", "--help"],
    },
)
@click.option("--models", "models_", multiple=True, help="Glob(s) matching model keys in models.yaml.")
@click.option("--all-models", is_flag=True, help="Run every model in models.yaml.")
@click.option("--cases", "cases_", multiple=True, help="Glob(s) matching test-case dirs.")
@click.option("--all-cases", is_flag=True, help="Run every bundled test case.")
@click.option("--case-range", default=None, help="Numeric ID range, e.g. 1-50.")
@click.option("--max-concurrent", type=int, default=2, help="Max parallel jobs (default: 2).")
@click.option("--output-dir", type=click.Path(path_type=Path), default=None,
              help="Base output directory (default: ./claw-output).")
@click.option("--stagger-delay", type=float, default=15,
              help="Min seconds between container starts (default: 15).")
@click.option("--dry-run", is_flag=True, help="Print job matrix without running.")
@click.option("--no-upload", is_flag=True, help="Skip HuggingFace upload for all runs.")
@click.option("--harness", type=click.Choice(["openclaw", "opencode"]), default=None,
              help="Coding-agent harness (default: openclaw).")
@click.pass_context
def batch_cmd(
    ctx: click.Context,
    models_: tuple[str, ...],
    all_models: bool,
    cases_: tuple[str, ...],
    all_cases: bool,
    case_range: str | None,
    max_concurrent: int,
    output_dir: Path | None,
    stagger_delay: float,
    dry_run: bool,
    no_upload: bool,
    harness: str | None,
) -> None:
    """Run a model x case cross-product concurrently."""
    from clawbench import batch as _batch
    argv: list[str] = []
    if models_:
        argv += ["--models", *models_]
    if all_models:
        argv.append("--all-models")
    if cases_:
        argv += ["--cases", *cases_]
    if all_cases:
        argv.append("--all-cases")
    if case_range:
        argv += ["--case-range", case_range]
    argv += ["--max-concurrent", str(max_concurrent)]
    if output_dir:
        argv += ["--output-dir", str(output_dir)]
    argv += ["--stagger-delay", str(stagger_delay)]
    if dry_run:
        argv.append("--dry-run")
    if no_upload:
        argv.append("--no-upload")
    if harness:
        argv += ["--harness", harness]
    argv += list(ctx.args)
    _batch.main(argv)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

@main.command("build")
@click.option("--no-cache", is_flag=True, help="Ignore layer cache — full rebuild.")
@click.option("--harness", type=click.Choice(["openclaw", "opencode"]),
              default="openclaw",
              help="Coding-agent harness layer to build (default: openclaw).")
def build_cmd(no_cache: bool, harness: str) -> None:
    """Build the base + harness container images from the bundled Dockerfiles."""
    from clawbench import run as _run
    # ``run.docker_build`` already retries with --no-cache on stale-cache
    # detection; if the user explicitly asks for a cold build, we blow the
    # cache up front by removing the existing images and then rebuilding.
    if no_cache:
        from clawbench.engine import detect_engine
        eng = detect_engine()
        if eng:
            for tag in (_run.BASE_IMAGE, _run.harness_image(harness)):
                subprocess.run([eng, "image", "rm", "-f", tag],
                               capture_output=True)
    _run.docker_build(harness)


# ---------------------------------------------------------------------------
# cases
# ---------------------------------------------------------------------------

@main.command("cases")
@click.option("--category", default=None, help="Filter by category (substring match).")
def cases_cmd(category: str | None) -> None:
    """List bundled test cases (name, category, time-limit)."""
    import json as _json
    base = _paths.test_cases_dir()
    dirs = sorted(p.parent for p in base.glob("*/task.json"))
    if not dirs:
        click.echo("No test cases found.")
        sys.exit(1)
    # One outlier case has a 180+ char name; cap padding at 60 so the
    # common case doesn't get a wall of whitespace.
    width = min(60, max(len(d.name) for d in dirs))
    shown = 0
    for d in dirs:
        try:
            task = _json.loads((d / "task.json").read_text())
        except Exception as e:
            click.echo(f"  {d.name:<{width}}  [unreadable: {e}]")
            continue
        cat = task.get("category", "?")
        if category and category.lower() not in cat.lower():
            continue
        time_limit = task.get("time_limit", "?")
        click.echo(f"  {d.name:<{width}}  {cat:<20}  {time_limit} min")
        shown += 1
    click.echo(f"\n{shown} case(s)")


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------

@main.command("models")
def models_cmd() -> None:
    """List configured models from the user's models.yaml."""
    import yaml as _yaml
    path = _paths.user_models_yaml()
    try:
        data = _yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        click.echo(f"ERROR: cannot read {path}: {e}", err=True)
        sys.exit(1)
    if not data:
        click.echo(f"No models configured. Edit {path} or run `clawbench configure`.")
        return
    click.echo(f"Models configured in {path}:")
    for name in sorted(data):
        api = data[name].get("api_type") if isinstance(data[name], dict) else "?"
        click.echo(f"  {name}  ({api})")


# ---------------------------------------------------------------------------
# configure
# ---------------------------------------------------------------------------

@main.command("configure")
@click.option("--show", is_flag=True, help="Print the config file path and exit.")
@click.option("--secrets", is_flag=True, help="Write a secrets.env file (chmod 600) interactively.")
def configure_cmd(show: bool, secrets: bool) -> None:
    """Open the user's models.yaml in $EDITOR, or manage secrets."""
    if show and secrets:
        click.echo("ERROR: pass --show OR --secrets, not both", err=True)
        sys.exit(1)
    if show:
        click.echo(f"models.yaml: {_paths.user_models_yaml()}")
        click.echo(f"config.json: {_paths.user_config_json()}")
        click.echo(f"secrets.env: {_paths.user_secrets_path()}")
        return
    if secrets:
        _write_secrets_interactive()
        return
    # Default: $EDITOR on models.yaml (seeds it first if missing).
    path = _paths.user_models_yaml()
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
    click.echo(f"Opening {path} with {editor}...")
    try:
        subprocess.run([editor, str(path)], check=False)
    except FileNotFoundError:
        click.echo(f"ERROR: editor '{editor}' not found. Set $EDITOR.", err=True)
        sys.exit(1)


def _write_secrets_interactive() -> None:
    """Prompt for PurelyMail + optional HF keys and persist to secrets.env.

    We chmod 600 and parent-dir mkdir exists_ok=True via
    :func:`_paths.user_config_dir`. Values blanked out are omitted so we
    never overwrite a previously-persisted key with "".
    """
    target = _paths.user_secrets_path()
    existing: dict[str, str] = {}
    if target.exists():
        for line in target.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            existing[k.strip()] = v.strip().strip('"').strip("'")
    click.echo(f"Writing to {target}")
    click.echo("Leave blank to keep the current value (or skip if unset).\n")

    keys = [
        ("PURELY_MAIL_API_KEY", "PurelyMail API key"),
        ("PURELY_MAIL_DOMAIN", "PurelyMail domain"),
        ("HF_TOKEN", "HuggingFace token (optional)"),
        ("HF_REPO_ID", "HuggingFace dataset repo id (optional)"),
    ]
    updated: dict[str, str] = dict(existing)
    for key, label in keys:
        cur = existing.get(key, "")
        default = DEFAULT_SECRETS.get(key, "")
        # Existing values are redacted (user has already committed to them
        # and might share the terminal); shipped defaults are shown in
        # full so a new user can see exactly what they're accepting.
        if cur:
            hint = f" [current: {_redact(cur)}]"
        elif default:
            hint = f" [default: {default}]"
        else:
            hint = ""
        val = click.prompt(f"  {label}{hint}", default="", show_default=False).strip()
        if val:
            updated[key] = val
        elif not cur and default:
            # User just hit enter on a shipped default — persist it so
            # secrets.env is self-documenting and the value survives
            # future default-rotations.
            updated[key] = default

    lines = ["# clawbench secrets — chmod 600", ""]
    lines += [f'{k}="{v}"' for k, v in updated.items()]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        target.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # windows / non-posix — best effort
    click.echo(f"\nWrote {len(updated)} key(s) to {target}")


def _redact(v: str) -> str:
    if len(v) <= 4:
        return "****"
    return v[:2] + "****" + v[-2:]


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

@main.command("doctor")
def doctor_cmd() -> None:
    """Validate engine, image, test-cases, output perms, and secrets."""
    click.echo("clawbench diagnostics\n")
    results = _doctor.run_all()
    for r in results:
        _echo_result(r)
    click.echo()
    fails = [r for r in results if r.status == "fail"]
    warns = [r for r in results if r.status == "warn"]
    if fails:
        click.echo(click.style(f"{len(fails)} failing check(s). Fix and re-run.", fg="red"))
        sys.exit(1)
    if warns:
        click.echo(click.style(f"{len(warns)} warning(s). ClawBench should still work.", fg="yellow"))
    else:
        click.echo(click.style("All checks passed.", fg="green"))


# ---------------------------------------------------------------------------
# version (explicit subcommand in addition to --version)
# ---------------------------------------------------------------------------

@main.command("version")
def version_cmd() -> None:
    """Print the installed version."""
    click.echo(__version__)


if __name__ == "__main__":
    main()
