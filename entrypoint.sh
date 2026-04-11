#!/bin/bash
set -e

# Ensure /data exists for recording output and diagnostic logs
mkdir -p /data

# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
sleep 1

# Start the server
cd /app/extension-server
uv run uvicorn server:app --host 0.0.0.0 --port 7878 &
sleep 1

# Start Chrome with extension (realistic profile to reduce bot detection)
mkdir -p /tmp/chrome-profile/Default

cat > /tmp/chrome-profile/Default/Preferences <<'PREFS'
{
  "credentials_enable_service": false,
  "profile": {
    "password_manager_enabled": false,
    "password_manager_leak_detection": false,
    "name": "Default",
    "created_by_version": "131.0.6778.139",
    "content_settings": {
      "exceptions": {}
    }
  },
  "browser": {
    "has_seen_welcome_page": true,
    "check_default_browser": false,
    "window_placement": {
      "bottom": 1080,
      "left": 0,
      "maximized": false,
      "right": 1920,
      "top": 0,
      "work_area_bottom": 1080,
      "work_area_left": 0,
      "work_area_right": 1920,
      "work_area_top": 0
    }
  },
  "dns_prefetching": {
    "enabled": true
  },
  "safebrowsing": {
    "enabled": true
  },
  "search": {
    "suggest_enabled": true
  },
  "translate": {
    "enabled": false
  },
  "intl": {
    "accept_languages": "en-US,en"
  },
  "distribution": {
    "import_bookmarks": false,
    "skip_first_run_ui": true
  }
}
PREFS

cat > /tmp/chrome-profile/Default/Bookmarks <<'BOOKMARKS'
{
  "checksum": "b5f7e1a2c3d4e5f6a7b8c9d0e1f2a3b4",
  "roots": {
    "bookmark_bar": {
      "children": [
        {
          "date_added": "13350000000000000",
          "date_last_used": "0",
          "guid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "name": "Google",
          "type": "url",
          "url": "https://www.google.com/"
        },
        {
          "date_added": "13350000000000000",
          "date_last_used": "0",
          "guid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
          "name": "YouTube",
          "type": "url",
          "url": "https://www.youtube.com/"
        },
        {
          "date_added": "13350000000000000",
          "date_last_used": "0",
          "guid": "c3d4e5f6-a7b8-9012-cdef-123456789012",
          "name": "Wikipedia",
          "type": "url",
          "url": "https://en.wikipedia.org/"
        }
      ],
      "date_added": "13350000000000000",
      "date_last_used": "0",
      "date_modified": "13350000000000000",
      "guid": "00000000-0000-4000-a000-000000000001",
      "name": "Bookmarks bar",
      "type": "folder"
    },
    "other": {
      "children": [],
      "date_added": "13350000000000000",
      "date_last_used": "0",
      "date_modified": "0",
      "guid": "00000000-0000-4000-a000-000000000002",
      "name": "Other bookmarks",
      "type": "folder"
    },
    "synced": {
      "children": [],
      "date_added": "13350000000000000",
      "date_last_used": "0",
      "date_modified": "0",
      "guid": "00000000-0000-4000-a000-000000000003",
      "name": "Mobile bookmarks",
      "type": "folder"
    }
  },
  "version": 1
}
BOOKMARKS

cat > /tmp/chrome-profile/'Local State' <<'LOCALSTATE'
{
  "browser": {
    "enabled_labs_experiments": []
  },
  "profile": {
    "info_cache": {
      "Default": {
        "active_time": 1710000000,
        "is_consented_primary_account": false,
        "name": "Person 1"
      }
    }
  },
  "user_experience_metrics": {
    "reporting_enabled": false
  }
}
LOCALSTATE

chromium \
  --window-size=1920,1080 \
  --window-position=0,0 \
  --no-first-run \
  --disable-default-apps \
  --no-sandbox \
  --disable-infobars \
  --disable-dev-shm-usage \
  --disable-blink-features=AutomationControlled \
  --use-gl=angle --use-angle=swiftshader \
  --enable-unsafe-swiftshader \
  --enable-webgl \
  --password-store=basic \
  --use-mock-keychain \
  --disable-sync \
  --disable-features=PasswordLeakDetection,PasswordManager \
  --user-data-dir=/tmp/chrome-profile \
  --remote-debugging-port=9222 \
  --remote-debugging-address=127.0.0.1 \
  --remote-allow-origins=* \
  --load-extension=/app/chrome-extension \
  --disable-extensions-except=/app/chrome-extension \
  about:blank &

