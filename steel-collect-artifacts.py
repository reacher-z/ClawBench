#!/usr/bin/env python3
# ABOUTME: Post-run Steel artifact collector — fetches session metadata, rrweb events, context, and proxy info.
# ABOUTME: Called from entrypoint.sh after the harness exits, before container shutdown.
"""
Reads the session id from /data/steel/session.json (written by the shim at
startup) and pulls everything Steel exposes about the run into /data/steel/.

Each endpoint is best-effort: a failure on /events doesn't block /context,
etc. The session id is the only required input — no Steel API key on the
command line; we read STEEL_API_KEY from env like the shim does.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from steel import Steel


log = logging.getLogger("steel-collect-artifacts")


def _to_dict(obj) -> dict | list:
    if obj is None:
        return {}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(x) for x in obj]
    for attr in ("model_dump", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except TypeError:
                continue
    if isinstance(obj, dict):
        return obj
    return {k: v for k, v in vars(obj).items() if not k.startswith("_")}


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))
    log.info("wrote %s (%d bytes)", path, path.stat().st_size)


def collect_session(client: Steel, session_id: str, out_dir: Path) -> None:
    try:
        session = client.sessions.retrieve(session_id)
        _save(out_dir / "session.json", _to_dict(session))
    except Exception as e:
        log.warning("retrieve failed: %s", e)


def collect_events(client: Steel, session_id: str, out_dir: Path) -> None:
    """rrweb stream — paginated. Save as JSONL, one event per line."""
    out_path = out_dir / "events.jsonl"
    try:
        # SDK exposes .events(id, **params) → SessionEventsResponse with
        # paginated semantics. Iterate defensively across both shapes
        # (paginator object vs single response with .events list).
        resp = client.sessions.events(session_id)
        events = _extract_events(resp)
        with out_path.open("w") as f:
            for ev in events:
                f.write(json.dumps(_to_dict(ev), default=str) + "\n")
        log.info("wrote %s (%d events)", out_path, len(events))
    except Exception as e:
        log.warning("events failed: %s", e)


def _extract_events(resp) -> list:
    """SDK shape varies by version; try several attribute names."""
    if resp is None:
        return []
    if isinstance(resp, list):
        return resp
    for attr in ("events", "data", "items", "results"):
        events = getattr(resp, attr, None)
        if events is not None:
            return list(events)
    # iterable / paginator
    try:
        return list(resp)
    except TypeError:
        return []


def collect_context(client: Steel, session_id: str, out_dir: Path) -> None:
    try:
        ctx = client.sessions.context(session_id)
        _save(out_dir / "context.json", _to_dict(ctx))
    except Exception as e:
        log.warning("context failed: %s", e)


def collect_live_details(client: Steel, session_id: str, out_dir: Path) -> None:
    """Useful when invoked while the session is still live (debug/manual)."""
    try:
        live = client.sessions.live_details(session_id)
        _save(out_dir / "live-details.json", _to_dict(live))
    except Exception as e:
        log.debug("live_details failed (ok if session already released): %s", e)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--data-dir",
        default=os.environ.get("CLAWBENCH_DATA_DIR", "/data"),
    )
    p.add_argument("--log-level", default="INFO")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="[collect] %(message)s",
    )

    api_key = os.environ.get("STEEL_API_KEY")
    if not api_key:
        log.error("STEEL_API_KEY not set")
        return 2

    out_dir = Path(args.data_dir) / "steel"
    session_path = out_dir / "session.json"
    if not session_path.exists():
        log.error("no session.json at %s — shim never started?", session_path)
        return 3

    try:
        existing = json.loads(session_path.read_text())
        session_id = existing.get("id")
    except Exception as e:
        log.error("could not read session.json: %s", e)
        return 4

    if not session_id:
        log.error("session.json has no id")
        return 5

    client = Steel(steel_api_key=api_key)
    log.info("collecting artifacts for session %s", session_id)

    # Order matters: retrieve overwrites session.json with the post-run
    # state (status, duration, eventCount, creditsUsed). Then events
    # (likely the slowest), then context, then live details.
    collect_session(client, session_id, out_dir)
    collect_events(client, session_id, out_dir)
    collect_context(client, session_id, out_dir)
    collect_live_details(client, session_id, out_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
