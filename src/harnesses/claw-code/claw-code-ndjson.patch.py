#!/usr/bin/env python3
"""Two behavioural patches to upstream claw-code, plus the compile-forced
cascade of one-line additions Rust's exhaustive pattern matching demands
once we introduce a new enum variant.

1. **MCP stdio framing** (mcp_stdio.rs) — upstream claw speaks LSP-style
   `Content-Length: N\\r\\n\\r\\n<body>` on stdio MCP transport, but the MCP
   2024-11-05 spec and every real-world stdio MCP server (Playwright-MCP,
   the Python & TS SDKs, Anthropic's filesystem server, etc.) use
   newline-delimited JSON. The two deadlock: the server writes
   `{"jsonrpc":...}\\n`, claw's `read_frame` interprets it as a header line,
   can't find the Content-Length colon/value pair, and blocks forever on
   the next read_line. We swap only `write_jsonrpc_message` /
   `read_jsonrpc_message` to newline-delimited JSON so the binary can
   actually talk to `@playwright/mcp`. `encode_frame`/`write_frame`/
   `read_frame` themselves stay intact so upstream tests still pass.

2. **Capture thinking blocks in the session transcript**
   (conversation.rs + session.rs + main.rs) — upstream claw parses
   `ThinkingDelta` SSE events but explicitly throws the content away at
   `main.rs:~6993` (`ContentBlockDelta::ThinkingDelta { .. } => { render a
   one-line terminal summary, push nothing }`). The runtime layer's
   `AssistantEvent` enum has no `ThinkingDelta` variant and the persisted
   `ContentBlock` enum has no `Thinking` variant, so even the agent's own
   reasoning is dropped by the time the session JSONL is written. We add
   `AssistantEvent::ThinkingDelta(String)` and `ContentBlock::Thinking
   { text: String }`, have the SSE handler emit the event, and have
   `build_assistant_message` flush the buffered thinking into the
   session. `to_json` / `from_json` handle the new variant so
   `agent-messages.jsonl` gets `{"type":"thinking","text":"..."}` blocks.

Adding a variant to `ContentBlock` forces every exhaustive match on it to
grow a `Thinking` arm — Rust won't compile otherwise. Those cascaded
one-liners in compact.rs (5), tools/lib.rs (1), and main.rs (3) are
mechanical compile fixes, not design decisions; the compiler catches
every omission.
"""
from __future__ import annotations

import sys
from pathlib import Path

PATH = Path("/build/claw-code/rust/crates/runtime/src/mcp_stdio.rs")
CONVERSATION_PATH = Path("/build/claw-code/rust/crates/runtime/src/conversation.rs")
SESSION_PATH = Path("/build/claw-code/rust/crates/runtime/src/session.rs")
MAIN_PATH = Path("/build/claw-code/rust/crates/rusty-claude-cli/src/main.rs")
COMPACT_PATH = Path("/build/claw-code/rust/crates/runtime/src/compact.rs")
TOOLS_PATH = Path("/build/claw-code/rust/crates/tools/src/lib.rs")

OLD_WRITE = """    pub async fn write_jsonrpc_message<T: Serialize>(&mut self, message: &T) -> io::Result<()> {
        let body = serde_json::to_vec(message)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
        self.write_frame(&body).await
    }"""

NEW_WRITE = """    pub async fn write_jsonrpc_message<T: Serialize>(&mut self, message: &T) -> io::Result<()> {
        // Patched by clawbench harness: MCP stdio spec (2024-11-05) uses
        // newline-delimited JSON, not LSP-style Content-Length framing.
        let body = serde_json::to_vec(message)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
        self.write_all(&body).await?;
        self.write_all(b"\\n").await?;
        self.flush().await
    }"""

OLD_READ = """    pub async fn read_jsonrpc_message<T: DeserializeOwned>(&mut self) -> io::Result<T> {
        let payload = self.read_frame().await?;
        serde_json::from_slice(&payload)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))
    }"""

