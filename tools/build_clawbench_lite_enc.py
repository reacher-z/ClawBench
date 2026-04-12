#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["cryptography>=42"]
# ///
"""Build the ClawBench-Lite encrypted task blob for browser-use/benchmark.

Reads `test-cases/lite.json`, resolves each entry to its `task.json`, and for
every task produces exactly::

    {
        "task_id": "clawbench-lite-NNN",
        "confirmed_task": build_instruction(task),
    }

`build_instruction` is copied VERBATIM from `test-driver/run.py` (L223-266).
The copy is intentional: `run.py` imports heavy modules (`yaml`,
`generate_resume_pdf`, `hf_upload`) that make direct import awkward, and
having the body here makes it obvious that the adapter produces byte-identical
prompts to what ClawBench main bench serves via Docker. If `run.py`'s prompt
builder ever changes, update this copy in the same commit.

The output list is Fernet-encrypted with seed ``b"ClawBench_Lite_V1"`` and
written as base64 text, matching the upstream decrypt path in
``browser-use/benchmark/run_eval.py``.

Usage:
    uv run tools/build_clawbench_lite_enc.py --dry-run
    uv run tools/build_clawbench_lite_enc.py --out ClawBench_Lite_V1.enc
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.fernet import Fernet

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LITE_MANIFEST = PROJECT_ROOT / "test-cases" / "lite.json"
ENCRYPTION_SEED = b"ClawBench_Lite_V1"


# ---------------------------------------------------------------------------
# KEEP IN SYNC with test-driver/run.py::build_instruction (L223-266).
# Copied verbatim. Do not edit the string contents. If run.py changes, update
# this copy in the same commit.
# ---------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------


def load_lite_tasks() -> list[dict]:
    """Read lite.json and each referenced task.json, return upstream-shaped dicts."""
    manifest = json.loads(LITE_MANIFEST.read_text(encoding="utf-8"))
    tasks: list[dict] = []
    for entry in manifest["tasks"]:
        task_dir = PROJECT_ROOT / "test-cases" / entry["dir"]
        task_path = task_dir / "task.json"
        task = json.loads(task_path.read_text(encoding="utf-8"))
        tid = task["metadata"]["task_id"]
        tasks.append({
            "task_id": f"clawbench-lite-{tid:03d}",
            "confirmed_task": build_instruction(task),
        })
    return tasks


def encrypt_tasks(tasks: list[dict]) -> str:
    """Fernet-encrypt the task list with the upstream-compatible seed."""
    key = base64.urlsafe_b64encode(hashlib.sha256(ENCRYPTION_SEED).digest())
    payload = json.dumps(tasks, ensure_ascii=False).encode("utf-8")
    ciphertext = Fernet(key).encrypt(payload)
    return base64.b64encode(ciphertext).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "ClawBench_Lite_V1.enc",
        help="Path to write the encrypted .enc file (ignored with --dry-run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write plaintext JSON to clawbench_lite_v1.plaintext.json instead "
             "of encrypting.",
    )
    args = parser.parse_args()

    tasks = load_lite_tasks()
    if len(tasks) != 20:
        print(f"ERROR: expected 20 tasks, got {len(tasks)}", file=sys.stderr)
        return 1

    if args.dry_run:
        out = PROJECT_ROOT / "clawbench_lite_v1.plaintext.json"
        out.write_text(
            json.dumps(tasks, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[dry-run] wrote plaintext to {out} ({len(tasks)} tasks)")
        return 0

    encoded = encrypt_tasks(tasks)
    args.out.write_text(encoded, encoding="ascii")
    print(f"wrote {args.out} ({len(tasks)} tasks, {len(encoded)} bytes base64)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
