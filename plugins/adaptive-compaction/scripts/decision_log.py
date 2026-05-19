#!/usr/bin/env python3
"""Append adaptive-compaction decisions to JSONL.

JSON stdin -> JSON stdout. No network. No model calls.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    pass


VALID_ACTIONS = {
    "NOOP",
    "ZERO_LLM_PRUNE",
    "SAVE_STATE",
    "PREPARE_FOR_COMPACT",
    "FORCED_COMPACT",
    "FORK_OR_RESET",
    "ASK_USER",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def number(data: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = data.get(key, default)
    if value is None:
        return default
    if not isinstance(value, (int, float)):
        raise ContractError(f"schema violation: {key} must be numeric")
    return float(value)


def integer(data: dict[str, Any], key: str, default: int = 0) -> int:
    return int(number(data, key, default))


def boolean(data: dict[str, Any], key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ContractError(f"schema violation: {key} must be boolean")
    return value


def list_value(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContractError(f"schema violation: {key} must be list")
    return value


def object_value(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ContractError(f"schema violation: {key} must be object")
    return value


def resolve_log_path(data: dict[str, Any]) -> Path:
    raw = data.get("log_path") or data.get("decision_log_path") or "decision_log.jsonl"
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_entry(data: dict[str, Any]) -> dict[str, Any]:
    action = str(data.get("action", ""))
    if action not in VALID_ACTIONS:
        raise ContractError("schema violation: action is invalid")
    thresholds = data.get("thresholds", data.get("thresholds_used", {}))
    if not isinstance(thresholds, dict):
        raise ContractError("schema violation: thresholds must be object")
    return {
        "ts": str(data.get("ts") or utc_now()),
        "session_id": str(data.get("session_id", "unknown")),
        "host": str(data.get("host", "unknown")),
        "host_capability_tier": str(data.get("host_capability_tier", "persist-only")),
        "headroom_frac": number(data, "headroom_frac"),
        "relevance": number(data, "relevance"),
        "relevance_confidence": number(data, "relevance_confidence"),
        "burden_tokens": integer(data, "burden_tokens"),
        "continuity": number(data, "continuity"),
        "continuity_flags": list_value(data, "continuity_flags"),
        "action": action,
        "require_snapshot": boolean(data, "require_snapshot"),
        "recovered_tokens": data.get("recovered_tokens", None),
        "post_action_user_correction": data.get("post_action_user_correction", None),
        "thresholds": thresholds,
    }


def append_log(data: dict[str, Any]) -> dict[str, Any]:
    path = resolve_log_path(data)
    entry = build_entry(data)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    return {"decision_log_path": str(path.resolve()), "entry": entry}


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ContractError("schema violation: input must be a JSON object")
        print(json.dumps(append_log(data), indent=2, sort_keys=True))
        return 0
    except (json.JSONDecodeError, ContractError, OSError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
