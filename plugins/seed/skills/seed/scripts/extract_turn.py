#!/usr/bin/env python3
"""Extract the last user-prompt → assistant-response turn from a Claude Code
transcript and emit a markdown block.

Usage (invoked by Stop hook):
    python3 extract_turn.py \
        --transcript /path/to/session.jsonl \
        --session-id abc123 \
        --timestamp "2026-04-20 23:42:30" \
        --cwd /Users/.../project \
        --session-file /path/to/sessions/abc123.md

Behavior:
- Reads the transcript JSONL
- Finds the most recent "real user prompt" (type=user, content is string,
  and does NOT have toolUseResult)
- Captures everything from that prompt forward: assistant text + tool_use
  blocks (names only, arguments summarized)
- De-dupes by the user prompt's uuid — if the session file already contains
  that uuid, exit silently (Stop hook fires after every assistant turn, so
  we can re-run safely)
- Appends a markdown block to the session file
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def message_content_text(msg: dict) -> str:
    """Extract plain text from a message.content that may be str or list of blocks."""
    content = msg.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def is_real_user_prompt(entry: dict) -> bool:
    """True if this is a user message typed by the human, not a tool result."""
    if entry.get("type") != "user":
        return False
    if entry.get("isSidechain"):
        return False
    if entry.get("toolUseResult"):
        return False
    if entry.get("isMeta"):
        return False
    msg = entry.get("message", {}) or {}
    content = msg.get("content")
    # If content is a list and contains only tool_result blocks, it's a tool response
    if isinstance(content, list):
        has_text = any(
            isinstance(b, dict) and b.get("type") in ("text",) for b in content
        )
        has_tool_result = any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        )
        if has_tool_result and not has_text:
            return False
    return True


def extract_tool_uses(entry: dict) -> list[dict]:
    """Extract {name, input_summary} for each tool_use block in an assistant message."""
    content = entry.get("message", {}).get("content", [])
    if not isinstance(content, list):
        return []
    tools = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = block.get("name", "?")
            inp = block.get("input", {}) or {}
            summary = summarize_tool_input(name, inp)
            tools.append({"name": name, "summary": summary})
    return tools


def summarize_tool_input(name: str, inp: dict) -> str:
    """Short one-line summary of important input fields, without dumping full args."""
    if name in ("Read", "Glob"):
        return inp.get("file_path") or inp.get("pattern") or ""
    if name == "Grep":
        p = inp.get("pattern", "")
        path = inp.get("path", "")
        return f"{p!r} in {path}" if path else repr(p)
    if name in ("Edit", "Write"):
        return inp.get("file_path", "")
    if name == "Bash":
        cmd = inp.get("command", "")
        # first 120 chars of command
        return cmd[:120] + ("…" if len(cmd) > 120 else "")
    if name == "Skill":
        return inp.get("skill", "")
    if name == "Agent":
        return inp.get("description") or inp.get("subagent_type", "")
    # default: just note the tool fired
    return ""


def already_recorded(session_file: Path, uuid: str) -> bool:
    if not session_file.exists():
        return False
    if not uuid:
        return False
    marker = f"<!-- turn-uuid: {uuid} -->"
    try:
        text = session_file.read_text(encoding="utf-8")
    except Exception:
        return False
    return marker in text


def format_block(
    timestamp: str,
    cwd: str,
    user_prompt_text: str,
    assistant_text: str,
    tools: list[dict],
    prompt_uuid: str,
) -> str:
    lines = []
    lines.append(f"## {timestamp}")
    lines.append(f"<!-- turn-uuid: {prompt_uuid} -->")
    if cwd:
        lines.append(f"**cwd:** `{cwd}`")
    lines.append("")
    lines.append("**User:**")
    lines.append("")
    lines.append(user_prompt_text.strip() or "_(empty)_")
    lines.append("")
    if tools:
        lines.append("**Tools:**")
        for t in tools:
            summary = f" — {t['summary']}" if t["summary"] else ""
            lines.append(f"- `{t['name']}`{summary}")
        lines.append("")
    lines.append("**Assistant output:**")
    lines.append("")
    lines.append(assistant_text.strip() or "_(no text output, tool-only turn)_")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--timestamp", required=True)
    ap.add_argument("--cwd", default="")
    ap.add_argument("--session-file", required=True)
    args = ap.parse_args()

    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        return 0

    entries = load_jsonl(transcript_path)
    if not entries:
        return 0

    # Find index of the last real user prompt
    last_user_idx = None
    for i in range(len(entries) - 1, -1, -1):
        if is_real_user_prompt(entries[i]):
            last_user_idx = i
            break

    if last_user_idx is None:
        return 0

    user_entry = entries[last_user_idx]
    prompt_uuid = user_entry.get("uuid", "")

    session_file = Path(args.session_file)
    if already_recorded(session_file, prompt_uuid):
        return 0

    user_prompt_text = message_content_text(user_entry)

    # Collect all assistant entries AFTER last_user_idx
    assistant_texts = []
    tools: list[dict] = []
    for entry in entries[last_user_idx + 1 :]:
        if entry.get("type") == "assistant" and not entry.get("isSidechain"):
            txt = message_content_text(entry)
            if txt:
                assistant_texts.append(txt)
            tools.extend(extract_tool_uses(entry))

    assistant_text = "\n\n".join(assistant_texts)

    block = format_block(
        timestamp=args.timestamp,
        cwd=args.cwd,
        user_prompt_text=user_prompt_text,
        assistant_text=assistant_text,
        tools=tools,
        prompt_uuid=prompt_uuid,
    )

    session_file.parent.mkdir(parents=True, exist_ok=True)

    # Write header if new file
    if not session_file.exists():
        header = f"# Session Seed Log — `{args.session_id}`\n\n"
        session_file.write_text(header, encoding="utf-8")

    with session_file.open("a", encoding="utf-8") as f:
        f.write(block)

    return 0


if __name__ == "__main__":
    sys.exit(main())