# Forward CDP port to all interfaces
sleep 2
socat TCP-LISTEN:9223,fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:9222 &

# Human mode: expose display via noVNC, wait for VNC disconnect or eval match
if [ "$HUMAN_MODE" = "1" ]; then
  echo "Starting human mode with noVNC..."

  # Start x11vnc with disconnect/reconnect hooks
  x11vnc -display :99 -nopw -shared -forever -rfbport 5900 -xkb \
    -gone "touch /data/.vnc-disconnected" \
    -afteraccept "rm -f /data/.vnc-disconnected" &
  sleep 1

  # Start noVNC websocket proxy (browser-based VNC client on port 6080)
  /opt/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 6080 &
  sleep 1

  echo "============================================"
  echo "noVNC ready: http://localhost:6080/vnc.html"
  echo "============================================"
  if [ -n "$INSTRUCTION" ]; then
    echo ""
    echo "TASK: $INSTRUCTION"
    echo ""
  fi

  # Human watchdog: no idle detection (humans pause to think)
  MAX_WAIT=${TIME_LIMIT_S:-1800}
  ELAPSED=0
  DISCONNECT_WAIT=0
  STOP_REASON=""

  while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
    sleep 5
    ELAPSED=$((ELAPSED + 5))

    # Check if eval interceptor matched
    if [ -f /data/.stop-requested ]; then
      echo "Stop requested by server (eval matched)."
      STOP_REASON="eval_matched"
      break
    fi

    # Check if VNC client disconnected (with 15s grace period for reconnect)
    if [ -f /data/.vnc-disconnected ]; then
      DISCONNECT_WAIT=$((DISCONNECT_WAIT + 5))
      if [ "$DISCONNECT_WAIT" -ge 15 ]; then
        echo "VNC client disconnected for ${DISCONNECT_WAIT}s, assuming done."
        STOP_REASON="vnc_disconnected"
        break
      fi
    else
      DISCONNECT_WAIT=0
    fi
  done

  if [ -z "$STOP_REASON" ]; then
    echo "Time limit (${MAX_WAIT}s) exceeded."
    STOP_REASON="time_limit_exceeded"
  fi

  echo "$STOP_REASON" > /data/.stop-reason

  # Finalize bookkeeping (eval promotion, etc.) — recording keeps running
  curl -sf -X POST http://localhost:7878/api/stop || true
  rm -f /data/.stop-requested /data/.vnc-disconnected

  # Grace period: keep recording for 15s to capture end state
  echo "Human finished, recording grace period (15s)..."
  sleep 15

  # Stop recording
  echo "Stopping recording..."
  curl -sf -X POST http://localhost:7878/api/stop-recording || true
  sleep 2
  echo "Done."
  exit 0
fi

# HARNESS is baked into the image via ENV in Dockerfile.{openclaw,opencode}.
# clawbench-base has no HARNESS set — agent-mode runs on the base image will
# hit the "harness_not_installed" guard below.
HARNESS="${HARNESS:-openclaw}"
echo "Harness: $HARNESS"

# If no INSTRUCTION provided, skip the agent and keep container alive for external use
if [ -z "$INSTRUCTION" ]; then
  echo "No INSTRUCTION set, running in manual mode (no agent)."
  wait -n
  exit 0
fi

# Agent mode requires an actual harness binary in the image. The base image
# has neither — users should layer clawbench-openclaw or clawbench-opencode
# on top for agent runs.
case "$HARNESS" in
  openclaw)
    if ! command -v openclaw >/dev/null 2>&1; then
      echo "ERROR: HARNESS=openclaw but the 'openclaw' binary is not installed in this image." >&2
      echo "       Use the clawbench-openclaw image (or build it first) for agent runs." >&2
      echo "harness_not_installed" > /data/.stop-reason
      exit 1
    fi
    ;;
  opencode)
    if ! command -v opencode >/dev/null 2>&1; then
      echo "ERROR: HARNESS=opencode but the 'opencode' binary is not installed in this image." >&2
      echo "       Use the clawbench-opencode image (or build it first) for agent runs." >&2
      echo "harness_not_installed" > /data/.stop-reason
      exit 1
    fi
    ;;
  *)
    echo "ERROR: unknown HARNESS='$HARNESS' (expected 'openclaw' or 'opencode')" >&2
    echo "harness_not_installed" > /data/.stop-reason
    exit 1
    ;;
esac

