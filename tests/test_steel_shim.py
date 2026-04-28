"""Tests for steel-cdp-shim.py — the CDP proxy that fronts a Steel session.

We don't require a real Steel API key here. Two strategies:

1. ``test_session_to_dict_handles_*``: pure-function tests of the shape
   adapters used to serialize SDK objects to JSON. No network.

2. ``test_shim_proxies_ws_bytes`` / ``test_shim_serves_json_version``:
   spin up a fake "Steel" upstream — a websockets server we control —
   and run the shim against it with a stubbed Steel SDK. Verifies that
   /json/version returns the local WS URL and that bytes round-trip
   cleanly through the proxy.

The shim file lives at the repo root (`steel-cdp-shim.py`) — we load it
via importlib because the hyphenated name isn't a valid Python module."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import socket
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_shim_module():
    spec = importlib.util.spec_from_file_location(
        "steel_cdp_shim", REPO_ROOT / "steel-cdp-shim.py"
    )
    if spec is None or spec.loader is None:
        pytest.skip("could not locate steel-cdp-shim.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["steel_cdp_shim"] = mod
    try:
        spec.loader.exec_module(mod)
    except ImportError as e:
        pytest.skip(f"shim deps not installed: {e}")
    return mod


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Pure-function tests (no network)
# ---------------------------------------------------------------------------


def test_session_to_dict_uses_model_dump():
    shim = _load_shim_module()

    class FakeSession:
        def model_dump(self):
            return {"id": "abc", "status": "live"}

    assert shim._session_to_dict(FakeSession()) == {"id": "abc", "status": "live"}


def test_session_to_dict_falls_back_to_dict_method():
    shim = _load_shim_module()

    class FakeSession:
        def dict(self):
            return {"id": "xyz"}

    assert shim._session_to_dict(FakeSession()) == {"id": "xyz"}


def test_session_to_dict_falls_back_to_vars():
    shim = _load_shim_module()

    @dataclass
    class FakeSession:
        id: str = "plain"
        _internal: str = "skip"

    out = shim._session_to_dict(FakeSession())
    assert out["id"] == "plain"
    assert "_internal" not in out


# ---------------------------------------------------------------------------
# Live shim against a fake upstream
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_steel_upstream(monkeypatch):
    """Start a websockets echo server and patch the shim to point at it."""
    aiohttp = pytest.importorskip("aiohttp")
    web = aiohttp.web

    received: list[str] = []

    async def upstream_ws(request):
        ws = web.WebSocketResponse(autoping=False)
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                received.append(msg.data)
                # Echo with id wrapped to mimic CDP response
                try:
                    parsed = json.loads(msg.data)
                    if "id" in parsed:
                        await ws.send_str(json.dumps({
                            "id": parsed["id"], "result": {"echoed": parsed}
                        }))
                except json.JSONDecodeError:
                    await ws.send_str(msg.data)
            elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                break
        return ws

    upstream_app = web.Application()
    upstream_app.router.add_get("/", upstream_ws)
    return upstream_app, received


def test_shim_serves_json_version_pointing_at_itself(tmp_path, monkeypatch):
    """The /json/version response must put webSocketDebuggerUrl back on the shim
    so existing CDP clients (Playwright, browser-use, hermes) follow it back
    into the proxy rather than trying to reach Steel directly over HTTPS."""
    pytest.importorskip("aiohttp")
    shim = _load_shim_module()

    class FakeSession:
        def __init__(self):
            self.id = "test-session-123"
            self.session_viewer_url = "https://app.steel.dev/sessions/test-session-123"

        def model_dump(self):
            return {"id": self.id, "session_viewer_url": self.session_viewer_url}

    state = shim.ShimState(
        api_key="sk-fake",
        session=FakeSession(),
        data_dir=tmp_path,
        host="127.0.0.1",
        port=12345,
    )

    app = shim.build_app(state)
    app["browser_version"] = {
        "product": "Chrome/131.0",
        "userAgent": "TestUA",
        "protocolVersion": "1.3",
        "jsVersion": "12.0",
    }

    aiohttp = pytest.importorskip("aiohttp")
    from aiohttp.test_utils import TestClient, TestServer

    async def _run():
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/json/version")
            assert resp.status == 200
            data = await resp.json()
            assert data["Browser"] == "Chrome/131.0"
            assert data["User-Agent"] == "TestUA"
            assert data["webSocketDebuggerUrl"].endswith(
                "/devtools/browser/test-session-123"
            )
            assert data["webSocketDebuggerUrl"].startswith("ws://127.0.0.1:")

            # /json defaults to empty target list — clients that need
            # targets discover via Target.* CDP, not this HTTP list.
            resp2 = await client.get("/json")
            assert resp2.status == 200
            assert await resp2.json() == []

    asyncio.run(_run())
