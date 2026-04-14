"""ClawBench single test-case driver."""

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
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

from generate_resume_pdf import generate_resume_pdf
from hf_upload import hf_upload_enabled, upload_run

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE = "clawbench"
console = Console()


def _detect_engine() -> str:
    env = os.environ.get("CONTAINER_ENGINE", "").strip().lower()
    if env:
        if env not in ("docker", "podman"):
            print(
                f"ERROR: CONTAINER_ENGINE must be 'docker' or 'podman', got '{env}'")
            sys.exit(1)
        if not shutil.which(env):
            print(
                f"ERROR: CONTAINER_ENGINE={env} but '{env}' not found on PATH")
            sys.exit(1)
        return env
    for cmd in ("docker", "podman"):
        if shutil.which(cmd):
            return cmd
    print("ERROR: Neither 'podman' nor 'docker' found on PATH")
    sys.exit(1)


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


MODELS_YAML = PROJECT_ROOT / "models" / "models.yaml"


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

def _image_exists() -> bool:
    return subprocess.run(
        [ENGINE, "image", "inspect", IMAGE],
        capture_output=True,
    ).returncode == 0


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


def docker_build() -> None:
    """Build (or rebuild) the clawbench image with a live progress spinner.

    The first build pulls ~2GB (python base, chromium, ffmpeg, noVNC, Node,
    openclaw) and takes several minutes; subsequent rebuilds are near-instant
    when the layer cache is warm. We show a banner only for the cold path.

    If the build fails with a pattern that suggests stale layer-cache
    (e.g. a lockfile mismatch), we automatically retry once with
    ``--no-cache`` so the user doesn't have to debug it manually.
    """
    first_build = not _image_exists()

    if first_build:
        console.print()
        console.print(Panel(
            "[bold]First-time container build.[/]\n"
            "This downloads ~2 GB (chromium, ffmpeg, noVNC, Node, openclaw)\n"
            "and typically takes [bold]5–10 minutes[/] on a decent connection.\n"
            "[dim]Subsequent runs reuse the layer cache and finish in seconds.[/]",
            title="[bold]Building clawbench image[/]",
            border_style="cyan",
        ))

    cmd = [ENGINE, "build", "-t", IMAGE, str(PROJECT_ROOT)]
    rc, last_line, output_lines = _run_build(cmd)

    # If the build failed and the output looks like a stale-cache
    # problem, retry once with --no-cache before giving up.
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
        cmd_nc = [ENGINE, "build", "--no-cache", "-t", IMAGE, str(PROJECT_ROOT)]
        rc, last_line, output_lines = _run_build(cmd_nc)

    if rc != 0:
        console.print(f"[red bold]Build failed[/] (exit {rc})")
        if last_line:
            console.print(f"  Last output: [dim]{last_line}[/]")
        sys.exit(rc)

    console.print("[green]✓[/] Container image ready")


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
            IMAGE,
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
        IMAGE,
    ]
    run(cmd)


def docker_run(name: str, instruction: str, schema_path: Path,
               personal_info_dir: Path, model_cfg: dict,
               time_limit_s: int = 1800,
               host_port: int | None = None) -> None:
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
    run([*env_flags, IMAGE])


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
    # Remove internal marker file and bulky logs
    (output_dir / "data" / ".stop-requested").unlink(missing_ok=True)
    (output_dir / "data" / "agent.log").unlink(missing_ok=True)
    (output_dir / "data" / "gateway.log").unlink(missing_ok=True)


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


def main():
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
    args = parser.parse_args()

    if not args.human and args.model is None:
        parser.error("model is required for agent mode (or use --human)")

    # Load infrastructure config from .env (PurelyMail only)
    env = load_dotenv(PROJECT_ROOT / ".env")
    infra_required = ["PURELY_MAIL_API_KEY", "PURELY_MAIL_DOMAIN"]
    missing = [k for k in infra_required if not env.get(k)]
    if missing:
        for k in missing:
            print(f"ERROR: {k} not set in .env")
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
    task_bytes = task_file.read_bytes()
    task = json.loads(task_bytes)
    task_json_sha256 = hashlib.sha256(task_bytes).hexdigest()

    case_name = task_dir.name
    time_limit_s = task["time_limit"] * 60
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    model_cfg: dict | None = None
    if args.human:
        safe_model = "human"
    else:
        model_cfg = load_model_config(args.model)
        safe_model = re.sub(r'[/:]+', '--', args.model)

    container = f"clawbench-{case_name}-{safe_model}-{int(time.time())}"

    if args.output_dir is not None:
        output_dir = args.output_dir.resolve() / safe_model / \
            f"{case_name}-{safe_model}-{ts}"
    else:
        output_dir = PROJECT_ROOT / "test-output" / \
            safe_model / f"{case_name}-{safe_model}-{ts}"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_build:
        step("Building container image")
        docker_build()

    email = None
    personal_info_tmp: Path | None = None
    start_time = time.time()
    try:
        step("Creating disposable email")
        email, email_pw = create_email(pm_key, pm_domain)

        step("Preparing personal info")
        personal_info_tmp = prepare_personal_info(
            PROJECT_ROOT / "shared", email, email_pw, output_dir)
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
                       host_port=host_port)

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
                "task_json_sha256": task_json_sha256,
                "instruction": task["instruction"],
                "model": "human",
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
                "task_json_sha256": task_json_sha256,
                "instruction": task["instruction"],
                "model": model_cfg["model"],
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
            repo_path = f"{safe_model}/{case_name}-{safe_model}-{ts}"
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
    else:
        print(f"\nNOT INTERCEPTED — results in {output_dir}")
        sys.exit(1)


if __name__ == "__main__":
    main()
