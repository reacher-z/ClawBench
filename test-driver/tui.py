"""Interactive TUI for ClawBench — select mode, models, and cases with rich UI."""

import multiprocessing
import os
import sys
from pathlib import Path

import questionary
import yaml
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_YAML = PROJECT_ROOT / "models" / "models.yaml"
CASES_DIR = PROJECT_ROOT / "test-cases"

API_TYPES = [
    "openai-completions",
    "openai-responses",
    "anthropic-messages",
    "google-generative-ai",
]
THINKING_LEVELS = ["off", "minimal", "low", "medium", "high", "xhigh", "adaptive"]

console = Console()

# Questionary style matching a dark-terminal aesthetic
STYLE = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
    ("separator", "fg:#6c6c6c"),
    ("instruction", "fg:#6c6c6c"),
    ("text", "fg:white"),
])


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_models_data() -> dict:
    if not MODELS_YAML.exists():
        return {}
    return yaml.safe_load(MODELS_YAML.read_text()) or {}


def save_models(data: dict) -> None:
    MODELS_YAML.parent.mkdir(parents=True, exist_ok=True)
    MODELS_YAML.write_text(yaml.safe_dump(data, sort_keys=False))


def load_models() -> list[str]:
    return sorted(load_models_data().keys())


def load_cases() -> list[str]:
    cases = sorted(p.parent.name for p in CASES_DIR.glob("*/task.json"))
    if not cases:
        console.print("[red bold]ERROR:[/] No test cases found in test-cases/")
        sys.exit(1)
    return cases


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recommend_concurrent() -> int:
    cpus = multiprocessing.cpu_count()
    try:
        mem_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        mem_gb = mem_bytes / (1024**3)
    except (ValueError, OSError):
        mem_gb = 8
    by_cpu = cpus // 2
    by_ram = int(mem_gb // 2)
    recommended = max(1, min(by_cpu, by_ram))
    console.print(
        f"  System: [cyan]{cpus}[/] CPUs, [cyan]{mem_gb:.0f}[/] GB RAM "
        f"— recommended max: [green bold]{recommended}[/]"
    )
    return recommended


def _case_display(case: str) -> str:
    """Format a case name for display: '886  886-entertainment-hobbies-...'"""
    prefix = case.split("-", 1)[0]
    return f"{prefix:>3}  {case}"


def _parse_range_input(raw: str, cases: list[str]) -> list[str]:
    """Parse comma-separated IDs, ranges (e.g. 1-50), or * into case names."""
    if raw.strip() == "*":
        return list(cases)

    # Build ID map: both '001' and '1' → full case name
    id_map: dict[str, str] = {}
    for c in cases:
        prefix = c.split("-", 1)[0]
        id_map[prefix] = c
        stripped = prefix.lstrip("0") or "0"
        id_map[stripped] = c

    selected: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            for i in range(int(lo), int(hi) + 1):
                key = str(i)
                if key in id_map and id_map[key] not in selected:
                    selected.append(id_map[key])
        else:
            if part in id_map and id_map[part] not in selected:
                selected.append(id_map[part])
    return selected


def run_cmd(cmd: list[str]) -> None:
    console.print()
    console.print(Panel(" ".join(cmd), title="[bold]Command[/]", border_style="green"))
    console.print()
    os.execvp(cmd[0], cmd)


def _confirm_launch(summary: dict) -> bool:
    """Show a summary panel and ask for confirmation."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan")
    table.add_column()
    for key, val in summary.items():
        table.add_row(key, str(val))
    console.print()
    console.print(Panel(table, title="[bold]Launch Summary[/]", border_style="cyan"))
    console.print()
    return questionary.confirm("Launch?", default=True, style=STYLE).ask()


def _show_models_table(data: dict) -> None:
    """Print a rich table of configured models."""
    if not data:
        console.print("  [dim]No models configured yet.[/]\n")
        return
    table = Table(title="Configured Models", border_style="dim")
    table.add_column("Name", style="bold green")
    table.add_column("API Type", style="cyan")
    table.add_column("Base URL")
    table.add_column("Thinking", style="yellow")
    for name, cfg in sorted(data.items()):
        table.add_row(
            name,
            cfg.get("api_type", "—"),
            cfg.get("base_url", "—"),
            cfg.get("thinking_level", "—"),
        )
    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Mode: Single run
# ---------------------------------------------------------------------------

def mode_single(models: list[str], cases: list[str]) -> None:
    console.print("\n[bold cyan]--- Select Model ---[/]\n")
    model = questionary.select(
        "Model:",
        choices=models,
        style=STYLE,
    ).ask()
    if model is None:
        return

    console.print("\n[bold cyan]--- Select Test Case ---[/]\n")
    case = questionary.autocomplete(
        "Case (type to filter):",
        choices=cases,
        style=STYLE,
        validate=lambda x: x in cases or "Select a valid case",
    ).ask()
    if case is None:
        return

    ok = _confirm_launch({"Mode": "Single run", "Model": model, "Case": case})
    if not ok:
        return

    run_cmd([
        "uv", "run", "--project", "test-driver",
        "test-driver/run.py", f"test-cases/{case}", model,
    ])


# ---------------------------------------------------------------------------
# Mode: Batch run
# ---------------------------------------------------------------------------

def mode_batch(models: list[str], cases: list[str]) -> None:
    console.print("\n[bold cyan]--- Select Models ---[/]\n")
    selected_models = questionary.checkbox(
        "Models (space to select, enter to confirm):",
        choices=models,
        style=STYLE,
        validate=lambda x: len(x) > 0 or "Select at least one model",
    ).ask()
    if not selected_models:
        return

    console.print("\n[bold cyan]--- Case Selection ---[/]\n")
    case_mode = questionary.select(
        "How to select cases?",
        choices=[
            questionary.Choice("All cases", value="all"),
            questionary.Choice("Case range (e.g. 1-50)", value="range"),
            questionary.Choice("Pick specific cases", value="pick"),
        ],
        style=STYLE,
    ).ask()
    if case_mode is None:
        return

    case_args: list[str] = []

    if case_mode == "all":
        case_args = ["--all-cases"]
        case_summary = f"All ({len(cases)})"
    elif case_mode == "range":
        raw = questionary.text(
            "Range (e.g. 1-50, 100-200):",
            style=STYLE,
            validate=lambda x: bool(x.strip()) or "Enter a range",
        ).ask()
        if raw is None:
            return
        # Validate and show what matched
        matched = _parse_range_input(raw, cases)
        if not matched:
            console.print("[red]No cases matched that range.[/]")
            return
        console.print(f"  Matched [green]{len(matched)}[/] cases")
        case_args = ["--case-range", raw.strip()]
        case_summary = f"Range {raw.strip()} ({len(matched)} cases)"
    else:
        # Interactive checkbox with all cases
        selected_cases = questionary.checkbox(
            "Cases (space to select):",
            choices=[questionary.Choice(_case_display(c), value=c) for c in cases],
            style=STYLE,
            validate=lambda x: len(x) > 0 or "Select at least one case",
        ).ask()
        if not selected_cases:
            return
        case_args = ["--cases"] + [f"test-cases/{c}" for c in selected_cases]
        case_summary = f"{len(selected_cases)} selected"

    recommended = _recommend_concurrent()
    concurrent = questionary.text(
        "Max concurrent jobs:",
        default=str(recommended),
        style=STYLE,
        validate=lambda x: x.isdigit() and int(x) > 0 or "Enter a positive number",
    ).ask()
    if concurrent is None:
        return

    dry = questionary.confirm("Dry run first?", default=False, style=STYLE).ask()
    if dry is None:
        return

    ok = _confirm_launch({
        "Mode": "Batch run",
        "Models": ", ".join(selected_models),
        "Cases": case_summary,
        "Concurrent": concurrent,
        "Dry run": "Yes" if dry else "No",
    })
    if not ok:
        return

    cmd = [
        "uv", "run", "--project", "test-driver",
        "test-driver/batch.py",
        "--models", *selected_models,
        *case_args,
        "--max-concurrent", concurrent,
    ]
    if dry:
        cmd.append("--dry-run")

    run_cmd(cmd)


# ---------------------------------------------------------------------------
# Mode: Human
# ---------------------------------------------------------------------------

def mode_human(cases: list[str]) -> None:
    console.print("\n[bold cyan]--- Select Test Case ---[/]\n")
    case = questionary.autocomplete(
        "Case (type to filter):",
        choices=cases,
        style=STYLE,
        validate=lambda x: x in cases or "Select a valid case",
    ).ask()
    if case is None:
        return

    ok = _confirm_launch({"Mode": "Human mode", "Case": case})
    if not ok:
        return

    run_cmd([
        "uv", "run", "--project", "test-driver",
        "test-driver/run.py", f"test-cases/{case}", "--human",
    ])


# ---------------------------------------------------------------------------
# Mode: Configure models
# ---------------------------------------------------------------------------

def mode_configure() -> None:
    while True:
        data = load_models_data()
        _show_models_table(data)

        actions = ["Add a new model"]
        if data:
            actions.extend(["Edit a model", "Delete a model", "Back to main menu"])
        else:
            actions.append("Back to main menu")

        action = questionary.select(
            "What would you like to do?",
            choices=actions,
            style=STYLE,
        ).ask()
        if action is None or action == "Back to main menu":
            return

        if action == "Add a new model":
            _add_model(data)
        elif action == "Edit a model":
            _edit_model(data)
        elif action == "Delete a model":
            _delete_model(data)


def _add_model(data: dict) -> None:
    name = questionary.text(
        "Model name:",
        style=STYLE,
        validate=lambda x: (
            "Name cannot be empty" if not x.strip()
            else f"'{x}' already exists" if x.strip() in data
            else True
        ),
    ).ask()
    if name is None:
        return
    name = name.strip()

    base_url = questionary.text(
        "Base URL:",
        style=STYLE,
        validate=lambda x: bool(x.strip()) or "URL cannot be empty",
    ).ask()
    if base_url is None:
        return

    api_type = questionary.select(
        "API type:",
        choices=API_TYPES,
        default="openai-completions",
        style=STYLE,
    ).ask()
    if api_type is None:
        return

    api_key = questionary.text(
        "API key:",
        style=STYLE,
        validate=lambda x: bool(x.strip()) or "API key cannot be empty",
    ).ask()
    if api_key is None:
        return

    thinking_level = questionary.select(
        "Thinking level:",
        choices=THINKING_LEVELS,
        default="medium",
        style=STYLE,
    ).ask()
    if thinking_level is None:
        return

    data[name] = {
        "api_key": api_key.strip(),
        "base_url": base_url.strip(),
        "api_type": api_type,
        "thinking_level": thinking_level,
    }
    save_models(data)
    console.print(f"\n  [green bold]Saved[/] {name} to {MODELS_YAML}\n")


def _edit_model(data: dict) -> None:
    name = questionary.select(
        "Which model to edit?",
        choices=sorted(data.keys()),
        style=STYLE,
    ).ask()
    if name is None:
        return

    cfg = data[name]
    console.print(f"\n  Editing [bold]{name}[/] — press Enter to keep current value.\n")

    base_url = questionary.text(
        "Base URL:",
        default=cfg.get("base_url", ""),
        style=STYLE,
    ).ask()
    if base_url is None:
        return

    api_type = questionary.select(
        "API type:",
        choices=API_TYPES,
        default=cfg.get("api_type", "openai-completions"),
        style=STYLE,
    ).ask()
    if api_type is None:
        return

    api_key = questionary.text(
        "API key:",
        default=cfg.get("api_key", ""),
        style=STYLE,
    ).ask()
    if api_key is None:
        return

    thinking_level = questionary.select(
        "Thinking level:",
        choices=THINKING_LEVELS,
        default=cfg.get("thinking_level", "medium"),
        style=STYLE,
    ).ask()
    if thinking_level is None:
        return

    data[name] = {
        "api_key": api_key.strip(),
        "base_url": base_url.strip(),
        "api_type": api_type,
        "thinking_level": thinking_level,
    }
    save_models(data)
    console.print(f"\n  [green bold]Updated[/] {name}\n")


def _delete_model(data: dict) -> None:
    name = questionary.select(
        "Which model to delete?",
        choices=sorted(data.keys()),
        style=STYLE,
    ).ask()
    if name is None:
        return

    confirm = questionary.confirm(
        f"Delete '{name}'?", default=False, style=STYLE
    ).ask()
    if not confirm:
        return

    del data[name]
    save_models(data)
    console.print(f"\n  [red bold]Deleted[/] {name}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.chdir(PROJECT_ROOT)

    models = load_models()
    cases = load_cases()

    # Header
    title = Text("ClawBench", style="bold cyan")
    subtitle = Text(
        f"{len(models)} models configured  |  {len(cases)} test cases available",
        style="dim",
    )
    console.print()
    console.print(Panel(
        Text.assemble(title, "\n", subtitle),
        border_style="cyan",
    ))
    console.print()

    while True:
        mode = questionary.select(
            "Select mode:",
            choices=[
                questionary.Choice("Single run  (one model x one case)", value="single"),
                questionary.Choice("Batch run   (models x cases)", value="batch"),
                questionary.Choice("Human mode  (no agent, noVNC)", value="human"),
                questionary.Choice("Configure models", value="configure"),
                questionary.Choice("Exit", value="exit"),
            ],
            style=STYLE,
        ).ask()

        if mode is None or mode == "exit":
            console.print("\n[dim]Bye.[/]")
            return

        if mode == "configure":
            mode_configure()
            # Reload models after configuration changes
            models = load_models()
            continue

        if not models:
            console.print(
                "\n[red bold]No models configured.[/] "
                "Run [cyan]Configure models[/] first, or copy "
                "[cyan]models/models.example.yaml[/] to [cyan]models/models.yaml[/].\n"
            )
            continue

        if mode == "single":
            mode_single(models, cases)
        elif mode == "batch":
            mode_batch(models, cases)
        elif mode == "human":
            mode_human(cases)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Aborted.[/]")
        sys.exit(0)
