"""One-shot migrator: ~/.claude/skills/seed/state/sessions/*.md → agentlog pool.

The seed skill records each Claude Code turn as a markdown block headed by
`## <ISO timestamp>` with a `<!-- turn-uuid: ... -->` comment and a `**User:**`
section followed by a `**Tools:**` listing. We convert each turn into one
EventV0 with `source_type = "claude_code_seed"` so it doesn't collide with
the live ClaudeCodeAdapter (which uses `source_type = "claude_code"`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .schema import make_event_id


DEFAULT_SEED_DIR = Path("~/.claude/skills/seed/state/sessions").expanduser()

# `## 2026-04-21 00:07:29`
HEADING_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2}[T ]?\d{2}:\d{2}:\d{2})", re.MULTILINE)
TURN_UUID_RE = re.compile(r"<!--\s*turn-uuid:\s*([0-9a-f-]+)\s*-->")
CWD_RE = re.compile(r"\*\*cwd:\*\*\s+`([^`]+)`")
TOOL_LINE_RE = re.compile(r"^-\s+`([^`]+)`")


@dataclass
class MigrationResult:
    sessions_scanned: int
    turns_emitted: int
    turns_skipped: int
    quarantined: int


def _iter_turns(text: str) -> Iterator[dict[str, Any]]:
    """Split a seed session markdown into per-turn dicts."""
    # Find heading positions
    headings: list[tuple[int, str]] = []
    for m in HEADING_RE.finditer(text):
        headings.append((m.start(), m.group(1)))

    for i, (start, ts_raw) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        block = text[start:end]

        ts_norm = ts_raw.replace(" ", "T")
        # Default to UTC if no offset
        if "+" not in ts_norm and not ts_norm.endswith("Z"):
            ts_norm = ts_norm + "+00:00"

        uuid_match = TURN_UUID_RE.search(block)
        turn_uuid = uuid_match.group(1) if uuid_match else f"line:{start}"

        cwd_match = CWD_RE.search(block)
        cwd = cwd_match.group(1) if cwd_match else None

        # Extract User section
        user_text = ""
        m = re.search(r"\*\*User:\*\*\s*\n+(.*?)(?:\n\*\*Tools:\*\*|\n## |$)",
                      block, re.DOTALL)
        if m:
            user_text = m.group(1).strip()

        # Extract Tools section
        tools: list[str] = []
        tools_section = re.search(r"\*\*Tools:\*\*\s*\n+(.*?)(?:\n## |$)",
                                   block, re.DOTALL)
        if tools_section:
            for line in tools_section.group(1).splitlines():
                tm = TOOL_LINE_RE.match(line.strip())
                if tm:
                    tools.append(tm.group(1))

        yield {
            "timestamp": ts_norm,
            "turn_uuid": turn_uuid,
            "cwd": cwd,
            "user_text": user_text,
            "tools": tools,
        }


def _project_from_cwd(cwd: str | None) -> dict[str, Any]:
    if not cwd:
        return {"name": "unknown"}
    name = Path(cwd).name or cwd
    return {"name": name, "path": cwd}


def _summary(user_text: str, n_tools: int) -> str:
    main = user_text.replace("\n", " ").strip()
    if not main:
        return f"(empty turn, {n_tools} tools)"
    main = re.sub(r"<command-(?:message|name|args)>[^<]*</command-[^>]+>", "", main).strip()
    main = re.sub(r"\s+", " ", main)
    if len(main) > 200:
        main = main[:199] + "…"
    if n_tools:
        return f"{main}  [{n_tools} tools]"
    return main


def _build_event(*, session_id: str, turn: dict[str, Any], device_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    summary = _summary(turn["user_text"], len(turn["tools"]))
    if len(summary) > 240:
        summary = summary[:239] + "…"

    return {
        "schema_version": "agentlog.event.v0",
        "id": make_event_id(),
        "source_event_id": f"seed:{session_id}:{turn['turn_uuid']}",
        "timestamp": turn["timestamp"],
        "ingested_at": now,
        "actor": {"id": "human:seed-import", "name": "User", "kind": "human"},
        "source_type": "claude_code_seed",
        "source": {
            "device_id": device_id,
            "session_id": session_id,
        },
        "project": _project_from_cwd(turn["cwd"]),
        "action": {"type": "user_request", "status": "completed"},
        "summary": summary,
        "payload": {
            "tools": turn["tools"],
            "tool_count": len(turn["tools"]),
            "user_text_excerpt": turn["user_text"][:2_000],
        },
        "artifact_refs": [],
        "session": {"id": session_id, "cwd": turn["cwd"]},
        "tags": ["seed_import", "claude_code"],
    }


def migrate(
    pool: Any,
    *,
    seed_dir: Path = DEFAULT_SEED_DIR,
    device_id: str,
    dry_run: bool = False,
) -> MigrationResult:
    result = MigrationResult(0, 0, 0, 0)

    if not seed_dir.exists():
        return result

    for md in sorted(seed_dir.glob("*.md")):
        session_id = md.stem
        result.sessions_scanned += 1
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue

        for turn in _iter_turns(text):
            event = _build_event(
                session_id=session_id,
                turn=turn,
                device_id=device_id,
            )
            if dry_run:
                result.turns_emitted += 1
                continue
            try:
                pool.append(event, flush=False)
                result.turns_emitted += 1
            except Exception:
                result.quarantined += 1

    return result
