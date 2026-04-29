"""ClawBench browser-use agent driver.

Talks to the local LiteLLM proxy (localhost:4000) via browser-use's
ChatOpenAI wrapper.
Streams transcript to /data/agent-messages.jsonl after every step so
partial history survives a watchdog kill.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from browser_use import Agent, Browser, ChatOpenAI, Tools

OUT = Path("/data/agent-messages.jsonl")
STOP = Path("/data/.stop-requested")  # extension-server eval-match marker

# Map our THINKING_LEVEL values onto browser-use's `reasoning_effort` levels.
_EFFORT_MAP = {
    "minimal":  "minimal",
    "low":      "low",
    "medium":   "medium",
    "adaptive": "medium",
    "high":     "high",
    "xhigh":    "high",
}


def make_llm() -> ChatOpenAI:
    """Construct browser-use's ChatOpenAI pointed at the local LiteLLM proxy."""
    model = os.environ["BU_MODEL_NAME"]
    base_url = os.environ["BU_BASE_URL"]
    api_key = os.environ["BU_API_KEY"]
    temperature = float(os.environ.get("BU_TEMPERATURE", "0.0"))
    thinking = os.environ.get("BU_THINKING_LEVEL", "off").lower()
    effort = _EFFORT_MAP.get(thinking) if thinking != "off" else None

    kw: dict[str, Any] = {
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "temperature": temperature,
    }
    if effort:
        kw["reasoning_effort"] = effort
        kw["reasoning_models"] = [model]
    return ChatOpenAI(**kw)


def dump_history(agent_obj) -> None:
    """Write the current AgentHistoryList to /data/agent-messages.jsonl as JSONL."""
    with OUT.open("w") as f:
        for h in agent_obj.history.history:
            f.write(
                json.dumps(h.model_dump(), default=str,
                           ensure_ascii=False) + "\n"
            )


async def main() -> None:
    instruction = os.environ["INSTRUCTION"]
    time_limit = int(os.environ.get("TIME_LIMIT_S", "1800"))
    thinking = os.environ.get("BU_THINKING_LEVEL", "off").lower()

    # Discover any files mounted under /root/workspace/my-info/ so the
    # agent's read_file tool can access them. browser-use's FileSystem
    # only exposes paths listed in `available_file_paths`; without this
    # the model sees "file not found" for every credential lookup.
    workspace = Path("/root/workspace")
    my_info = workspace / "my-info"
    available_files: list[str] = []
    if my_info.exists():
        for p in my_info.rglob("*"):
            if p.is_file():
                available_files.append(str(p))

    llm = make_llm()
    browser = Browser(cdp_url="http://127.0.0.1:9222")
    tools = Tools()  # default: browser-only actions, no shell escape

    OUT.write_text("")  # truncate

    # We need access to the full agent for `agent.history`, so we close
    # over a mutable holder populated after Agent() is constructed.
    holder: dict = {}

    async def on_step(_state, _output, _step_num):
        agent_obj = holder.get("agent")
        if agent_obj is not None:
            dump_history(agent_obj)

    async def should_stop() -> bool:
        # Cooperate with the harness watchdog when the eval interceptor
        # signals a match by touching /data/.stop-requested.
        return STOP.exists()

    async def on_done(_history):
        agent_obj = holder.get("agent")
        if agent_obj is not None:
            dump_history(agent_obj)

    agent = Agent(
        task=instruction,
        llm=llm,
        browser=browser,
        tools=tools,
        use_vision=True,
        use_thinking=(thinking != "off"),
        file_system_path=str(workspace),
        available_file_paths=available_files,
        register_new_step_callback=on_step,
        register_done_callback=on_done,
        register_should_stop_callback=should_stop,
    )
    holder["agent"] = agent

    try:
        await asyncio.wait_for(agent.run(), timeout=time_limit)
    except asyncio.TimeoutError:
        # The harness watchdog will set the stop-reason; we just need to
        # land the most-recent transcript.
        pass
    finally:
        # Final dump in case the last step's callback didn't get to fire.
        try:
            dump_history(agent)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
