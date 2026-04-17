"""ClawBench single test-case driver."""

import argparse
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

from clawbench import engine as _engine
from clawbench import paths as _paths
from clawbench.generate_resume_pdf import generate_resume_pdf
from clawbench.hf_upload import hf_upload_enabled, upload_run

from clawbench.harnesses import discover_harnesses as _discover_harnesses

# The tuple form is kept for back-compat with callers that imported it
# directly. It now mirrors whatever the plugin surface discovered at
# import time (built-ins + any third-party ``clawbench.harnesses`` entry
# points). Built-in harnesses always come first so ``DEFAULT_HARNESS``
# stays stable.
_BUILTIN_HARNESS_ORDER = ("openclaw", "opencode", "claude-code", "codex")


def _compute_harnesses() -> tuple[str, ...]:
    discovered = list(_discover_harnesses())
    ordered: list[str] = [h for h in _BUILTIN_HARNESS_ORDER if h in discovered]
    for h in discovered:
        if h not in ordered:
            ordered.append(h)
    return tuple(ordered)


HARNESSES = _compute_harnesses()
DEFAULT_HARNESS = "openclaw"
BASE_IMAGE = "clawbench-base"


def harness_image(harness: str) -> str:
    """Return the docker image tag for a given harness name."""
    return f"clawbench-{harness}"


# Kept for backward compat with older callers that imported IMAGE directly.
IMAGE = harness_image(DEFAULT_HARNESS)
console = Console()


def _detect_engine() -> str:
    """Select the container engine, matching the TUI/engine module priority
    (podman-first, env override wins). Exits with an actionable message if
    the env var is malformed or nothing is installed."""
    env_override = os.environ.get("CONTAINER_ENGINE", "").strip().lower()
    if env_override and env_override not in ("docker", "podman"):
        print(f"ERROR: CONTAINER_ENGINE must be 'docker' or 'podman', got '{env_override}'")
        sys.exit(1)
    if env_override and not shutil.which(env_override):
        print(f"ERROR: CONTAINER_ENGINE={env_override} but '{env_override}' not found on PATH")
        sys.exit(1)
    detected = _engine.detect_engine()
    if detected is None:
        print("ERROR: Neither 'podman' nor 'docker' found on PATH")
        print("  Install podman (recommended): brew install podman  |  sudo apt install podman")
        sys.exit(1)
    return detected


ENGINE = _detect_engine()
PURELYMAIL_API = "https://purelymail.com/api/v0"


def load_dotenv(path: Path) -> dict[str, str]:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# PurelyMail credentials we ship as defaults so ``pip install``
# followed by ``clawbench`` works with zero configuration. These are
# the same credentials committed in the repo's ``.env`` (which is
# intentional — the key is shared project infrastructure, not a
# personal secret). Users who want to point ClawBench at their own
# PurelyMail account override via env var, ``./.env``, or
# ``clawbench configure --secrets``.
DEFAULT_SECRETS: dict[str, str] = {
    "PURELY_MAIL_API_KEY": "pm-live-4c2a5524-392b-4117-a722-0aab7a3bf885",
    "PURELY_MAIL_DOMAIN": "clawbench.cc",
}


def _load_runtime_env() -> dict[str, str]:
    """Build the runtime env dict from, in order of precedence:

    1. ``os.environ`` — normal env vars (highest priority).
    2. ``$CWD/.env`` — legacy source-install layout (if present).
    3. ``user_config_dir()/secrets.env`` — persisted secrets from
       ``clawbench configure --secrets``.
    4. :data:`DEFAULT_SECRETS` — wheel-shipped defaults for the
       PurelyMail credentials so a fresh install works immediately.

    Earlier sources win; later sources fill in missing keys only. This lets
    ``PURELY_MAIL_API_KEY=... clawbench run ...`` work without any config
    file, while still picking up a persisted key for users who prefer one.
    """
    merged: dict[str, str] = {}
    cwd_env = load_dotenv(Path.cwd() / ".env")
    user_env = load_dotenv(_paths.user_secrets_path())
    for key in ("PURELY_MAIL_API_KEY", "PURELY_MAIL_DOMAIN", "HF_TOKEN", "HF_REPO_ID"):
        val = (
            os.environ.get(key)
            or cwd_env.get(key)
            or user_env.get(key)
            or DEFAULT_SECRETS.get(key, "")
        )
        if val:
            merged[key] = val
    return merged


MODELS_YAML = _paths.user_models_yaml()


def load_models_yaml() -> dict:
    """Load all model definitions from models/models.yaml."""
    if not MODELS_YAML.exists():
        print(f"ERROR: {MODELS_YAML} not found (copy models.example.yaml and fill in your keys)")
        sys.exit(1)
    return yaml.safe_load(MODELS_YAML.read_text()) or {}


