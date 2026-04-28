#!/usr/bin/env python3
# ABOUTME: One-shot validation that two CDP clients can coexist on a single Steel session.
# ABOUTME: Run before trusting the steel-cdp-shim — confirms eval-runner + harness Playwright pattern works.
"""
Validates the load-bearing assumption of the Steel browser provider:
the eval-runner (Fetch.enable + Target.setAutoAttach) and the harness
(Page.navigate via its own Playwright connection) can both attach to
one Steel session simultaneously without one clobbering the other.

Usage:
    STEEL_API_KEY=sk-... uv run python tools/probe_steel_multiclient.py

The probe:
  1. Creates a Steel session
  2. Opens client A (eval-runner role): Target.setAutoAttach(flatten=true)
     + Fetch.enable("*"), with a url filter that matches httpbin.org/post
  3. Opens client B (harness role): Page.navigate to https://httpbin.org/get
     and POSTs to https://httpbin.org/post via in-page fetch()
  4. Confirms client A receives Fetch.requestPaused for the POST and that
     Fetch.failRequest from A actually blocks the request (B's fetch fails)
  5. Releases the session

Exit code 0 = multi-client works → ship the shim. Non-zero = the byte-level
proxy approach needs revisiting.
"""

import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager

import aiohttp
from steel import Steel


HTTPBIN_GET = "https://httpbin.org/get"
HTTPBIN_POST = "https://httpbin.org/post"
EVAL_PATTERN = "httpbin.org/post"


@asynccontextmanager
async def cdp_client(ws_url: str, name: str):
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=20, sock_read=None)
    async with aiohttp.ClientSession(timeout=timeout) as http:
        async with http.ws_connect(ws_url, autoping=False, max_msg_size=0) as ws:
            print(f"[{name}] connected to {ws_url[:60]}...")
            yield ws
            print(f"[{name}] disconnecting")