# Copy /my-info/ into the workspace so the agent can access it via ./my-info/
WORKSPACE=/root/workspace
mkdir -p "$WORKSPACE"
if [ -d /my-info ]; then
  cp -r /my-info "$WORKSPACE/my-info"
  echo "Copied /my-info to $WORKSPACE/my-info"
fi

# Wait for Chrome CDP to be ready (harness-agnostic)
echo "Waiting for Chrome CDP..."
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:9222/json/version > /dev/null 2>&1; then
    echo "Chrome CDP ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Chrome CDP not ready after 30s, aborting"
    echo "chrome_cdp_timeout" > /data/.stop-reason
    exit 1
  fi
  sleep 1
done

GATEWAY_PID=""
if [ "$HARNESS" = "opencode" ]; then
  # --- opencode harness ---
  /setup-opencode.sh

  cd "$WORKSPACE"
  echo "Starting opencode agent from $WORKSPACE..."
  # --format json writes a JSON event stream to stdout. This stream is useful
  # for live progress monitoring but is LOSSY for reasoning/thinking content —
  # reasoning parts only appear in the on-disk session, not the live stream.
  # We capture the stream here to extract the sessionID for the post-run
  # `opencode export` step (see cleanup block below), which produces the
  # full transcript (including reasoning) as /data/agent-messages.jsonl.
  opencode run --format json --model "clawbench/$MODEL_NAME" -- "$INSTRUCTION" \
    > /data/opencode-stream.jsonl 2> /data/agent.log &
  AGENT_PID=$!
  sleep 3

  if ! kill -0 $AGENT_PID 2>/dev/null; then
    echo "ERROR: opencode process died on startup. Log:"
    cat /data/agent.log
    echo "opencode_failed" > /data/.stop-reason
    exit 1
  fi
  echo "opencode agent running (pid=$AGENT_PID)"
else
  # --- openclaw harness (default) ---

  # Generate a shared gateway token so gateway and agent can authenticate
  OPENCLAW_GATEWAY_TOKEN="$(head -c 32 /dev/urandom | od -A n -t x1 | tr -d ' \n')"
  export OPENCLAW_GATEWAY_TOKEN

  # Generate OpenClaw config from env vars
  /setup-openclaw.sh

  # Start OpenClaw gateway (log to /data for post-mortem debugging)
  openclaw gateway run > /data/gateway.log 2>&1 &
  GATEWAY_PID=$!
  sleep 3

  # Check gateway is alive
  if ! kill -0 $GATEWAY_PID 2>/dev/null; then
    echo "ERROR: OpenClaw gateway died on startup. Log:"
    cat /data/gateway.log
    echo "gateway_failed" > /data/.stop-reason
    exit 1
  fi
  echo "OpenClaw gateway running (pid=$GATEWAY_PID)"

  # Run the agent from workspace directory (where my-info/ lives)
  echo "Starting OpenClaw agent from $WORKSPACE..."
  TIMEOUT_MS=$(( ${TIME_LIMIT_S:-1800} * 1000 ))
  AGENT_CMD=(openclaw agent --session-id clawbench --message "$INSTRUCTION" --thinking "${THINKING_LEVEL:-medium}" --timeout "$TIMEOUT_MS" --local)
  echo "Agent command: ${AGENT_CMD[*]}"
  if [ -n "$TEMPERATURE" ]; then
    AGENT_CMD+=(--temperature "$TEMPERATURE")
  fi
  if [ -n "$MAX_TOKENS" ]; then
    AGENT_CMD+=(--max-tokens "$MAX_TOKENS")
  fi
  cd "$WORKSPACE"
  "${AGENT_CMD[@]}" > /data/agent.log 2>&1 &
  AGENT_PID=$!
fi

# Watchdog: wait for agent activity, then detect idle (no new actions for 300s)
IDLE_THRESHOLD=300
MAX_WAIT=${TIME_LIMIT_S:-1800}
ELAPSED=0
LAST_SIZE=0
IDLE=0
STOP_REASON=""