def load_model_config(model: str) -> dict:
    """Load a model config by name from models/models.yaml.

    The YAML key is the model name (passed as MODEL_NAME to the container).
    """
    all_models = load_models_yaml()
    if model not in all_models:
        print(f"ERROR: model '{model}' not found in {MODELS_YAML}")
        print(f"Available models: {', '.join(sorted(all_models))}")
        sys.exit(1)

    # Validate model name characters. Note: '/' and ':' are valid in
    # vendor-prefixed ids like 'anthropic/claude-sonnet-4-6' or
    # 'arcee-ai/trinity-large-preview:free' — they get sanitized to
    # '--' before being used as path components (see `safe_model`
    # below). We only reject characters that could cause real trouble
    # in shell/filesystem paths even after that sanitization.
    bad = [c for c in " \\*?\"<>|" if c in model]
    if bad:
        print(
            f"ERROR: model name '{model}' contains illegal character(s): "
            f"{' '.join(repr(c) for c in bad)}"
        )
        sys.exit(1)

    config = dict(all_models[model])
    config["model"] = model  # the YAML key IS the model name

    # Validate required fields
    required = ["base_url", "api_type"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        for k in missing:
            print(f"ERROR: Required field '{k}' missing for model '{model}'")
        sys.exit(1)

    # Normalize API keys: api_keys list wins, else wrap api_key into list
    if config.get("api_keys"):
        config["api_key"] = config["api_keys"][0]
    elif config.get("api_key"):
        config["api_keys"] = [config["api_key"]]

    if not config.get("api_keys"):
        print(f"ERROR: no api_key or api_keys for model '{model}'")
        sys.exit(1)

    return config


def step(msg: str):
    print(f"\n{'=' * 60}\n[STEP] {msg}\n{'=' * 60}", flush=True)


def run(cmd: list[str], **kwargs):  # type: ignore[no-untyped-def]
    print(f"$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, **kwargs)


# -- PurelyMail --

def purelymail_request(endpoint: str, body: dict, api_key: str) -> dict:
    data = json.dumps(body).encode()
    req = Request(
        f"{PURELYMAIL_API}/{endpoint}",
        data=data,
        headers={"Purelymail-Api-Token": api_key,
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def create_email(api_key: str, domain: str) -> tuple[str, str]:
    local = f"cb{uuid.uuid4().hex[:12]}"
    password = secrets.token_urlsafe(16)
    purelymail_request("createUser", {
        "userName": local,
        "domainName": domain,
        "password": password,
        "enablePasswordReset": False,
        "sendWelcomeEmail": False,
    }, api_key)
    email = f"{local}@{domain}"
    print(f"  Created email: {email}")
    print(f"  Password: {password}")
    return email, password


def delete_email(api_key: str, email: str) -> None:
    try:
        purelymail_request("deleteUser", {"userName": email}, api_key)
        print(f"  Deleted email: {email}")
    except (URLError, Exception) as e:
        print(f"  WARNING: Failed to delete email {email}: {e}")


# -- Personal info --

RESUME_TEMPLATE = Path(__file__).resolve().parent / "resume_template.json"


def _shared_src() -> Path:
    """Return the bundled ``shared/`` directory (personal-info templates)."""
    return _paths.shared_dir()


def prepare_personal_info(shared_src: Path, email: str, password: str,
                          output_dir: Path) -> Path:
    """Create a temp directory with personal info files, email fields updated."""
    tmp = output_dir / ".my-info-tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    # -- personal info JSON --
    pi_src = shared_src / "alex_green_personal_info.json"
    pi_data = json.loads(pi_src.read_text())
    pi_data["contact"]["email"] = email
    pi_data.pop("online_accounts", None)
    (tmp / "alex_green_personal_info.json").write_text(
        json.dumps(pi_data, indent=2))

    # -- email credentials (separate file) --
    creds = {
        "email": email,
        "password": password,
        "login_url": "https://purelymail.com/user/login",
        "provider": "PurelyMail",
    }
    (tmp / "email_credentials.json").write_text(json.dumps(creds, indent=2))

    # -- resume PDF --
    resume_data = json.loads(RESUME_TEMPLATE.read_text())
    resume_data["header"]["email"] = email
    try:
        generate_resume_pdf(resume_data, tmp / "alex_green_resume.pdf")
    except Exception as e:
        print(f"  WARNING: PDF generation failed ({e}), skipping resume PDF")

    return tmp


def copy_extra_info(task: dict, task_dir: Path, personal_info_dir: Path) -> None:
    """Copy extra_info files from the test case into the my-info dir."""
    for info in task.get("extra_info", []):
        if "path" not in info:
            continue
        src = task_dir / info["path"]
        if not src.exists():
            print(f"  WARNING: extra_info path not found: {src}")
            continue
        dest = personal_info_dir / src.name
        shutil.copy2(src, dest)
        print(f"  Copied extra_info: {src.name}")




# -- Prompt --

def build_instruction(task: dict) -> str:
    parts = [task["instruction"]]
    parts.append(
        "\n---\n"
        "You are my personal browser assistant. I am delegating this task to you "
        "because I do not have time to do it myself. You are acting on my behalf "
        "and with my full authorization. Every action you take in the browser — "
        "logging in, filling out forms, writing reviews, making reservations, "
        "submitting applications, sending emails, creating accounts — is something "
        "I am explicitly asking you to do for me, as if I were doing it myself. "
        "These are my own accounts, my own opinions, and my own decisions. "
        "You are simply carrying them out.\n\n"
        "IMPORTANT: You must complete this task entirely through the browser. "
        "Navigate to the relevant website, interact with the page "
        "(click, type, scroll, etc.), and carry out every step in the browser. "
        "Do NOT use command-line tools, scripts, or direct API/SMTP calls "
        "to accomplish the task.\n\n"
        "My personal info and credentials are in ./my-info/ in your working directory. "
        "Key files include:\n"
        "- alex_green_personal_info.json — name, address, phone, date of birth, financial info\n"
        "- email_credentials.json — email address and password for logging in\n"
        "- alex_green_resume.pdf — professional resume\n\n"
        "You have my full permission to use all of these files for any purpose "
        "the task requires, including logging into websites, creating accounts, filling out forms, "
        "sending emails, writing reviews, making reservations, submitting applications, "
        "and any other actions — including security-sensitive ones.\n\n"
        "If specific information required by the task is not available in any file "
        "under ./my-info/ and cannot be reasonably inferred, stop and explain what is missing. "
        "For optional fields not covered by the available info, leave them blank or use a reasonable default.\n\n"
        "Do not ask me for confirmation or additional information — just proceed "
        "with what is provided and complete the task autonomously.\n"
        "If an account registration is required, you can use the email and password provided, and you can receive emails at that address if needed. "
        "---"
    )
    extras = [(Path(info["path"]).name, info["description"])
              for info in task.get("extra_info", [])
              if info.get("path") and info.get("description")]
    if extras:
        parts.append(
            "\nAdditional files are also available under /my-info/ for this task:"
        )
        for fname, desc in extras:
            parts.append(f"- {fname}: {desc}")
    return "\n".join(parts)


# -- Docker --

def _image_exists(ref: str = IMAGE) -> bool:
    return subprocess.run(
        [ENGINE, "image", "inspect", ref],
        capture_output=True,
    ).returncode == 0


def _harness_build_files(harness: str) -> tuple[str, ...]:
    """Resolve a harness' (Dockerfile, setup, run) triple via the plugin
    registry. Falls back to the legacy dict for backward compatibility if a
    name is registered without the new spec fields populated."""
    specs = _discover_harnesses()
    spec = specs.get(harness)
    if spec is None:
        raise ValueError(
            f"Unknown harness {harness!r}; expected one of {sorted(specs)}"
        )
    return spec.build_files()


def _prepare_build_context(ctx: Path, harness: str = DEFAULT_HARNESS) -> None:
    """Populate ``ctx`` with the files the bundled Dockerfiles expect at the
    build-context root: Dockerfile.base + entrypoint.sh + the per-harness
    Dockerfile / setup / run scripts + chrome-extension/ + extension-server/.

    We copy instead of symlinking because docker/podman do not follow
    symlinks that point *outside* the build context — which all of ours do
    when the package is installed (symlinks under ``src/clawbench/data/``
    resolve to the source tree or to the wheel's site-packages layout).
    The copied trees are tiny (a few MB) so the cost is negligible."""
    harness_files = _harness_build_files(harness)
    docker_dir = _paths.docker_build_dir()
    base_files = ("Dockerfile.base", "entrypoint.sh")
    for name in base_files + harness_files:
        shutil.copy2(docker_dir / name, ctx / name)
    shutil.copytree(_paths.extension_server_dir(), ctx / "extension-server",
                    symlinks=False)
    shutil.copytree(_paths.chrome_extension_dir(), ctx / "chrome-extension",
                    symlinks=False)


def _pick_free_port(preferred: int = 6080) -> int:
    """Return ``preferred`` if available on 127.0.0.1, else an OS-assigned
    ephemeral port. Avoids the hard-coded ``-p 6080:6080`` collision when
    something else on the host already owns that port.
    """
    for candidate in (preferred, 0):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", candidate))
                return s.getsockname()[1]
        except OSError:
            continue
    raise RuntimeError("Could not find a free TCP port for noVNC")


_STEP_RE = re.compile(r"^(?:STEP|Step)\s+(\d+)(?:/(\d+))?", re.IGNORECASE)
_BK_STEP_RE = re.compile(r"^#(\d+)\s+\[")


def _run_build(cmd: list[str]) -> tuple[int, str, list[str]]:
    """Execute a build command with a live spinner.

    Returns ``(exit_code, last_line, all_output_lines)``.
    """
    console.print(f"[dim]$ {' '.join(cmd)}[/]")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None

    last_line = ""
    last_step = ""
    output_lines: list[str] = []
    status_msg = "[cyan]Starting build…[/]"
    with Status(status_msg, console=console, spinner="dots") as status:
        for raw in proc.stdout:
            line = raw.rstrip()
            if not line:
                continue
            last_line = line
            output_lines.append(line)

            m = _STEP_RE.match(line)
            if m:
                cur = m.group(1)
                tot = m.group(2) or "?"
                rest = line.split(":", 1)[-1].strip()[:72]
                last_step = f"step {cur}/{tot}"
                status.update(
                    f"[cyan]Building image — {last_step}[/] [dim]{rest}[/]"
                )
                continue

            m = _BK_STEP_RE.match(line)
            if m:
                snippet = line[:100]
                status.update(f"[cyan]Building image[/] [dim]{snippet}[/]")
                continue

            lowered = line.lower()
            if "error" in lowered and "--no-" not in lowered:
                console.print(f"  [yellow]{line[:120]}[/]")
            status.update(
                f"[cyan]Building image[/] "
                f"[dim]{(last_step + ' · ') if last_step else ''}{line[:72]}[/]"
            )

    rc = proc.wait()
    return rc, last_line, output_lines


def _looks_like_stale_cache(output_lines: list[str]) -> bool:
    """Return True if the build failure looks like it was caused by
    stale layer-cache (e.g. old lockfiles, wrong Python version)."""
    blob = "\n".join(output_lines).lower()
    patterns = [
        "no interpreter found for python",
        "no matching distribution found",
        "package not found",
        "could not find a version that satisfies",
    ]
    return any(p in blob for p in patterns)


def _build_one(ctx: Path, dockerfile: str, tag: str) -> None:
    """Run a single ``docker build`` with the shared spinner and stale-cache
    retry. Exits the process on failure."""
    cmd = [ENGINE, "build", "-f", dockerfile, "-t", tag, str(ctx)]
    rc, last_line, output_lines = _run_build(cmd)

    if rc != 0 and _looks_like_stale_cache(output_lines):
        console.print()
        console.print(
            "[yellow]Build failed — looks like a stale layer cache "
            "(e.g. updated lockfiles not picked up).[/]"
        )
        console.print(
            "[yellow]Retrying with [bold]--no-cache[/] "
            "(full rebuild, may take a few minutes)…[/]"
        )
        console.print()
        cmd_nc = [ENGINE, "build", "--no-cache", "-f", dockerfile,
                  "-t", tag, str(ctx)]
        rc, last_line, output_lines = _run_build(cmd_nc)

    if rc != 0:
        console.print(f"[red bold]Build failed[/] (exit {rc}) for [bold]{tag}[/]")
        if last_line:
            console.print(f"  Last output: [dim]{last_line}[/]")
        sys.exit(rc)


def docker_build(harness: str = DEFAULT_HARNESS) -> None:
    """Build the base + harness images with a live progress spinner.

    The first build pulls ~2GB (python base, chromium, ffmpeg, noVNC, Node,
    plus the harness CLI) and takes several minutes; subsequent rebuilds
    are near-instant when the layer cache is warm. We show a banner only
    for the cold path.

    If a build fails with a pattern that suggests stale layer-cache
    (e.g. a lockfile mismatch), we automatically retry once with
    ``--no-cache`` so the user doesn't have to debug it manually.
    """
    if harness not in _HARNESS_BUILD_FILES:
        raise ValueError(
            f"Unknown harness {harness!r}; expected one of {list(_HARNESS_BUILD_FILES)}"
        )
    target_image = harness_image(harness)
    first_build = not _image_exists(target_image)

    if first_build:
        console.print()
        console.print(Panel(
            "[bold]First-time container build.[/]\n"
            f"This downloads ~2 GB (chromium, ffmpeg, noVNC, Node, {harness})\n"
            "and typically takes [bold]5–10 minutes[/] on a decent connection.\n"
            "[dim]Subsequent runs reuse the layer cache and finish in seconds.[/]",
            title=f"[bold]Building {target_image} image[/]",
            border_style="cyan",
        ))

    with tempfile.TemporaryDirectory(prefix="clawbench-build-") as td:
        ctx = Path(td)
        _prepare_build_context(ctx, harness)
        _build_one(ctx, "Dockerfile.base", BASE_IMAGE)
        harness_dockerfile = _HARNESS_BUILD_FILES[harness][0]
        _build_one(ctx, harness_dockerfile, target_image)

    console.print(f"[green]✓[/] Container image ready ({target_image})")


def _fix_data_ownership(data_dir: Path) -> None:
    """On Linux + rootful Docker, files written inside the container are
    owned by root on the host. After ``docker cp``, the caller cannot
    ``rm -rf test-output/`` without sudo. Detect this and chown the tree
    back to the caller's UID/GID via a throwaway container (which has the
    root privileges needed to chown anything on the bind-mounted dir).

    No-op on macOS, on rootless podman, and when the tree is already
    owned by the caller.
    """
    if sys.platform != "linux":
        return
    if ENGINE != "docker":
        return
    if not data_dir.exists():
        return
    try:
        uid = os.getuid()
    except AttributeError:
        return
    try:
        needs_fix = any(
            p.stat().st_uid != uid
            for p in data_dir.rglob("*")
            if not p.is_symlink()
        )
    except OSError:
        needs_fix = True
    if not needs_fix:
        return

    print(f"  Fixing ownership of {data_dir} (rootful Docker -> host UID)")
    subprocess.run(
        [
            ENGINE, "run", "--rm",
            "-v", f"{data_dir.resolve()}:/fix",
            BASE_IMAGE,
            "chown", "-R", f"{uid}:{os.getgid()}", "/fix",
        ],
        check=False,
        capture_output=True,
    )


def _network_flags() -> list[str]:
    """Force slirp4netns on podman to avoid host-network port collisions."""
    if ENGINE == "podman":
        return ["--network=slirp4netns"]
    return []


def _proxy_env_flags() -> list[str]:
    """Forward host proxy env vars into the container.

    Inside the container 127.0.0.1 is its own loopback, not the host.
    Rewrite localhost references to the host gateway so the proxy is reachable.
    Both podman (host.containers.internal) and Docker Desktop
    (host.docker.internal) resolve to the Mac host.
    """
    host_gw = "host.containers.internal" if ENGINE == "podman" else "host.docker.internal"
    flags: list[str] = []
    has_proxy = False
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"):
        val = os.environ.get(var, "")
        if not val:
            continue
        if var not in ("NO_PROXY", "no_proxy"):
            has_proxy = True
        # Rewrite 127.0.0.1 / localhost to host gateway
        val = val.replace("127.0.0.1", host_gw).replace("localhost", host_gw)
        flags += ["-e", f"{var}={val}"]
    # Ensure container-internal traffic bypasses the proxy
    if has_proxy and not os.environ.get("NO_PROXY") and not os.environ.get("no_proxy"):
        flags += ["-e", "NO_PROXY=localhost,127.0.0.1"]
        flags += ["-e", "no_proxy=localhost,127.0.0.1"]
    return flags


def docker_run_human(name: str, instruction: str, schema_path: Path,
                     personal_info_dir: Path,
                     time_limit_s: int = 1800,
                     host_port: int = 6080) -> None:
    # Human mode has no agent harness — base image carries everything
    # needed (Xvfb, Chrome, extension-server, noVNC).
    cmd = [
        ENGINE, "run", "-d", "--name", name,
        *_network_flags(),
        *_proxy_env_flags(),
        "-e", "HUMAN_MODE=1",
        "-e", f"INSTRUCTION={instruction}",
        "-e", f"TIME_LIMIT_S={time_limit_s}",
        "-p", f"{host_port}:6080",
        "-v", f"{schema_path.resolve()}:/eval-schema.json:ro",
        "-v", f"{personal_info_dir.resolve()}:/my-info:ro",
        BASE_IMAGE,
    ]
    run(cmd)


def docker_run(name: str, instruction: str, schema_path: Path,
               personal_info_dir: Path, model_cfg: dict,
               time_limit_s: int = 1800,
               host_port: int | None = None,
               harness: str = DEFAULT_HARNESS) -> None:
    env_flags = [
        ENGINE, "run", "-d", "--name", name,
        *_network_flags(),
        *_proxy_env_flags(),
        "-e", f"MODEL_NAME={model_cfg['model']}",
        "-e", f"BASE_URL={model_cfg['base_url']}",
        "-e", f"API_TYPE={model_cfg['api_type']}",
        "-e", f"API_KEYS={json.dumps(model_cfg.get('api_keys', []))}",
        "-e", f"API_KEY={model_cfg.get('api_key', '')}",
        "-e", f"INSTRUCTION={instruction}",
        "-e", f"TIME_LIMIT_S={time_limit_s}",
        "-v", f"{schema_path.resolve()}:/eval-schema.json:ro",
        "-v", f"{personal_info_dir.resolve()}:/my-info:ro",
    ]
    # Expose noVNC so the user can watch the agent in real-time.
    if host_port is not None:
        env_flags += ["-p", f"{host_port}:6080"]
    # host.docker.internal needs explicit mapping on Linux (not Docker Desktop)
    if "host.docker.internal" in model_cfg["base_url"]:
        env_flags += ["--add-host=host.docker.internal:host-gateway"]
    if model_cfg.get("thinking_level"):
        env_flags += ["-e", f"THINKING_LEVEL={model_cfg['thinking_level']}"]
    if model_cfg.get("temperature") is not None:
        env_flags += ["-e", f"TEMPERATURE={model_cfg['temperature']}"]
    if model_cfg.get("max_tokens") is not None:
        env_flags += ["-e", f"MAX_TOKENS={model_cfg['max_tokens']}"]
    run([*env_flags, harness_image(harness)])


def docker_wait(name: str) -> None:
    """Block until the container exits, showing a live status line."""
    start = time.time()
    # Launch `docker wait` in background so we can poll status
    proc = subprocess.Popen([ENGINE, "wait", name],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    last_actions = 0
    with Status("[dim]starting...[/]", console=console) as status:
        while proc.poll() is None:
            elapsed = int(time.time() - start)
            mins, secs = divmod(elapsed, 60)
            # Query actions count from container
            r = subprocess.run(
                [ENGINE, "exec", name, "wc", "-l", "/data/actions.jsonl"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                try:
                    last_actions = int(r.stdout.strip().split()[0])
                except (ValueError, IndexError):
                    pass
            status.update(
                f"[dim]{mins:02d}:{secs:02d}  •  {last_actions} actions[/]"
            )
            # Poll every 5s
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
    elapsed = int(time.time() - start)
    mins, secs = divmod(elapsed, 60)
    console.print(f"  Container exited ({mins}m{secs:02d}s, {last_actions} actions)")


def docker_copy(name: str, output_dir: Path) -> None:
    run([ENGINE, "cp", f"{name}:/data", str(output_dir / "data")])
    # Remove internal marker file and bulky harness logs
    (output_dir / "data" / ".stop-requested").unlink(missing_ok=True)
    for log_file in (output_dir / "data").glob("*.log"):
        log_file.unlink(missing_ok=True)


def docker_logs(name: str) -> None:
    subprocess.run([ENGINE, "logs", "--tail", "40", name])


def docker_rm(name: str) -> None:
    subprocess.run([ENGINE, "rm", "-f", name], capture_output=True)


# -- Results --

def ensure_interception(output_dir: Path):
    """If the interceptor didn't produce interception.json, create one with the stop reason."""
    stop_reason_file = output_dir / "data" / ".stop-reason"
    reason = stop_reason_file.read_text().strip(
    ) if stop_reason_file.exists() else "unknown"
    stop_reason_file.unlink(missing_ok=True)
    interception_file = output_dir / "data" / "interception.json"
    if interception_file.exists():
        return
    descriptions = {
        "time_limit_exceeded": "Session stopped: time limit exceeded before the interceptor was triggered.",
        "agent_idle": "Session stopped: agent went idle (300s no actions) before triggering the interceptor.",
        "agent_exited": "Session stopped: agent process exited before triggering the interceptor.",
        "vnc_disconnected": "Session stopped: human disconnected from VNC without triggering the interceptor.",
        "chrome_cdp_timeout": "Session stopped: Chrome CDP was not ready after 30s (browser failed to start).",
        "gateway_failed": "Session stopped: OpenClaw gateway died on startup.",
        "opencode_failed": "Session stopped: opencode process died on startup.",
        "claude_code_failed": "Session stopped: Claude Code process died on startup.",
        "codex_failed": "Session stopped: Codex CLI process died on startup.",
        "proxy_failed": "Session stopped: LiteLLM API translation proxy failed to start.",
        "missing_harness": "Session stopped: container image was built without a harness layer.",
    }
    description = descriptions.get(reason, f"Session stopped: {reason}.")
    schema_file = output_dir / "eval-schema.json"
    schema = json.loads(schema_file.read_text()) if schema_file.exists() else None
    result = {
        "intercepted": False,
        "stop_reason": reason,
        "stop_description": description,
        "request": None,
        "schema": schema,
    }
    interception_file.parent.mkdir(parents=True, exist_ok=True)
    interception_file.write_text(json.dumps(result, indent=2))


def print_results(output_dir: Path) -> bool:
    data_dir = output_dir / "data"

    # Actions
    actions_file = data_dir / "actions.jsonl"
    if actions_file.exists():
        actions = [json.loads(
            l) for l in actions_file.read_text().splitlines() if l.strip()]
        print(f"Actions recorded: {len(actions)}")
        for a in actions:
            print(f"  {a['type']:10s}  {a.get('url', '')[:70]}")
    else:
        print("No actions.jsonl found")

    # HTTP Requests
    requests_file = data_dir / "requests.jsonl"
    if requests_file.exists():
        request_lines = [
            l for l in requests_file.read_text().splitlines() if l.strip()]
        print(f"HTTP requests logged: {len(request_lines)}")

    # Interception
    interception_file = data_dir / "interception.json"
    result = json.loads(interception_file.read_text())
    intercepted = result.get("intercepted", False)
    print(f"Intercepted: {intercepted}")
    if result.get("stop_reason"):
        print(f"Stop reason: {result['stop_reason']}")
    if result.get("request"):
        print(f"Request URL: {result['request']['url']}")
        print(f"Request method: {result['request']['method']}")
        if result["request"].get("body"):
            print(f"Body: {json.dumps(result['request']['body'])[:300]}")
    return intercepted


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run a single ClawBench test case")
    parser.add_argument("test_case_dir", type=Path,
                        help="Path to the test case directory")
    parser.add_argument("model", type=str, nargs="?", default=None,
                        help="Model name (key in models/models.yaml, required for agent mode)")
    parser.add_argument("--human", action="store_true",
                        help="Human mode: expose Chrome via noVNC instead of running an agent")
    parser.add_argument("--output-dir", dest="output_dir", type=Path, default=None,
                        help="Directory to write output data to (default: <project>/test-output)")
    parser.add_argument("--no-build", dest="no_build", action="store_true",
                        help="Skip building the container image (assumes it already exists)")
    parser.add_argument("--no-upload", dest="no_upload", action="store_true",
                        help="Skip HuggingFace upload even if HF_TOKEN is configured")
    parser.add_argument("--harness", choices=HARNESSES, default=DEFAULT_HARNESS,
                        help=f"Coding-agent harness (default: {DEFAULT_HARNESS})")
    args = parser.parse_args(argv)

    if not args.human and args.model is None:
        parser.error("model is required for agent mode (or use --human)")

    # Load infrastructure config from env + ./.env + user secrets.env
    env = _load_runtime_env()
    infra_required = ["PURELY_MAIL_API_KEY", "PURELY_MAIL_DOMAIN"]
    missing = [k for k in infra_required if not env.get(k)]
    if missing:
        for k in missing:
            print(f"ERROR: {k} not set (checked env, ./.env, and {_paths.user_secrets_path()})")
        print("  Tip: run `clawbench configure --secrets` to persist these keys")
        sys.exit(1)
    pm_key: str = env["PURELY_MAIL_API_KEY"]
    pm_domain: str = env["PURELY_MAIL_DOMAIN"]

    # HuggingFace upload (optional)
    hf_env = {"HF_TOKEN": env.get("HF_TOKEN", ""),
              "HF_REPO_ID": env.get("HF_REPO_ID", "")}
    do_upload = hf_upload_enabled(hf_env) and not args.no_upload

    # Load task
    task_dir = args.test_case_dir.resolve()
    task_file = task_dir / "task.json"
    if not task_file.exists():
        print(f"ERROR: {task_file} not found")
        sys.exit(1)
    task = json.loads(task_file.read_text())

    case_name = task_dir.name
    time_limit_s = task["time_limit"] * 60
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    model_cfg: dict | None = None
    if args.human:
        safe_model = "human"
        harness_tag = "human"
    else:
        model_cfg = load_model_config(args.model)
        safe_model = re.sub(r'[/:]+', '--', args.model)
        harness_tag = args.harness

    container = f"clawbench-{harness_tag}-{case_name}-{safe_model}-{int(time.time())}"
    run_dir_name = f"{harness_tag}-{case_name}-{safe_model}-{ts}"

    if args.output_dir is not None:
        output_dir = args.output_dir.resolve() / safe_model / run_dir_name
    else:
        output_dir = _paths.default_output_dir() / safe_model / run_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_build:
        step("Building container image")
        docker_build(args.harness)

    email = None
    personal_info_tmp: Path | None = None
    start_time = time.time()
    try:
        step("Creating disposable email")
        email, email_pw = create_email(pm_key, pm_domain)

        step("Preparing personal info")
        personal_info_tmp = prepare_personal_info(
            _shared_src(), email, email_pw, output_dir)
        copy_extra_info(task, task_dir, personal_info_tmp)
        print(f"  Personal info dir: {personal_info_tmp}")

        # Write eval schema for the interceptor
        schema_path = output_dir / "eval-schema.json"
        schema_path.write_text(json.dumps(task["eval_schema"], indent=2))

        step("Building instruction")
        instruction = build_instruction(task)
        print(instruction[:500])

        if args.human:
            step("Starting container (human mode)")
            # Avoid the hard-coded 6080:6080 collision: try 6080 first and
            # fall back to an OS-assigned ephemeral port if something else
            # on the host is already listening there.
            host_port = _pick_free_port(6080)
            docker_run_human(container, instruction, schema_path,
                             personal_info_tmp, time_limit_s,
                             host_port=host_port)

            # Graceful stop on Ctrl+C: give container time to flush recording
            def handle_sigint(sig, frame):
                print("\nCtrl+C received, stopping container gracefully...")
                subprocess.run([ENGINE, "stop", "-t", "20", container],
                               capture_output=True)

            signal.signal(signal.SIGINT, handle_sigint)

            vnc_url = f"http://localhost:{host_port}/vnc.html"
            console.print(f"\n  noVNC: [link={vnc_url}]{vnc_url}[/link]")
            if host_port != 6080:
                console.print(f"  [dim](port 6080 was busy, auto-picked {host_port})[/dim]")
            console.print(f"  Task:  {task['instruction'][:200]}")
            console.print(f"  Email: {email}  Password: {email_pw}")
            console.print(f"  Time limit: {task['time_limit']} minutes")
            console.print(f"  Close the noVNC tab when done.\n")

            step(f"Waiting for human (max {task['time_limit']}min)")
        else:
            step("Starting container")
            assert model_cfg is not None
            host_port = _pick_free_port(6080)
            docker_run(container, instruction, schema_path,
                       personal_info_tmp, model_cfg,
                       time_limit_s=time_limit_s,
                       host_port=host_port,
                       harness=args.harness)

            vnc_url = f"http://localhost:{host_port}/vnc.html"
            console.print(f"\n  noVNC: [link={vnc_url}]{vnc_url}[/link]")
            if host_port != 6080:
                console.print(f"  [dim](port 6080 was busy, auto-picked {host_port})[/dim]")
            console.print(f"  Open the URL above to watch the agent in real-time.\n")

            step(f"Agent running (max {task['time_limit']}min)")

        docker_wait(container)

        step("Container logs")
        docker_logs(container)

        step("Copying results")
        docker_copy(container, output_dir)
        _fix_data_ownership(output_dir / "data")

        ensure_interception(output_dir)

        step("Results")
        intercepted = print_results(output_dir)

        # Write run metadata
        duration = time.time() - start_time
        if args.human:
            meta = {
                "test_case": case_name,
                **(task.get("metadata") or {}),
                "instruction": task["instruction"],
                "model": "human",
                "harness": "human",
                "thinking_level": None,
                "temperature": None,
                "max_tokens": None,
                "email_used": email,
                "timestamp": ts,
                "time_limit_minutes": task["time_limit"],
                "duration_seconds": round(duration),
                "intercepted": intercepted,
            }
        else:
            assert model_cfg is not None
            meta = {
                "test_case": case_name,
                **(task.get("metadata") or {}),
                "instruction": task["instruction"],
                "model": model_cfg["model"],
                "harness": args.harness,
                "thinking_level": model_cfg.get("thinking_level"),
                "temperature": model_cfg.get("temperature"),
                "max_tokens": model_cfg.get("max_tokens"),
                "email_used": email,
                "timestamp": ts,
                "time_limit_minutes": task["time_limit"],
                "duration_seconds": round(duration),
                "intercepted": intercepted,
            }
        (output_dir / "run-meta.json").write_text(json.dumps(meta, indent=2))

        if do_upload:
            step("Uploading to HuggingFace")
            repo_path = f"{safe_model}/{run_dir_name}"
            upload_run(output_dir, repo_path, hf_env)

    finally:
        step("Cleanup")
        docker_rm(container)
        if email:
            delete_email(pm_key, email)
        if personal_info_tmp and personal_info_tmp.exists():
            shutil.rmtree(personal_info_tmp, ignore_errors=True)
        (output_dir / "eval-schema.json").unlink(missing_ok=True)

    if intercepted:
        print(f"\nINTERCEPTED — results in {output_dir}")
        from clawbench.support import print_star_prompt
        print_star_prompt()
    else:
        print(f"\nNOT INTERCEPTED — results in {output_dir}")
        sys.exit(1)


if __name__ == "__main__":
    main()
