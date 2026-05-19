#!/usr/bin/env python3
"""Deterministic four-signal scorer for adaptive-compaction.

JSON stdin -> JSON stdout. No network. No model calls.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from typing import Any


HOST_TIERS = {
    "claude-code": "hook-rich",
    "codex": "advise-persist",
    "mcp-only": "persist-only",
    "api": "persist-only",
    "unknown": "persist-only",
}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "i", "in", "into", "is", "it", "now", "of", "on", "or",
    "please", "the", "this", "to", "we", "with", "you", "your",
}

NEW_TASK_MARKERS = (
    "new task",
    "switch to",
    "unrelated",
    "now do",
    "different topic",
    "start over",
)


class ContractError(ValueError):
    pass


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def tokens(text: Any) -> set[str]:
    if text is None:
        return set()
    raw = re.findall(r"[a-zA-Z0-9_./-]+", str(text).lower())
    out: set[str] = set()
    for token in raw:
        parts = re.split(r"[/._-]+", token)
        for part in parts + [token]:
            if len(part) >= 2 and part not in STOPWORDS:
                out.add(part)
    return out


def require_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ContractError(f"schema violation: {key} must be a number")
    return float(value)


def require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ContractError(f"schema violation: {key} must be a list")
    return value


def host_tier(data: dict[str, Any]) -> str:
    host = str(data.get("host", "unknown"))
    declared = data.get("host_capability_tier")
    expected = HOST_TIERS.get(host, "persist-only")
    if declared in {"hook-rich", "advise-persist", "persist-only"}:
        return str(declared)
    return expected


def score_relevance(data: dict[str, Any]) -> tuple[float, float, int]:
    prompt = str(data.get("user_prompt") or "")
    prompt_tokens = tokens(prompt)

    context_text = " ".join(
        [str(data.get("objective") or "")]
        + [str(x) for x in data.get("accepted_constraints", [])]
        + [str(x) for x in data.get("plan_items", [])]
    )
    context_tokens = tokens(context_text)

    hot_files = [str(x) for x in data.get("hot_files", [])]
    symbols = [str(x) for x in data.get("touched_symbols", [])]
    structural_terms = set()
    for item in hot_files + symbols:
        structural_terms |= tokens(item)

    lexical_overlap = 0.0
    if prompt_tokens and context_tokens:
        lexical_overlap = len(prompt_tokens & context_tokens) / len(prompt_tokens | context_tokens)

    prompt_lower = prompt.lower()
    structural_hits = 0
    structural_total = 0
    for item in hot_files + symbols:
        item_tokens = tokens(item)
        if not item_tokens:
            continue
        structural_total += 1
        basename = item.rsplit("/", 1)[-1].lower()
        if basename and basename in prompt_lower:
            structural_hits += 1
        elif prompt_tokens & item_tokens:
            structural_hits += 1

    plan_items = [str(x) for x in data.get("plan_items", [])]
    plan_hits = 0
    for item in plan_items:
        item_tokens = tokens(item)
        if item_tokens and prompt_tokens & item_tokens:
            plan_hits += 1

    structural_overlap = structural_hits / structural_total if structural_total else 0.0
    plan_overlap = plan_hits / len(plan_items) if plan_items else 0.0
    objective_coverage = 0.0
    if prompt_tokens and context_tokens:
        objective_coverage = len(prompt_tokens & context_tokens) / len(prompt_tokens)

    marker_penalty = 0.35 if explicit_new_task(data) else 0.0
    relevance = clamp(
        (0.45 * objective_coverage)
        + (0.25 * lexical_overlap)
        + (0.20 * structural_overlap)
        + (0.10 * plan_overlap)
        - marker_penalty
    )
    if not explicit_new_task(data):
        if structural_overlap > 0 and objective_coverage >= 0.20:
            relevance = max(relevance, 0.55)
        elif objective_coverage >= 0.40:
            relevance = max(relevance, 0.45)

    evidence_parts = sum(
        1
        for score in (objective_coverage, lexical_overlap, structural_overlap, plan_overlap)
        if score > 0
    )
    confidence = clamp(0.25 + 0.20 * evidence_parts + min(len(prompt_tokens), 20) / 100)

    previous_streak = int(data.get("low_relevance_streak", 0) or 0)
    if explicit_new_task(data):
        low_streak = max(previous_streak + 1, 2)
    elif relevance < 0.30:
        low_streak = previous_streak + 1
    else:
        low_streak = 0
    return round(relevance, 4), round(confidence, 4), low_streak


def explicit_new_task(data: dict[str, Any]) -> bool:
    if data.get("explicit_new_task_marker") is True:
        return True
    prompt = str(data.get("user_prompt") or "").lower()
    return any(marker in prompt for marker in NEW_TASK_MARKERS)


def estimate_burden(data: dict[str, Any]) -> int:
    events = data.get("tool_events")
    if not isinstance(events, list):
        raise ContractError("schema violation: tool_events must be a list")

    latest_turn = max((int(e.get("turn", 0) or 0) for e in events if isinstance(e, dict)), default=0)
    burden_event_indexes: set[int] = set()

    reads_by_key: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    reads_by_target: dict[str, list[int]] = defaultdict(list)
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            raise ContractError("schema violation: tool_events entries must be objects")
        event_type = str(event.get("type", ""))
        target = str(event.get("target", ""))
        content_hash = str(event.get("content_hash", ""))
        turn = int(event.get("turn", 0) or 0)
        if event_type == "read":
            reads_by_key[(target, content_hash)].append((idx, turn))
            reads_by_target[target].append(turn)

    for occurrences in reads_by_key.values():
        if len(occurrences) > 1:
            for idx, _turn in occurrences[:-1]:
                burden_event_indexes.add(idx)

    for idx, event in enumerate(events):
        event_type = str(event.get("type", ""))
        target = str(event.get("target", ""))
        turn = int(event.get("turn", 0) or 0)
        event_tokens = int(event.get("tokens", 0) or 0)

        if event_type in {"write", "edit"} and any(read_turn > turn for read_turn in reads_by_target.get(target, [])):
            burden_event_indexes.add(idx)
        if event.get("errored") is True and latest_turn - turn >= 4:
            burden_event_indexes.add(idx)
        if event_tokens > 5000:
            burden_event_indexes.add(idx)

    return sum(int(events[idx].get("tokens", 0) or 0) for idx in burden_event_indexes)


def score_continuity(data: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []
    events = data.get("tool_events")
    if not isinstance(events, list):
        raise ContractError("schema violation: tool_events must be a list")
    recent_turns = data.get("recent_turns")
    if not isinstance(recent_turns, list):
        raise ContractError("schema violation: recent_turns must be a list")

    latest_turn = max((int(e.get("turn", 0) or 0) for e in events if isinstance(e, dict)), default=0)
    if any(
        isinstance(e, dict)
        and str(e.get("type", "")) in {"write", "edit"}
        and latest_turn - int(e.get("turn", 0) or 0) <= 2
        for e in events
    ):
        flags.append("active_edit")

    recent_text = " ".join(str(t.get("summary", "")) for t in recent_turns if isinstance(t, dict)).lower()
    if re.search(r"\b(fail|failing|failed|failure|test error|assertion|traceback)\b", recent_text):
        flags.append("failing_test")
    if any(isinstance(e, dict) and e.get("errored") is True and latest_turn - int(e.get("turn", 0) or 0) <= 2 for e in events):
        flags.append("unresolved_tool_error")
    if data.get("plan_items"):
        flags.append("uncheckpointed_plan")

    continuity = clamp(len(flags) / 4)
    return round(continuity, 4), flags


def score(data: dict[str, Any]) -> dict[str, Any]:
    required_lists = ["accepted_constraints", "hot_files", "touched_symbols", "plan_items", "recent_turns", "tool_events"]
    for key in required_lists:
        require_list(data, key)
    for key in ["tokens_used", "effective_window", "reserved_output"]:
        require_number(data, key)
    if not isinstance(data.get("user_prompt"), str):
        raise ContractError("schema violation: user_prompt must be a string")

    tokens_used = require_number(data, "tokens_used")
    effective_window = require_number(data, "effective_window")
    reserved_output = require_number(data, "reserved_output")
    if effective_window <= 0:
        raise ContractError("schema violation: effective_window must be > 0")

    headroom = clamp((effective_window - reserved_output - tokens_used) / effective_window)
    relevance, confidence, low_streak = score_relevance(data)
    burden = estimate_burden(data)
    continuity, flags = score_continuity(data)

    return {
        "headroom_frac": round(headroom, 4),
        "relevance": relevance,
        "relevance_confidence": confidence,
        "low_relevance_streak": low_streak,
        "burden_tokens": burden,
        "reclaimable_burden_frac": round(clamp(burden / tokens_used if tokens_used > 0 else 0.0), 4),
        "continuity": continuity,
        "continuity_flags": flags,
        "host_capability_tier": host_tier(data),
    }


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ContractError("schema violation: input must be a JSON object")
        print(json.dumps(score(data), indent=2, sort_keys=True))
        return 0
    except (json.JSONDecodeError, ContractError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
