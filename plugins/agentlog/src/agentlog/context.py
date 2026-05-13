"""Project context file contract.

Layer 2 of agentlog: per-project state document that every AI coding agent
reads on entry. Two complementary surfaces:

1. AGENTS.md (Cursor + Codex entrypoint) and CLAUDE.md (Claude Code
   entrypoint) — both contain a managed state block bounded by
   ``<!-- agentlog:state-start -->`` ... ``<!-- agentlog:state-end -->``.
   User-authored text outside that block is preserved.

2. ``docs/agent-context/`` — three plain markdown files:
       state.md         overwrite-with-diff   (current snapshot)
       decisions.md     append-only           (design tradeoffs + rationale)
       next-steps.md    overwrite-with-diff   (open work)

The append-only contract on decisions.md guarantees rationale history is
never lost. state.md / next-steps.md are overwritten but should be git
tracked so diffs preserve the audit trail.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENTS_MD = "AGENTS.md"
CLAUDE_MD = "CLAUDE.md"
AGENT_CONTEXT_DIR = Path("docs/agent-context")
STATE_FILE = "state.md"
DECISIONS_FILE = "decisions.md"
NEXT_STEPS_FILE = "next-steps.md"

STATE_BLOCK_START = "<!-- agentlog:state-start -->"
STATE_BLOCK_END = "<!-- agentlog:state-end -->"

_ENTRY_TEMPLATE = """# Agent context

This file is maintained by [`agentlog`](https://github.com/Yrzhe/claude-skills/tree/main/plugins/agentlog).
The block between the markers below is auto-synced from `docs/agent-context/`.
Edit text **outside** the block freely — it will not be overwritten.

{block_start}
(no state yet — run `agentlog brief --project <name>` to populate)
{block_end}

## How to use

- New AI agent entering this project: read this file first, then
  `docs/agent-context/decisions.md` for the why.
- After a working session, run `agentlog brief --project <name>` to
  refresh the state block and next-steps.

## Decisions

Append-only history of design tradeoffs lives in
`docs/agent-context/decisions.md`.
"""

_DEFAULT_STATE_BODY = (
    "(no state yet — run `agentlog brief --project <name>` to populate)"
)
_DEFAULT_NEXT_STEPS = "_(no open items yet)_\n"
_DECISIONS_HEADER = (
    "# Decisions\n\n"
    "Append-only log of design tradeoffs and rationale. New entries are added "
    "at the bottom; existing entries are never removed.\n\n"
)


def init_project(project_root: Path) -> dict[str, Any]:
    """Create AGENTS.md / CLAUDE.md / docs/agent-context/ skeleton.

    Idempotent: never overwrites existing files. Returns ``{"created": bool}``
    indicating whether any file was created in this call.
    """
    project_root = Path(project_root)
    created = False

    entry_text = _ENTRY_TEMPLATE.format(
        block_start=STATE_BLOCK_START, block_end=STATE_BLOCK_END
    )
    for name in (AGENTS_MD, CLAUDE_MD):
        path = project_root / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(entry_text)
            created = True

    context_dir = project_root / AGENT_CONTEXT_DIR
    context_dir.mkdir(parents=True, exist_ok=True)

    state_path = context_dir / STATE_FILE
    if not state_path.exists():
        state_path.write_text(_DEFAULT_STATE_BODY + "\n")
        created = True

    decisions_path = context_dir / DECISIONS_FILE
    if not decisions_path.exists():
        decisions_path.write_text(_DECISIONS_HEADER)
        created = True

    next_steps_path = context_dir / NEXT_STEPS_FILE
    if not next_steps_path.exists():
        next_steps_path.write_text(_DEFAULT_NEXT_STEPS)
        created = True

    return {"created": created}


def sync_state(
    project_root: Path,
    *,
    state_md: str,
    next_steps_md: str,
) -> None:
    """Write state/next-steps to docs/agent-context and the entry-file blocks.

    AGENTS.md and CLAUDE.md keep all user-authored text outside the marker
    block. The state block in both files is replaced with the new state body
    plus the next-steps appended.
    """
    project_root = Path(project_root)
    init_project(project_root)

    context_dir = project_root / AGENT_CONTEXT_DIR
    (context_dir / STATE_FILE).write_text(state_md)
    (context_dir / NEXT_STEPS_FILE).write_text(next_steps_md)

    block_body = _entry_block_body(state_md=state_md, next_steps_md=next_steps_md)
    for name in (AGENTS_MD, CLAUDE_MD):
        path = project_root / name
        existing = path.read_text() if path.exists() else ""
        path.write_text(_replace_block(existing, block_body))


def append_decision(
    project_root: Path,
    *,
    title: str,
    rationale: str,
    alternatives: list[str] | None = None,
    source_event_id: str | None = None,
) -> None:
    """Append a single decision entry to decisions.md (never overwrites)."""
    project_root = Path(project_root)
    init_project(project_root)

    decisions_path = project_root / AGENT_CONTEXT_DIR / DECISIONS_FILE
    timestamp = datetime.now(timezone.utc).date().isoformat()

    entry_lines = [f"## {timestamp} — {title.strip()}", "", f"**Why**: {rationale.strip()}"]
    if alternatives:
        entry_lines.append("")
        entry_lines.append("**Alternatives considered**:")
        for alt in alternatives:
            entry_lines.append(f"- {alt}")
    if source_event_id:
        entry_lines.append("")
        entry_lines.append(f"_source: {source_event_id}_")
    entry_lines.append("")

    with decisions_path.open("a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n".join(entry_lines))
        f.write("\n")


def read_state(project_root: Path) -> dict[str, str]:
    """Read current state + next-steps from docs/agent-context/."""
    project_root = Path(project_root)
    context_dir = project_root / AGENT_CONTEXT_DIR

    def _read(name: str) -> str:
        path = context_dir / name
        return path.read_text() if path.exists() else ""

    return {
        "state": _read(STATE_FILE),
        "decisions": _read(DECISIONS_FILE),
        "next_steps": _read(NEXT_STEPS_FILE),
    }


def _entry_block_body(*, state_md: str, next_steps_md: str) -> str:
    parts = ["## Current state", "", state_md.rstrip("\n"), "", "## Next steps", "", next_steps_md.rstrip("\n")]
    return "\n".join(parts)


def _replace_block(text: str, body: str) -> str:
    start = text.find(STATE_BLOCK_START)
    end = text.find(STATE_BLOCK_END)
    new_block = f"{STATE_BLOCK_START}\n{body}\n{STATE_BLOCK_END}"
    if start == -1 or end == -1 or end < start:
        suffix = "" if text.endswith("\n") else "\n"
        return text + suffix + new_block + "\n"
    before = text[:start]
    after = text[end + len(STATE_BLOCK_END) :]
    return before + new_block + after