NEW_READ = """    pub async fn read_jsonrpc_message<T: DeserializeOwned>(&mut self) -> io::Result<T> {
        // Patched by clawbench harness: expect newline-delimited JSON.
        // Skip blank lines some servers emit between messages.
        loop {
            let line = self.read_line().await?;
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            return serde_json::from_str(trimmed)
                .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error));
        }
    }"""


# ── conversation.rs: AssistantEvent + build_assistant_message ─────────

OLD_ASSISTANT_EVENT = """pub enum AssistantEvent {
    TextDelta(String),
    ToolUse {
        id: String,
        name: String,
        input: String,
    },
    Usage(TokenUsage),
    PromptCache(PromptCacheEvent),
    MessageStop,
}"""

NEW_ASSISTANT_EVENT = """pub enum AssistantEvent {
    TextDelta(String),
    // clawbench patch: capture thinking/reasoning content deltas so they
    // can be recorded in the session transcript alongside text + tool_use.
    ThinkingDelta(String),
    ToolUse {
        id: String,
        name: String,
        input: String,
    },
    Usage(TokenUsage),
    PromptCache(PromptCacheEvent),
    MessageStop,
}"""

OLD_BUILD_BODY = """    let mut text = String::new();
    let mut blocks = Vec::new();
    let mut prompt_cache_events = Vec::new();
    let mut finished = false;
    let mut usage = None;

    for event in events {
        match event {
            AssistantEvent::TextDelta(delta) => text.push_str(&delta),
            AssistantEvent::ToolUse { id, name, input } => {
                flush_text_block(&mut text, &mut blocks);
                blocks.push(ContentBlock::ToolUse { id, name, input });
            }
            AssistantEvent::Usage(value) => usage = Some(value),
            AssistantEvent::PromptCache(event) => prompt_cache_events.push(event),
            AssistantEvent::MessageStop => {
                finished = true;
            }
        }
    }

    flush_text_block(&mut text, &mut blocks);"""

NEW_BUILD_BODY = """    let mut text = String::new();
    // clawbench patch: buffer thinking deltas separately so they land in
    // their own ContentBlock rather than being merged into text or dropped.
    let mut thinking = String::new();
    let mut blocks = Vec::new();
    let mut prompt_cache_events = Vec::new();
    let mut finished = false;
    let mut usage = None;

    for event in events {
        match event {
            AssistantEvent::TextDelta(delta) => {
                if !thinking.is_empty() {
                    blocks.push(ContentBlock::Thinking { text: std::mem::take(&mut thinking) });
                }
                text.push_str(&delta);
            }
            AssistantEvent::ThinkingDelta(delta) => {
                flush_text_block(&mut text, &mut blocks);
                thinking.push_str(&delta);
            }
            AssistantEvent::ToolUse { id, name, input } => {
                flush_text_block(&mut text, &mut blocks);
                if !thinking.is_empty() {
                    blocks.push(ContentBlock::Thinking { text: std::mem::take(&mut thinking) });
                }
                blocks.push(ContentBlock::ToolUse { id, name, input });
            }
            AssistantEvent::Usage(value) => usage = Some(value),
            AssistantEvent::PromptCache(event) => prompt_cache_events.push(event),
            AssistantEvent::MessageStop => {
                finished = true;
            }
        }
    }

    flush_text_block(&mut text, &mut blocks);
    if !thinking.is_empty() {
        blocks.push(ContentBlock::Thinking { text: std::mem::take(&mut thinking) });
    }"""


# ── session.rs: add Thinking variant to ContentBlock ──────────────────

OLD_CONTENT_BLOCK = """pub enum ContentBlock {
    Text {
        text: String,
    },
    ToolUse {
        id: String,
        name: String,
        input: String,
    },
    ToolResult {
        tool_use_id: String,
        tool_name: String,
        output: String,
        is_error: bool,
    },
}"""