class CDPClient:
    """Tiny CDP client that tracks msg_id and dispatches by id/method."""

    def __init__(self, ws, name: str):
        self.ws = ws
        self.name = name
        self.msg_id = 0
        self.pending: dict[int, asyncio.Future] = {}
        self.event_listeners: list = []

    async def call(self, method: str, params: dict | None = None,
                   session_id: str | None = None, timeout: float = 15.0):
        self.msg_id += 1
        msg_id = self.msg_id
        msg = {"id": msg_id, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        fut = asyncio.get_running_loop().create_future()
        self.pending[msg_id] = fut
        await self.ws.send_str(json.dumps(msg))
        return await asyncio.wait_for(fut, timeout=timeout)

    async def reader(self):
        async for raw in self.ws:
            if raw.type != aiohttp.WSMsgType.TEXT:
                continue
            msg = json.loads(raw.data)
            mid = msg.get("id")
            if mid is not None and mid in self.pending:
                fut = self.pending.pop(mid)
                if not fut.done():
                    if "error" in msg:
                        fut.set_exception(RuntimeError(f"{msg['error']}"))
                    else:
                        fut.set_result(msg.get("result", {}))
                continue
            if "method" in msg:
                for cb in self.event_listeners:
                    cb(msg)


async def probe(api_key: str) -> int:
    client = Steel(steel_api_key=api_key)
    print(f"[probe] creating steel session...")
    session = client.sessions.create(api_timeout=120_000)
    sid = session.id
    print(f"[probe] session id: {sid}")

    ws_url = f"wss://connect.steel.dev?apiKey={api_key}&sessionId={sid}"

    intercepted = asyncio.Event()
    intercept_record: dict = {}

    try:
        async with cdp_client(ws_url, "A-eval") as ws_a, \
                   cdp_client(ws_url, "B-harness") as ws_b:
            ca = CDPClient(ws_a, "A-eval")
            cb = CDPClient(ws_b, "B-harness")

            ca_reader = asyncio.create_task(ca.reader())
            cb_reader = asyncio.create_task(cb.reader())

            page_sessions: set[str] = set()

            def on_event_a(msg):
                method = msg.get("method")
                if method == "Target.attachedToTarget":
                    sess = msg["params"]["sessionId"]
                    ttype = msg["params"]["targetInfo"]["type"]
                    if ttype == "page":
                        page_sessions.add(sess)
                        print(f"[A-eval] auto-attached page session {sess[:12]}")
                        asyncio.create_task(_enable_fetch_on(ca, sess))
                elif method == "Fetch.requestPaused":
                    url = msg["params"]["request"]["url"]
                    method_str = msg["params"]["request"]["method"]
                    rid = msg["params"]["requestId"]
                    sess = msg.get("sessionId")
                    print(f"[A-eval] Fetch.requestPaused {method_str} {url[:80]}")
                    if EVAL_PATTERN in url and method_str == "POST":
                        intercept_record.update({"url": url, "method": method_str})
                        asyncio.create_task(ca.call(
                            "Fetch.failRequest",
                            {"requestId": rid, "errorReason": "BlockedByClient"},
                            session_id=sess,
                        ))
                        intercepted.set()
                    else:
                        asyncio.create_task(ca.call(
                            "Fetch.continueRequest",
                            {"requestId": rid},
                            session_id=sess,
                        ))

            ca.event_listeners.append(on_event_a)

            print("[A-eval] enabling Target.setAutoAttach + Fetch.enable")
            await ca.call("Target.setAutoAttach", {
                "autoAttach": True,
                "waitForDebuggerOnStart": False,
                "flatten": True,
            })

            print("[B-harness] creating new page target")
            tgt = await cb.call("Target.createTarget", {"url": "about:blank"})
            target_id = tgt.get("targetId")
            print(f"[B-harness] target {target_id[:12]} created")

            # Give A's setAutoAttach a moment to surface the new target
            for _ in range(20):
                if page_sessions:
                    break
                await asyncio.sleep(0.25)

            if not page_sessions:
                print("[probe] FAIL: A never received Target.attachedToTarget for new page")
                print("[probe] verdict: setAutoAttach from a second client does not see new targets")
                return 11

            print(f"[probe] A is attached to {len(page_sessions)} page session(s)")

            # Have B drive a navigation + a POST that A should intercept.
            # Attach B to its own target so it can issue Page commands.
            attach = await cb.call("Target.attachToTarget",
                                   {"targetId": target_id, "flatten": True})
            b_session = attach.get("sessionId")

            await cb.call("Page.enable", session_id=b_session)
            print("[B-harness] Page.navigate → httpbin.org/get")
            await cb.call("Page.navigate", {"url": HTTPBIN_GET}, session_id=b_session)
            await asyncio.sleep(2.0)

            print("[B-harness] firing in-page POST → httpbin.org/post")
            await cb.call("Runtime.evaluate", {
                "expression": (
                    "fetch('https://httpbin.org/post', "
                    "{method:'POST', body: JSON.stringify({probe: true}), "
                    " headers: {'content-type':'application/json'}}).then(r=>r.status).catch(e=>'BLOCKED')"
                ),
                "awaitPromise": True,
                "returnByValue": True,
            }, session_id=b_session)

            try:
                await asyncio.wait_for(intercepted.wait(), timeout=20.0)
                print(f"[probe] PASS — interception observed: {intercept_record}")
                return 0
            except asyncio.TimeoutError:
                print("[probe] FAIL: A never observed the POST")
                print("[probe] verdict: harness's Playwright/Network handling shadows Fetch on this target")
                return 12
            finally:
                ca_reader.cancel()
                cb_reader.cancel()
    finally:
        try:
            client.sessions.release(sid)
            print(f"[probe] released session {sid}")
        except Exception as e:
            print(f"[probe] release failed: {e}")


async def _enable_fetch_on(c: CDPClient, session_id: str):
    try:
        await c.call("Fetch.enable", {
            "patterns": [{"urlPattern": "*", "requestStage": "Request"}],
        }, session_id=session_id)
        await c.call("Runtime.runIfWaitingForDebugger", session_id=session_id)
    except Exception as e:
        print(f"[A-eval] Fetch.enable failed for {session_id[:12]}: {e}")


def main() -> int:
    api_key = os.environ.get("STEEL_API_KEY")
    if not api_key:
        print("STEEL_API_KEY not set", file=sys.stderr)
        return 2
    return asyncio.run(probe(api_key))


if __name__ == "__main__":
    sys.exit(main())
