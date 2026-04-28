#!/usr/bin/env python3
# ABOUTME: CDP proxy shim that fronts a Steel.dev cloud browser session.
# ABOUTME: Serves /json/version on 127.0.0.1:9222 and pipes CDP WS bytes to wss://connect.steel.dev.
"""
Run inside the per-case container when STEEL_API_KEY is set. The existing
extension-server, every harness, and any tool that points at
http://127.0.0.1:9222 talks to this shim instead of a local Chromium.

Lifecycle:
  1. Create a Steel session via the SDK
  2. Write /data/steel/session.json + /data/steel/browser-version.json
  3. Bind 127.0.0.1:9222; serve /json/version, /json, /json/list (HTTP)
  4. Proxy GET /devtools/browser/<sid> (WebSocket) byte-for-byte to
     wss://connect.steel.dev?apiKey=...&sessionId=...
  5. On SIGTERM/SIGINT, release the Steel session and exit cleanly
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path

import aiohttp
from aiohttp import web
from steel import Steel


log = logging.getLogger("steel-cdp-shim")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9222
STEEL_WSS_BASE = "wss://connect.steel.dev"


class ShimState:
    """Holds the live Steel session and config for a single shim instance."""

    def __init__(self, api_key: str, session, data_dir: Path, host: str, port: int):
        self.api_key = api_key
        self.session = session
        self.data_dir = data_dir
        self.host = host
        self.port = port

    @property
    def session_id(self) -> str:
        return self.session.id

    @property
    def upstream_ws_url(self) -> str:
        return f"{STEEL_WSS_BASE}?apiKey={self.api_key}&sessionId={self.session_id}"

    @property
    def local_ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}/devtools/browser/{self.session_id}"


def _session_to_dict(session) -> dict:
    """Serialize a Steel Session pydantic model to a plain dict.

    Falls back through model_dump → dict → vars to handle SDK shape drift.
    """
    for attr in ("model_dump", "dict"):
        fn = getattr(session, attr, None)
        if callable(fn):
            try:
                return fn()
            except TypeError:
                continue
    return {k: v for k, v in vars(session).items() if not k.startswith("_")}


async def _fetch_browser_version(state: ShimState) -> dict:
    """One-shot CDP Browser.getVersion call, captured at startup for run-meta."""
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.ws_connect(state.upstream_ws_url, autoping=False) as ws:
                await ws.send_str(json.dumps({"id": 1, "method": "Browser.getVersion"}))
                async for msg in ws:
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        continue
                    data = json.loads(msg.data)
                    if data.get("id") == 1 and "result" in data:
                        await ws.close()
                        return data["result"]
                    if data.get("id") == 1 and "error" in data:
                        log.warning("Browser.getVersion error: %s", data["error"])
                        return {}
    except Exception as e:
        log.warning("Browser.getVersion failed: %s", e)
    return {}


async def _write_initial_artifacts(state: ShimState) -> None:
    """Persist what we know at startup so artifacts exist even on early failure."""
    out_dir = state.data_dir / "steel"
    out_dir.mkdir(parents=True, exist_ok=True)

    session_dict = _session_to_dict(state.session)
    (out_dir / "session.json").write_text(json.dumps(session_dict, indent=2, default=str))

    version = await _fetch_browser_version(state)
    (out_dir / "browser-version.json").write_text(json.dumps(version, indent=2))


# ---------------------------------------------------------------------------
# HTTP / WS handlers
# ---------------------------------------------------------------------------


async def handle_json_version(request: web.Request) -> web.Response:
    state: ShimState = request.app["state"]
    version = request.app.get("browser_version") or {}
    return web.json_response({
        "Browser": version.get("product", f"Steel/{state.session_id}"),
        "Protocol-Version": version.get("protocolVersion", "1.3"),
        "User-Agent": version.get("userAgent", "ClawBench-Steel-Shim"),
        "V8-Version": version.get("jsVersion", ""),
        "WebKit-Version": "",
        "webSocketDebuggerUrl": state.local_ws_url,
    })


async def handle_json_list(request: web.Request) -> web.Response:
    # Most harnesses (Playwright, browser-use, hermes) connect via the
    # browser-level webSocketDebuggerUrl from /json/version and discover
    # targets through Target.* CDP commands, not this HTTP list. Returning
    # empty is a safe default; populate dynamically only if a harness
    # surfaces a need for it.
    return web.json_response([])


async def _pump(src, dst, direction: str) -> None:
    try:
        async for msg in src:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if dst.closed:
                    break
                await dst.send_str(msg.data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                if dst.closed:
                    break
                await dst.send_bytes(msg.data)
            elif msg.type in (
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.ERROR,
                aiohttp.WSMsgType.CLOSING,
            ):
                break
    except (aiohttp.ClientError, ConnectionResetError, asyncio.CancelledError) as e:
        log.debug("[%s] pump terminated: %s", direction, e)
    except Exception:
        log.exception("[%s] pump crashed", direction)


async def handle_devtools_ws(request: web.Request) -> web.WebSocketResponse:
    """Open one upstream WS to Steel per inbound client and pump bytes.

    Per-client upstream connection — multiple harness/eval clients each get
    their own Steel WS, so Chrome's native multi-client CDP semantics apply
    upstream and the shim doesn't need to mux anything.
    """
    state: ShimState = request.app["state"]
    log.info("WS client connected from %s", request.remote)

    ws_client = web.WebSocketResponse(autoping=False, max_msg_size=0)
    await ws_client.prepare(request)

    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=None)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.ws_connect(
                state.upstream_ws_url,
                autoping=False,
                max_msg_size=0,
                heartbeat=20,
            ) as ws_upstream:
                log.info("upstream WS opened")
                await asyncio.gather(
                    _pump(ws_upstream, ws_client, "upstream→client"),
                    _pump(ws_client, ws_upstream, "client→upstream"),
                    return_exceptions=True,
                )
                log.info("upstream WS closed")
    except aiohttp.ClientError as e:
        log.error("failed to open upstream WS: %s", e)
        if not ws_client.closed:
            await ws_client.close(code=1011, message=str(e).encode()[:120])

    if not ws_client.closed:
        await ws_client.close()
    return ws_client


def build_app(state: ShimState) -> web.Application:
    app = web.Application()
    app["state"] = state
    app.router.add_get("/json/version", handle_json_version)
    app.router.add_get("/json", handle_json_list)
    app.router.add_get("/json/list", handle_json_list)
    app.router.add_get("/devtools/browser/{sid}", handle_devtools_ws)
    return app


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def _create_session(client: Steel, time_limit_s: int):
    """Best-effort session create. Steel SDK accepts api_timeout in ms; we
    add a one-minute buffer over the harness time limit so the session
    outlives normal completion. Tier-cap errors propagate up so the caller
    can write a clean stop-reason."""
    return client.sessions.create(api_timeout=time_limit_s * 1000 + 60_000)


def _release_session(client: Steel, session_id: str) -> None:
    try:
        client.sessions.release(session_id)
        log.info("released steel session %s", session_id)
    except Exception as e:
        log.warning("release failed for %s: %s", session_id, e)


async def run(args: argparse.Namespace) -> int:
    api_key = os.environ.get("STEEL_API_KEY")
    if not api_key:
        log.error("STEEL_API_KEY not set")
        return 2

    data_dir = Path(args.data_dir)
    time_limit_s = int(os.environ.get("TIME_LIMIT_S", "1800"))

    client = Steel(steel_api_key=api_key)
    log.info("creating steel session (api_timeout=%dms)", time_limit_s * 1000 + 60_000)
    try:
        session = _create_session(client, time_limit_s)
    except Exception as e:
        # Tier caps, auth errors, plan-limit errors all land here.
        msg = str(e)
        log.error("steel session create failed: %s", msg)
        out_dir = data_dir / "steel"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "session-error.json").write_text(json.dumps({"error": msg}, indent=2))
        # Surface a clean stop reason for run.py's ensure_interception().
        (data_dir / ".stop-reason").write_text("steel_session_create_failed\n")
        return 3

    log.info("steel session %s created", session.id)

    state = ShimState(
        api_key=api_key,
        session=session,
        data_dir=data_dir,
        host=args.host,
        port=args.port,
    )

    await _write_initial_artifacts(state)
    # Cache the version dict so /json/version is consistent across calls
    try:
        version_path = data_dir / "steel" / "browser-version.json"
        if version_path.exists():
            state_app_version = json.loads(version_path.read_text())
        else:
            state_app_version = {}
    except Exception:
        state_app_version = {}

    app = build_app(state)
    app["browser_version"] = state_app_version

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    log.info("listening on http://%s:%d (CDP for steel session %s)",
             args.host, args.port, session.id)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        await stop_event.wait()
    finally:
        log.info("shutting down shim")
        await runner.cleanup()
        _release_session(client, session.id)

    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Steel CDP proxy shim")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument(
        "--data-dir",
        default=os.environ.get("CLAWBENCH_DATA_DIR", "/data"),
        help="where to write steel/session.json + steel/browser-version.json",
    )
    p.add_argument("--log-level", default="INFO")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="[shim] %(message)s",
    )
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