NEW_CONTENT_BLOCK = """pub enum ContentBlock {
    Text {
        text: String,
    },
    // clawbench patch: preserve model thinking/reasoning output in the
    // session transcript.
    Thinking {
        text: String,
    },
    ToolUse {
        id: String,
        name: String,
        input: String,
    },
    ToolResult {
        tool_use_id: String,
        tool_name: String,
        output: String,
        is_error: bool,
    },
}"""

OLD_TO_JSON_HEAD = """        match self {
            Self::Text { text } => {
                object.insert("type".to_string(), JsonValue::String("text".to_string()));
                object.insert("text".to_string(), JsonValue::String(text.clone()));
            }
            Self::ToolUse { id, name, input } => {"""

NEW_TO_JSON_HEAD = """        match self {
            Self::Text { text } => {
                object.insert("type".to_string(), JsonValue::String("text".to_string()));
                object.insert("text".to_string(), JsonValue::String(text.clone()));
            }
            Self::Thinking { text } => {
                object.insert("type".to_string(), JsonValue::String("thinking".to_string()));
                object.insert("text".to_string(), JsonValue::String(text.clone()));
            }
            Self::ToolUse { id, name, input } => {"""

OLD_FROM_JSON_HEAD = """            "text" => Ok(Self::Text {
                text: required_string(object, "text")?,
            }),
            "tool_use" => Ok(Self::ToolUse {"""

NEW_FROM_JSON_HEAD = """            "text" => Ok(Self::Text {
                text: required_string(object, "text")?,
            }),
            "thinking" => Ok(Self::Thinking {
                text: required_string(object, "text")?,
            }),
            "tool_use" => Ok(Self::ToolUse {"""


# ── compact.rs: 5 exhaustive matches on ContentBlock need a Thinking arm ──

OLD_COMPACT_TOOLNAMES = """        .filter_map(|block| match block {
            ContentBlock::ToolUse { name, .. } => Some(name.as_str()),
            ContentBlock::ToolResult { tool_name, .. } => Some(tool_name.as_str()),
            ContentBlock::Text { .. } => None,
        })"""

NEW_COMPACT_TOOLNAMES = """        .filter_map(|block| match block {
            ContentBlock::ToolUse { name, .. } => Some(name.as_str()),
            ContentBlock::ToolResult { tool_name, .. } => Some(tool_name.as_str()),
            ContentBlock::Text { .. } | ContentBlock::Thinking { .. } => None,
        })"""

OLD_COMPACT_SUMMARIZE = """fn summarize_block(block: &ContentBlock) -> String {
    let raw = match block {
        ContentBlock::Text { text } => text.clone(),
        ContentBlock::ToolUse { name, input, .. } => format!("tool_use {name}({input})"),
        ContentBlock::ToolResult {
            tool_name,
            output,
            is_error,
            ..
        } => format!(
            "tool_result {tool_name}: {}{output}",
            if *is_error { "error " } else { "" }
        ),
    };
    truncate_summary(&raw, 160)
}"""

NEW_COMPACT_SUMMARIZE = """fn summarize_block(block: &ContentBlock) -> String {
    let raw = match block {
        ContentBlock::Text { text } => text.clone(),
        ContentBlock::Thinking { text } => format!("thinking: {text}"),
        ContentBlock::ToolUse { name, input, .. } => format!("tool_use {name}({input})"),
        ContentBlock::ToolResult {
            tool_name,
            output,
            is_error,
            ..
        } => format!(
            "tool_result {tool_name}: {}{output}",
            if *is_error { "error " } else { "" }
        ),
    };
    truncate_summary(&raw, 160)
}"""

OLD_COMPACT_FILES = """        .map(|block| match block {
            ContentBlock::Text { text } => text.as_str(),
            ContentBlock::ToolUse { input, .. } => input.as_str(),
            ContentBlock::ToolResult { output, .. } => output.as_str(),
        })
        .flat_map(extract_file_candidates)"""

NEW_COMPACT_FILES = """        .map(|block| match block {
            ContentBlock::Text { text } | ContentBlock::Thinking { text } => text.as_str(),
            ContentBlock::ToolUse { input, .. } => input.as_str(),
            ContentBlock::ToolResult { output, .. } => output.as_str(),
        })
        .flat_map(extract_file_candidates)"""

