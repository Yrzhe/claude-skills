#!/usr/bin/env python3
"""Zero-LLM, non-destructive pruning planner.

JSON stdin -> JSON stdout. No network. No model calls.
Every action writes a recoverable event snapshot and returns a restore pointer.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def require_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    events = data.get("tool_events")
    if not isinstance(events, list):
        raise ContractError("schema violation: tool_events must be a list")
    out: list[dict[str, Any]] = []
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            raise ContractError("schema violation: tool_events entries must be objects")
        copied = dict(event)
        copied.setdefault("id", f"event-{idx}")
        out.append(copied)
    return out


def event_tokens(event: dict[str, Any]) -> int:
    value = event.get("tokens", 0)
    if not isinstance(value, (int, float)):
        raise ContractError("schema violation: event tokens must be numeric")
    return max(0, int(value))


def event_turn(event: dict[str, Any]) -> int:
    value = event.get("turn", 0)
    if not isinstance(value, (int, float)):
        raise ContractError("schema violation: event turn must be numeric")
    return int(value)


def content_material(event: dict[str, Any]) -> Any:
    for key in ("content", "output", "input", "payload", "text"):
        if key in event:
            return event[key]
    return None


def event_hash(event: dict[str, Any]) -> str:
    declared = event.get("content_hash")
    if isinstance(declared, str) and declared:
        return declared
    blob = json.dumps(event, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def safe_ref(value: Any) -> str:
    raw = str(value or "event")
    keep = [ch if ch.isalnum() or ch in "._-" else "_" for ch in raw]
    return "".join(keep)[:80] or "event"


def ensure_quarantine_dir(data: dict[str, Any]) -> Path:
    raw = data.get("quarantine_dir")
    if raw is None:
        raw = Path.cwd() / ".adaptive-compaction" / "quarantine"
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_restore_snapshot(quarantine_dir: Path, kind: str, event: dict[str, Any]) -> tuple[str, str]:
    digest = event_hash(event)
    ref = safe_ref(event.get("id") or event.get("target") or digest)
    path = quarantine_dir / f"{kind}-{ref}-{digest[:12]}.json"
    snapshot = {
        "kind": kind,
        "ts": utc_now(),
        "sha256": digest,
        "event": event,
        "content": content_material(event),
    }
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return str(path.resolve()), digest


def thresholds(data: dict[str, Any]) -> tuple[int, int]:
    config = data.get("thresholds", {})
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise ContractError("schema violation: thresholds must be an object")
    large_output = int(config.get("large_output_quarantine_tokens", data.get("large_output_quarantine_tokens", 5000)))
    error_age = int(config.get("error_input_purge_turns", data.get("error_input_purge_turns", 4)))
    return large_output, error_age


def plan_prune(data: dict[str, Any]) -> dict[str, Any]:
    events = require_events(data)
    quarantine_dir = ensure_quarantine_dir(data)
    large_output_threshold, error_age_threshold = thresholds(data)
    latest_turn = max((event_turn(event) for event in events), default=0)

    selected: dict[int, str] = {}

    # 1. Dedup repeated reads with the same target+hash; keep the latest.
    reads: dict[tuple[str, str], list[int]] = {}
    for idx, event in enumerate(events):
        if str(event.get("type", "")) == "read":
            key = (str(event.get("target", "")), event_hash(event))
            reads.setdefault(key, []).append(idx)
    for indexes in reads.values():
        if len(indexes) > 1:
            for idx in indexes[:-1]:
                selected.setdefault(idx, "dedup")

    # 2. Supersede write/edit payloads once a later read of the same target exists.
    read_turns_by_target: dict[str, list[int]] = {}
    for event in events:
        if str(event.get("type", "")) == "read":
            read_turns_by_target.setdefault(str(event.get("target", "")), []).append(event_turn(event))
    for idx, event in enumerate(events):
        if idx in selected:
            continue
        if str(event.get("type", "")) in {"write", "edit"}:
            target = str(event.get("target", ""))
            if any(read_turn > event_turn(event) for read_turn in read_turns_by_target.get(target, [])):
                selected[idx] = "supersede"

    # 3. Purge stale errored-tool inputs, preserving the event snapshot.
    for idx, event in enumerate(events):
        if idx in selected:
            continue
        if event.get("errored") is True and latest_turn - event_turn(event) >= error_age_threshold:
            selected[idx] = "error_purge"

    # 4. Quarantine large outputs not already handled.
    for idx, event in enumerate(events):
        if idx in selected:
            continue
        if event_tokens(event) > large_output_threshold:
            selected[idx] = "quarantine"

    actions: list[dict[str, Any]] = []
    for idx in sorted(selected):
        event = events[idx]
        kind = selected[idx]
        pointer, digest = write_restore_snapshot(quarantine_dir, kind, event)
        actions.append(
            {
                "kind": kind,
                "ref": str(event.get("id", f"event-{idx}")),
                "restore_pointer": pointer,
                "sha256": digest,
                "tokens": event_tokens(event),
            }
        )

    return {
        "recovered_tokens": sum(action["tokens"] for action in actions),
        "actions": actions,
        "quarantine_dir": str(quarantine_dir.resolve()),
    }


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ContractError("schema violation: input must be a JSON object")
        print(json.dumps(plan_prune(data), indent=2, sort_keys=True))
        return 0
    except (json.JSONDecodeError, ContractError, OSError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
