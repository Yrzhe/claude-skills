"""Event pool → Haiku distill → project context files.

Public entry points:
    distill(project_name, events, anthropic_client, model) -> dict
        Run the LLM, parse the 3-section response, return the parts.

    run_brief(project_name, project_root, events, anthropic_client)
        Convenience: distill, then write state/next-steps via context.sync_state
        and append each decision via context.append_decision (dedup against
        existing decisions so re-runs are idempotent).

    get_default_client() -> anthropic.Anthropic
        Reads ANTHROPIC_API_KEY env. Fails fast with RuntimeError if missing.

    select_events(events, limit) -> list
        Prioritize decision > checkpoint > file_changed > rest; cap to `limit`.

The skill keeps prompt content separate (see references/brief.md). This file
holds the orchestration only.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable

from agentlog import context

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_EVENT_LIMIT = 200
DEFAULT_MAX_TOKENS = 4000

_PRIORITY = {
    "decision": 0,
    "next_step": 1,
    "checkpoint": 2,
    "session_completed": 3,
    "file_changed": 4,
    "error": 5,
    "command_run": 6,
}
_PRIORITY_DEFAULT = 9

_SECTION_RE = re.compile(
    r"---STATE---\s*(?P<state>.*?)\s*---DECISIONS---\s*(?P<decisions>.*?)\s*---NEXT-STEPS---\s*(?P<next_steps>.*)",
    re.DOTALL,
)

_DECISION_BLOCK_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)


_SYSTEM_PROMPT = (
    "You distill an AI-coding project's recent activity into 3 markdown sections. "
    "Every claim must be grounded in the events provided — do not invent facts. "
    "Be terse: bullets, not paragraphs. Decisions must answer 'why this and not the "
    "alternatives'. Output exactly three sections separated by '---STATE---', "
    "'---DECISIONS---', '---NEXT-STEPS---' markers."
)


def select_events(events: Iterable[dict[str, Any]], limit: int = DEFAULT_EVENT_LIMIT) -> list[dict[str, Any]]:
    """Pick the most informative `limit` events by action.type priority."""
    indexed = list(enumerate(events))
    indexed.sort(
        key=lambda pair: (
            _PRIORITY.get(pair[1].get("action", {}).get("type"), _PRIORITY_DEFAULT),
            pair[0],
        )
    )
    selected = [event for _, event in indexed[:limit]]
    selected.sort(key=lambda ev: ev.get("timestamp", ""))
    return selected


def distill(
    *,
    project_name: str,
    events: list[dict[str, Any]],
    anthropic_client: Any,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[str, str]:
    """Send events to Haiku, parse the 3-section response."""
    user_prompt = _format_user_prompt(project_name=project_name, events=events)
    response = anthropic_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = _response_text(response)
    parts = _parse_sections(text)
    return parts


def run_brief(
    *,
    project_name: str,
    project_root: Path,
    events: list[dict[str, Any]],
    anthropic_client: Any | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Distill + write context files. Returns the parsed sections."""
    client = anthropic_client or get_default_client()
    selected = select_events(events)
    parts = distill(
        project_name=project_name,
        events=selected,
        anthropic_client=client,
        model=model,
    )

    state_md = parts["state"] if parts["state"].strip() else "(no state)"
    next_steps_md = parts["next_steps"] if parts["next_steps"].strip() else "_(no open items)_"
    context.sync_state(project_root, state_md=state_md, next_steps_md=next_steps_md)

    existing = (project_root / context.AGENT_CONTEXT_DIR / context.DECISIONS_FILE).read_text() if (
        project_root / context.AGENT_CONTEXT_DIR / context.DECISIONS_FILE
    ).exists() else ""
    for decision in _split_decision_blocks(parts["decisions"]):
        title = decision["title"]
        if f"## {title}" in existing or _decision_title_already_logged(existing, title):
            continue
        context.append_decision(
            project_root,
            title=title,
            rationale=decision["rationale"] or "(no rationale captured)",
            alternatives=decision["alternatives"] or None,
            source_event_id=f"brief:{project_name}",
        )
        existing = (project_root / context.AGENT_CONTEXT_DIR / context.DECISIONS_FILE).read_text()

    return {"project": project_name, "events_used": len(selected), **parts}


def get_default_client() -> Any:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set — `agentlog brief` requires an Anthropic API key. "
            "Export it before running, e.g. `export ANTHROPIC_API_KEY=sk-...`."
        )
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "anthropic package not installed. Run `pip install anthropic` first."
        ) from exc
    return anthropic.Anthropic(api_key=api_key)


def _format_user_prompt(*, project_name: str, events: list[dict[str, Any]]) -> str:
    lines = [f"Project: {project_name}", f"Event count: {len(events)}", ""]
    for ev in events:
        ts = ev.get("timestamp", "?")
        action = ev.get("action", {}).get("type", "?")
        source = ev.get("source_type", "?")
        summary = ev.get("summary", "")
        payload = ev.get("payload", {})
        rationale = payload.get("rationale") if isinstance(payload, dict) else None
        line = f"[{ts}] ({source} · {action}) {summary}"
        if rationale:
            line += f"  WHY: {rationale}"
        lines.append(line)
    lines.append("")
    lines.append("Now distill into three sections.")
    return "\n".join(lines)


def _response_text(response: Any) -> str:
    blocks = getattr(response, "content", None)
    if not blocks:
        return ""
    parts = []
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(parts)


def _parse_sections(text: str) -> dict[str, str]:
    match = _SECTION_RE.search(text)
    if not match:
        return {"state": text.strip(), "decisions": "", "next_steps": ""}
    return {
        "state": match.group("state").strip() + "\n",
        "decisions": match.group("decisions").strip() + "\n",
        "next_steps": match.group("next_steps").strip() + "\n",
    }


def _split_decision_blocks(decisions_md: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    if not decisions_md.strip():
        return blocks
    matches = list(_DECISION_BLOCK_RE.finditer(decisions_md))
    for i, match in enumerate(matches):
        title = match.group("title").strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(decisions_md)
        body = decisions_md[start:end].strip()
        blocks.append(
            {
                "title": title,
                "rationale": _extract_field(body, "Why"),
                "alternatives": _extract_alternatives(body),
            }
        )
    return blocks


def _extract_field(body: str, label: str) -> str:
    pattern = re.compile(rf"\*\*{label}\*\*[:：]\s*(.+?)(?:\n\n|\Z)", re.DOTALL | re.IGNORECASE)
    match = pattern.search(body)
    if match:
        return match.group(1).strip()
    plain = re.compile(rf"^{label}[:：]\s*(.+?)(?:\n\n|\Z)", re.DOTALL | re.IGNORECASE | re.MULTILINE)
    match = plain.search(body)
    if match:
        return match.group(1).strip()
    return ""


def _extract_alternatives(body: str) -> list[str]:
    raw = _extract_field(body, "Alternatives considered") or _extract_field(body, "Alternatives")
    if not raw:
        return []
    items: list[str] = []
    for line in raw.splitlines():
        cleaned = line.strip().lstrip("-•*").strip()
        if cleaned:
            items.append(cleaned)
    if items:
        return items
    return [part.strip() for part in raw.split(",") if part.strip()]


def _decision_title_already_logged(existing: str, title: str) -> bool:
    return f"— {title}" in existing or f"-- {title}" in existing