OLD_COMPACT_FIRSTTEXT = """fn first_text_block(message: &ConversationMessage) -> Option<&str> {
    message.blocks.iter().find_map(|block| match block {
        ContentBlock::Text { text } if !text.trim().is_empty() => Some(text.as_str()),
        ContentBlock::ToolUse { .. }
        | ContentBlock::ToolResult { .. }
        | ContentBlock::Text { .. } => None,
    })
}"""

NEW_COMPACT_FIRSTTEXT = """fn first_text_block(message: &ConversationMessage) -> Option<&str> {
    message.blocks.iter().find_map(|block| match block {
        ContentBlock::Text { text } if !text.trim().is_empty() => Some(text.as_str()),
        ContentBlock::ToolUse { .. }
        | ContentBlock::ToolResult { .. }
        | ContentBlock::Text { .. }
        | ContentBlock::Thinking { .. } => None,
    })
}"""

OLD_COMPACT_TOKENS = """        .map(|block| match block {
            ContentBlock::Text { text } => text.len() / 4 + 1,
            ContentBlock::ToolUse { name, input, .. } => (name.len() + input.len()) / 4 + 1,
            ContentBlock::ToolResult {
                tool_name, output, ..
            } => (tool_name.len() + output.len()) / 4 + 1,
        })
        .sum()"""

NEW_COMPACT_TOKENS = """        .map(|block| match block {
            ContentBlock::Text { text } | ContentBlock::Thinking { text } => text.len() / 4 + 1,
            ContentBlock::ToolUse { name, input, .. } => (name.len() + input.len()) / 4 + 1,
            ContentBlock::ToolResult {
                tool_name, output, ..
            } => (tool_name.len() + output.len()) / 4 + 1,
        })
        .sum()"""


# ── tools/lib.rs: skip Thinking blocks when rebuilding API input ──────
# Anthropic's InputContentBlock has no Thinking variant — extended
# thinking content is model→client only and must not be echoed back on
# the next turn unless interleaved-thinking beta is enabled. Drop it.

OLD_TOOLS_BUILD_INPUT = """            let content = message
                .blocks
                .iter()
                .map(|block| match block {
                    ContentBlock::Text { text } => InputContentBlock::Text { text: text.clone() },
                    ContentBlock::ToolUse { id, name, input } => InputContentBlock::ToolUse {
                        id: id.clone(),
                        name: name.clone(),
                        input: serde_json::from_str(input)
                            .unwrap_or_else(|_| serde_json::json!({ "raw": input })),
                    },
                    ContentBlock::ToolResult {
                        tool_use_id,
                        output,
                        is_error,
                        ..
                    } => InputContentBlock::ToolResult {
                        tool_use_id: tool_use_id.clone(),
                        content: vec![ToolResultContentBlock::Text {
                            text: output.clone(),
                        }],
                        is_error: *is_error,
                    },
                })
                .collect::<Vec<_>>();"""

NEW_TOOLS_BUILD_INPUT = """            let content = message
                .blocks
                .iter()
                .filter_map(|block| match block {
                    ContentBlock::Text { text } => Some(InputContentBlock::Text { text: text.clone() }),
                    // clawbench patch: Thinking is captured in the session
                    // transcript but not replayed to the API — Anthropic has
                    // no InputContentBlock::Thinking and echoing the text
                    // back would double-count reasoning tokens.
                    ContentBlock::Thinking { .. } => None,
                    ContentBlock::ToolUse { id, name, input } => Some(InputContentBlock::ToolUse {
                        id: id.clone(),
                        name: name.clone(),
                        input: serde_json::from_str(input)
                            .unwrap_or_else(|_| serde_json::json!({ "raw": input })),
                    }),
                    ContentBlock::ToolResult {
                        tool_use_id,
                        output,
                        is_error,
                        ..
                    } => Some(InputContentBlock::ToolResult {
                        tool_use_id: tool_use_id.clone(),
                        content: vec![ToolResultContentBlock::Text {
                            text: output.clone(),
                        }],
                        is_error: *is_error,
                    }),
                })
                .collect::<Vec<_>>();"""


