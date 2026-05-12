"""Format helpers for `agentlog pool` / `agentlog recap`.

Pure formatting layer — no LLM synthesis here. The `agentlog` skill itself (or
a downstream `seed`-like prompt) is responsible for narrative summarization
when the user invokes the skill from a chat agent.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .reader import stats


def _ts_short(ts: str) -> str:
    """Render an ISO timestamp as 'MM-DD HH:MM' local-ish (keep timezone offset)."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return ts[:16]
    return dt.strftime("%m-%d %H:%M")


def _trunc(text: str, n: int) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def format_flat(events: list[dict[str, Any]], *, limit: int | None = None) -> str:
    """One line per event, sorted by time."""
    lines: list[str] = []
    rows = events[-limit:] if limit else events
    for e in rows:
        ts = _ts_short(e.get("timestamp", ""))
        src = e.get("source_type", "?")
        actor = (e.get("actor") or {}).get("name") or "?"
        act = (e.get("action") or {}).get("type") or "?"
        proj = (e.get("project") or {}).get("name") or "?"
        summary = _trunc(e.get("summary", ""), 80)
        lines.append(f"{ts}  {src:<11}  {actor:<14}  {act:<18}  [{proj}] {summary}")
    return "\n".join(lines) if lines else "(no events)"


def format_grouped(events: list[dict[str, Any]], *, by: str) -> str:
    """Group by source/project/agent/device. Show counts + 3 most recent per group."""
    by_norm = {
        "source": "source_type",
        "project": "_proj",
        "agent": "_actor",
        "device": "_device",
    }.get(by, by)

    def key_of(e: dict[str, Any]) -> str:
        if by_norm == "source_type":
            return e.get("source_type", "?")
        if by_norm == "_proj":
            return (e.get("project") or {}).get("name", "?")
        if by_norm == "_actor":
            return (e.get("actor") or {}).get("name", "?")
        if by_norm == "_device":
            return (e.get("source") or {}).get("device_id", "?")
        return "?"

    groups: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        k = key_of(e)
        groups.setdefault(k, []).append(e)

    parts = [f"== {len(groups)} groups by {by}, {len(events)} events ==", ""]
    for k in sorted(groups):
        evs = groups[k]
        st = stats(evs)
        parts.append(f"┌── {k}  ({st['count']} events, {st['session_count']} sessions)")
        for src, c in sorted(st["sources"].items(), key=lambda kv: -kv[1]):
            parts.append(f"│   {src}: {c}")
        for e in evs[-3:]:
            ts = _ts_short(e.get("timestamp", ""))
            act = (e.get("action") or {}).get("type") or "?"
            parts.append(f"│   [{ts}] {act}: {_trunc(e.get('summary', ''), 70)}")
        parts.append("")
    return "\n".join(parts)


def format_recap(date_iso: str, events: list[dict[str, Any]], *, by: str = "source") -> str:
    """Per-day recap. Markdown output, scriptable to LLM downstream."""
    st = stats(events)
    if st["count"] == 0:
        return f"# {date_iso} · agentlog recap\n\n(no events captured)"

    lines: list[str] = [f"# {date_iso} · agentlog recap", ""]
    lines.append(
        f"**{st['count']} events** across "
        f"**{len(st['sources'])} sources**, "
        f"**{len(st['projects'])} projects**, "
        f"**{st['session_count']} sessions** "
        f"on **{len(st['devices'])} devices**."
    )
    if st["first_ts"] and st["last_ts"]:
        lines.append(f"\nTime span: `{st['first_ts']}` → `{st['last_ts']}`")

    lines.append("")
    lines.append("## Source breakdown")
    for src, c in sorted(st["sources"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- **{src}**: {c} events")

    lines.append("")
    lines.append("## Project breakdown")
    for proj, c in sorted(st["projects"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- **{proj}**: {c} events")

    lines.append("")
    lines.append(f"## Detail (grouped by {by})")
    lines.append(format_grouped(events, by=by))

    return "\n".join(lines)
