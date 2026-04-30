#!/usr/bin/env python3
"""Run Hermes with ClawBench live transcript capture callbacks."""

import json
import os
import sys
import threading
import time
from pathlib import Path

OUT = Path(
    os.environ.get(
        "CLAWBENCH_HERMES_LIVE_JSONL",
        "/tmp/hermes-live-agent-messages.jsonl",
    )
)
_LOCK = threading.Lock()
_SEQ = 0


def _safe_json(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _write(row):
    global _SEQ
    with _LOCK:
        _SEQ += 1
        payload = {
            "seq": _SEQ,
            "timestamp": time.time(),
            **row,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    default=str,
                    separators=(",", ":"),
                )
                + "\n"
            )


def _wrap_callback(existing, writer):
    def wrapped(*args, **kwargs):
        try:
            writer(*args, **kwargs)
        except Exception:
            pass
        if existing:
            return existing(*args, **kwargs)
        return None

    return wrapped


def _install_capture():
    import cli

    original_init_agent = cli.HermesCLI._init_agent

    def patched_init_agent(self, *args, **kwargs):
        ok = original_init_agent(self, *args, **kwargs)
        agent = getattr(self, "agent", None)
        if (
            not ok
            or agent is None
            or getattr(agent, "_clawbench_capture_installed", False)
        ):
            return ok

        agent._clawbench_capture_installed = True
        _write(
            {
                "type": "session_meta",
                "session_id": getattr(agent, "session_id", None),
                "model": getattr(agent, "model", None),
                "provider": getattr(agent, "provider", None),
                "platform": getattr(agent, "platform", None),
            }
        )

        def on_reasoning(text):
            if text:
                _write(
                    {
                        "type": "reasoning",
                        "session_id": getattr(agent, "session_id", None),
                        "role": "assistant",
                        "reasoning": text,
                    }
                )

        def on_thinking(text):
            if text:
                _write(
                    {
                        "type": "thinking",
                        "session_id": getattr(agent, "session_id", None),
                        "content": text,
                    }
                )

        def on_tool_start(call_id, name, tool_args):
            function = {
                "name": name,
                "arguments": json.dumps(
                    _safe_json(tool_args),
                    ensure_ascii=False,
                    default=str,
                ),
            }
            _write(
                {
                    "type": "tool_use",
                    "session_id": getattr(agent, "session_id", None),
                    "role": "assistant",
                    "tool_name": name,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": function,
                        }
                    ],
                    "arguments": _safe_json(tool_args),
                }
            )

        def on_tool_complete(call_id, name, tool_args, result):
            _write(
                {
                    "type": "tool_result",
                    "session_id": getattr(agent, "session_id", None),
                    "role": "tool",
                    "tool_call_id": call_id,
                    "tool_name": name,
                    "arguments": _safe_json(tool_args),
                    "content": _safe_json(result),
                }
            )

        def on_tool_progress(
            event_type, function_name=None, preview=None, function_args=None, **extra
        ):
            if event_type == "reasoning.available" and preview:
                _write(
                    {
                        "type": "reasoning",
                        "session_id": getattr(agent, "session_id", None),
                        "role": "assistant",
                        "reasoning": preview,
                        "source": "tool_progress",
                    }
                )
            elif event_type in {"tool.started", "tool.completed"}:
                _write(
                    {
                        "type": event_type.replace(".", "_"),
                        "session_id": getattr(agent, "session_id", None),
                        "tool_name": function_name,
                        "preview": preview,
                        "arguments": _safe_json(function_args),
                        "extra": _safe_json(extra),
                    }
                )

        agent.reasoning_callback = _wrap_callback(
            agent.reasoning_callback,
            on_reasoning,
        )
        agent.thinking_callback = _wrap_callback(agent.thinking_callback, on_thinking)
        agent.tool_start_callback = _wrap_callback(
            agent.tool_start_callback,
            on_tool_start,
        )
        agent.tool_complete_callback = _wrap_callback(
            agent.tool_complete_callback,
            on_tool_complete,
        )
        agent.tool_progress_callback = _wrap_callback(
            agent.tool_progress_callback,
            on_tool_progress,
        )
        return ok

    cli.HermesCLI._init_agent = patched_init_agent


def main():
    _install_capture()
    from hermes_cli.main import main as hermes_main

    return hermes_main()


if __name__ == "__main__":
    sys.exit(main())