# ── main.rs: SSE handler pushes ThinkingDelta ─────────────────────────

OLD_MAIN_DUMP = """        for block in &message.blocks {
            match block {
                ContentBlock::Text { text } => lines.push(text.clone()),
                ContentBlock::ToolUse { id, name, input } => {
                    lines.push(format!("[tool_use id={id} name={name}] {input}"));
                }
                ContentBlock::ToolResult {
                    tool_use_id,
                    tool_name,
                    output,
                    is_error,
                } => {
                    lines.push(format!(
                        "[tool_result id={tool_use_id} name={tool_name} error={is_error}] {output}"
                    ));
                }
            }
        }"""

NEW_MAIN_DUMP = """        for block in &message.blocks {
            match block {
                ContentBlock::Text { text } => lines.push(text.clone()),
                ContentBlock::Thinking { text } => lines.push(format!("[thinking] {text}")),
                ContentBlock::ToolUse { id, name, input } => {
                    lines.push(format!("[tool_use id={id} name={name}] {input}"));
                }
                ContentBlock::ToolResult {
                    tool_use_id,
                    tool_name,
                    output,
                    is_error,
                } => {
                    lines.push(format!(
                        "[tool_result id={tool_use_id} name={tool_name} error={is_error}] {output}"
                    ));
                }
            }
        }"""

OLD_MAIN_MD = """        for block in &message.blocks {
            match block {
                ContentBlock::Text { text } => {
                    let trimmed = text.trim_end();
                    if !trimmed.is_empty() {
                        lines.push(trimmed.to_string());
                        lines.push(String::new());
                    }
                }
                ContentBlock::ToolUse { id, name, input } => {"""

NEW_MAIN_MD = """        for block in &message.blocks {
            match block {
                ContentBlock::Text { text } => {
                    let trimmed = text.trim_end();
                    if !trimmed.is_empty() {
                        lines.push(trimmed.to_string());
                        lines.push(String::new());
                    }
                }
                ContentBlock::Thinking { text } => {
                    let trimmed = text.trim_end();
                    if !trimmed.is_empty() {
                        lines.push(format!("> _thinking:_ {trimmed}"));
                        lines.push(String::new());
                    }
                }
                ContentBlock::ToolUse { id, name, input } => {"""

OLD_MAIN_TO_INPUT = """                .map(|block| match block {
                    ContentBlock::Text { text } => InputContentBlock::Text { text: text.clone() },
                    ContentBlock::ToolUse { id, name, input } => InputContentBlock::ToolUse {
                        id: id.clone(),
                        name: name.clone(),
                        input: serde_json::from_str(input)
                            .unwrap_or_else(|_| serde_json::json!({ "raw": input })),
                    },
                    ContentBlock::ToolResult {
                        tool_use_id,
                        output,
                        is_error,
                        ..
                    } => InputContentBlock::ToolResult {
                        tool_use_id: tool_use_id.clone(),
                        content: vec![ToolResultContentBlock::Text {
                            text: output.clone(),
                        }],
                        is_error: *is_error,
                    },
                })
                .collect::<Vec<_>>();
            (!content.is_empty()).then(|| InputMessage {"""

NEW_MAIN_TO_INPUT = """                .filter_map(|block| match block {
                    ContentBlock::Text { text } => Some(InputContentBlock::Text { text: text.clone() }),
                    // clawbench patch: see tools/lib.rs — Thinking is session-only.
                    ContentBlock::Thinking { .. } => None,
                    ContentBlock::ToolUse { id, name, input } => Some(InputContentBlock::ToolUse {
                        id: id.clone(),
                        name: name.clone(),
                        input: serde_json::from_str(input)
                            .unwrap_or_else(|_| serde_json::json!({ "raw": input })),
                    }),
                    ContentBlock::ToolResult {
                        tool_use_id,
                        output,
                        is_error,
                        ..
                    } => Some(InputContentBlock::ToolResult {
                        tool_use_id: tool_use_id.clone(),
                        content: vec![ToolResultContentBlock::Text {
                            text: output.clone(),
                        }],
                        is_error: *is_error,
                    }),
                })
                .collect::<Vec<_>>();
            (!content.is_empty()).then(|| InputMessage {"""