while kill -0 $AGENT_PID 2>/dev/null && [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  sleep 5
  ELAPSED=$((ELAPSED + 5))

  # Check if server requested stop (eval interceptor matched)
  if [ -f /data/.stop-requested ]; then
    echo "Stop requested by server (eval matched), killing agent."
    STOP_REASON="eval_matched"
    break
  fi

  CURRENT_SIZE=$(wc -c < /data/actions.jsonl 2>/dev/null || echo 0)

  if [ "$CURRENT_SIZE" -gt 0 ] && [ "$CURRENT_SIZE" -eq "$LAST_SIZE" ]; then
    IDLE=$((IDLE + 5))
    if [ "$IDLE" -ge "$IDLE_THRESHOLD" ]; then
      echo "Agent idle for ${IDLE_THRESHOLD}s, assuming done."
      STOP_REASON="agent_idle"
      break
    fi
  else
    IDLE=0
  fi
  LAST_SIZE=$CURRENT_SIZE
done

# Determine stop reason if not set (loop exited without breaking)
if [ -z "$STOP_REASON" ]; then
  if ! kill -0 $AGENT_PID 2>/dev/null; then
    STOP_REASON="agent_exited"
  else
    echo "Time limit (${MAX_WAIT}s) exceeded, killing agent."
    STOP_REASON="time_limit_exceeded"
  fi
fi

echo "$STOP_REASON" > /data/.stop-reason

# Kill agent and (for openclaw) gateway processes
kill $AGENT_PID 2>/dev/null || true
if [ -n "$GATEWAY_PID" ]; then
  kill $GATEWAY_PID 2>/dev/null || true
fi
if [ "$HARNESS" = "opencode" ]; then
  pkill -f "opencode" 2>/dev/null || true
  pkill -f "chrome-devtools-mcp" 2>/dev/null || true
else
  pkill -f "openclaw" 2>/dev/null || true
fi
sleep 2

# Write the agent transcript to /data/agent-messages.jsonl (harness-specific).
if [ "$HARNESS" = "openclaw" ]; then
  # openclaw writes its own JSONL session file; copy it out.
  cp /root/.openclaw/agents/main/sessions/clawbench.jsonl /data/agent-messages.jsonl 2>/dev/null || true
else
  # opencode: the live --format json stream is LOSSY (no reasoning parts), so
  # export the on-disk session via `opencode export <sessionID>` which yields
  # the full transcript including reasoning/thinking content. Convert the
  # hierarchical export to JSONL (one line per session-info / message) so the
  # file extension contract holds.
  SESSION_ID=$(python3 -c '
import json
try:
    for line in open("/data/opencode-stream.jsonl"):
        line = line.strip()
        if not line:
            continue
        sid = json.loads(line).get("sessionID")
        if sid:
            print(sid)
            break
except Exception:
    pass
' 2>/dev/null)
  if [ -n "$SESSION_ID" ]; then
    echo "Exporting opencode session $SESSION_ID..."
    opencode export "$SESSION_ID" > /data/opencode-export.json 2>> /data/agent.log || true
    # Translate the opencode export into the same JSONL schema openclaw uses.
    # This way downstream consumers see a unified shape (session → model_change →
    # thinking_level_change → custom → messages with role ∈ {user, assistant,
    # toolResult}) regardless of which harness produced the transcript.
    python3 -c '
import json, os, secrets
from datetime import datetime, timezone

def iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def new_id():
    return secrets.token_hex(4)

def to_text(v):
    if v is None: return ""
    if isinstance(v, str): return v
    try:
        return json.dumps(v)
    except Exception:
        return str(v)

try:
    with open("/data/opencode-export.json") as f:
        doc = json.load(f)
except Exception as e:
    print(f"opencode export parse failed: {e}")
    raise SystemExit(0)

info = doc.get("info", {})
session_created_ms = info.get("time", {}).get("created") or 0
directory = info.get("directory", "/root/workspace")

# Find model id by scanning for the first assistant message
model_id = os.environ.get("MODEL_NAME", "unknown")
for m in doc.get("messages", []):
    if m.get("info", {}).get("role") == "assistant":
        mid = m.get("info", {}).get("modelID")
        if mid:
            model_id = mid
        break

api_type = os.environ.get("API_TYPE", "openai-completions")
thinking = os.environ.get("THINKING_LEVEL") or "medium"

with open("/data/agent-messages.jsonl", "w") as out:
    # --- session header (no id chain — openclaw emits it like this) ---
    out.write(json.dumps({
        "type": "session",
        "version": 3,
        "id": "clawbench",
        "timestamp": iso(session_created_ms),
        "cwd": directory,
    }) + "\n")

    # --- DAG: model_change (parentId=null) → thinking_level_change → custom → messages ---
    last_id = None
    ts_ms = session_created_ms + 1

    mc_id = new_id()
    out.write(json.dumps({
        "type": "model_change",
        "id": mc_id,
        "parentId": last_id,
        "timestamp": iso(ts_ms),
        "provider": "api",
        "modelId": model_id,
    }) + "\n")
    last_id = mc_id
    ts_ms += 1

    tl_id = new_id()
    out.write(json.dumps({
        "type": "thinking_level_change",
        "id": tl_id,
        "parentId": last_id,
        "timestamp": iso(ts_ms),
        "thinkingLevel": thinking,
    }) + "\n")
    last_id = tl_id
    ts_ms += 1

    cs_id = new_id()
    out.write(json.dumps({
        "type": "custom",
        "customType": "model-snapshot",
        "data": {
            "timestamp": ts_ms,
            "provider": "api",
            "modelApi": api_type,
            "modelId": model_id,
        },
        "id": cs_id,
        "parentId": last_id,
        "timestamp": iso(ts_ms),
    }) + "\n")
    last_id = cs_id

    # --- message events ---
    for msg in doc.get("messages", []):
        minfo = msg.get("info", {})
        role = minfo.get("role")
        parts = msg.get("parts", [])
        msg_ts_ms = (minfo.get("time") or {}).get("created") or ts_ms

        if role == "user":
            texts = [p.get("text", "") for p in parts if p.get("type") == "text"]
            content = [{"type": "text", "text": t} for t in texts]
            if not content:
                continue
            ev_id = new_id()
            out.write(json.dumps({
                "type": "message",
                "id": ev_id,
                "parentId": last_id,
                "timestamp": iso(msg_ts_ms),
                "message": {"role": "user", "content": content},
            }) + "\n")
            last_id = ev_id

        elif role == "assistant":
            content = []
            tool_parts = []
            for p in parts:
                pt = p.get("type")
                if pt == "reasoning":
                    content.append({
                        "type": "thinking",
                        "thinking": p.get("text", ""),
                        "thinkingSignature": "reasoning",
                    })
                elif pt == "text":
                    content.append({
                        "type": "text",
                        "text": p.get("text", ""),
                    })
                elif pt == "tool":
                    state = p.get("state", {}) or {}
                    content.append({
                        "type": "toolCall",
                        "id": p.get("callID", ""),
                        "name": p.get("tool", ""),
                        "arguments": state.get("input", {}) or {},
                    })
                    tool_parts.append(p)
                # step-start / step-finish: dropped (openclaw has no analog)

            if content:
                ev_id = new_id()
                out.write(json.dumps({
                    "type": "message",
                    "id": ev_id,
                    "parentId": last_id,
                    "timestamp": iso(msg_ts_ms),
                    "message": {"role": "assistant", "content": content},
                }) + "\n")
                last_id = ev_id

            # One toolResult message per toolCall, in order.
            for p in tool_parts:
                state = p.get("state", {}) or {}
                is_error = state.get("status") == "error"
                raw_output = state.get("error") if is_error else state.get("output")
                output_text = to_text(raw_output)
                tool_end_ms = (state.get("time") or {}).get("end") or msg_ts_ms
                ev_id = new_id()
                out.write(json.dumps({
                    "type": "message",
                    "id": ev_id,
                    "parentId": last_id,
                    "timestamp": iso(tool_end_ms),
                    "message": {
                        "role": "toolResult",
                        "toolCallId": p.get("callID", ""),
                        "toolName": p.get("tool", ""),
                        "content": [{"type": "text", "text": output_text}],
                        "isError": is_error,
                        "timestamp": tool_end_ms,
                    },
                }) + "\n")
                last_id = ev_id
        # other roles (none expected from opencode) are skipped
' 2>> /data/agent.log || true
    rm -f /data/opencode-export.json
  fi
  # Fallback: if the export failed or produced nothing, fall back to the raw
  # live stream so the run isn't left with an empty transcript.
  if [ ! -s /data/agent-messages.jsonl ]; then
    echo "opencode export empty or missing; falling back to live stream." >> /data/agent.log
    cp /data/opencode-stream.jsonl /data/agent-messages.jsonl 2>/dev/null || true
  fi
  rm -f /data/opencode-stream.jsonl
fi

# Finalize bookkeeping (eval promotion, etc.) — recording keeps running
curl -sf -X POST http://localhost:7878/api/stop || true

# Clean up internal marker (created by /api/stop)
rm -f /data/.stop-requested

# Grace period: keep recording for 15s after agent is killed to capture end result
echo "Agent finished, recording grace period (15s)..."
sleep 15

# Stop recording
echo "Stopping recording..."
curl -sf -X POST http://localhost:7878/api/stop-recording || true
sleep 2
echo "Done."