OLD_MAIN_THINK = """                    ContentBlockDelta::ThinkingDelta { .. } => {
                        if !block_has_thinking_summary {
                            render_thinking_block_summary(out, None, false)?;
                            block_has_thinking_summary = true;
                        }
                    }"""

NEW_MAIN_THINK = """                    ContentBlockDelta::ThinkingDelta { thinking } => {
                        if !block_has_thinking_summary {
                            render_thinking_block_summary(out, None, false)?;
                            block_has_thinking_summary = true;
                        }
                        // clawbench patch: capture the actual thinking text
                        // so `build_assistant_message` can flush it into a
                        // ContentBlock::Thinking in the session transcript.
                        events.push(AssistantEvent::ThinkingDelta(thinking));
                    }"""


def _patch(path: Path, patches: list[tuple[str, str, str]]) -> int:
    src = path.read_text()
    for old, new, label in patches:
        if old not in src:
            print(f"ERROR: could not find {label} in {path.name}", file=sys.stderr)
            return 1
        if src.count(old) > 1:
            print(f"ERROR: {label} matched >1 times in {path.name}", file=sys.stderr)
            return 1
        src = src.replace(old, new, 1)
        print(f"patched {label} in {path.name}")
    path.write_text(src)
    return 0


def main() -> int:
    steps = [
        (PATH, [
            (OLD_WRITE, NEW_WRITE, "write_jsonrpc_message"),
            (OLD_READ, NEW_READ, "read_jsonrpc_message"),
        ]),
        (CONVERSATION_PATH, [
            (OLD_ASSISTANT_EVENT, NEW_ASSISTANT_EVENT, "AssistantEvent enum"),
            (OLD_BUILD_BODY, NEW_BUILD_BODY, "build_assistant_message body"),
        ]),
        (SESSION_PATH, [
            (OLD_CONTENT_BLOCK, NEW_CONTENT_BLOCK, "ContentBlock enum"),
            (OLD_TO_JSON_HEAD, NEW_TO_JSON_HEAD, "ContentBlock::to_json thinking"),
            (OLD_FROM_JSON_HEAD, NEW_FROM_JSON_HEAD, "ContentBlock::from_json thinking"),
        ]),
        (COMPACT_PATH, [
            (OLD_COMPACT_TOOLNAMES, NEW_COMPACT_TOOLNAMES, "compact tool-name filter"),
            (OLD_COMPACT_SUMMARIZE, NEW_COMPACT_SUMMARIZE, "compact summarize_block"),
            (OLD_COMPACT_FILES, NEW_COMPACT_FILES, "compact file extraction"),
            (OLD_COMPACT_FIRSTTEXT, NEW_COMPACT_FIRSTTEXT, "compact first_text_block"),
            (OLD_COMPACT_TOKENS, NEW_COMPACT_TOKENS, "compact token estimator"),
        ]),
        (TOOLS_PATH, [
            (OLD_TOOLS_BUILD_INPUT, NEW_TOOLS_BUILD_INPUT, "tools session->input skip Thinking"),
        ]),
        (MAIN_PATH, [
            (OLD_MAIN_DUMP, NEW_MAIN_DUMP, "main.rs session dump formatter"),
            (OLD_MAIN_MD, NEW_MAIN_MD, "main.rs markdown exporter"),
            (OLD_MAIN_TO_INPUT, NEW_MAIN_TO_INPUT, "main.rs session->input skip Thinking"),
            (OLD_MAIN_THINK, NEW_MAIN_THINK, "SSE ThinkingDelta -> AssistantEvent"),
        ]),
    ]
    for path, patches in steps:
        rc = _patch(path, patches)
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
