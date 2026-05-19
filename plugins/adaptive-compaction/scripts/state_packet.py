#!/usr/bin/env python3
"""Write a redacted operational TASK_STATE.md packet.

JSON stdin -> JSON stdout. No network. No model calls.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    pass


REDACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{16,}")),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9_]{16,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*KEY-----.*?-----END [A-Z ]*KEY-----", re.DOTALL)),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    redacted = text
    for name, pattern in REDACTION_PATTERNS:
        redacted, count = pattern.subn(f"[REDACTED:{name}]", redacted)
        if count:
            counts[name] = counts.get(name, 0) + count
    return redacted, counts


def redact_value(value: Any) -> tuple[Any, dict[str, int]]:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        out = []
        total: dict[str, int] = {}
        for item in value:
            redacted, counts = redact_value(item)
            out.append(redacted)
            merge_counts(total, counts)
        return out, total
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        total: dict[str, int] = {}
        for key, item in value.items():
            redacted, counts = redact_value(item)
            out[str(key)] = redacted
            merge_counts(total, counts)
        return out, total
    return value, {}


def merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def as_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContractError(f"schema violation: {key} must be a list")
    return value


def as_text(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    raise ContractError(f"schema violation: {key} must be scalar text")


def bullet_list(items: list[Any]) -> str:
    if not items:
        return "- None recorded"
    lines = []
    for item in items:
        if isinstance(item, dict):
            rendered = json.dumps(item, sort_keys=True, ensure_ascii=False)
        else:
            rendered = str(item)
        lines.append(f"- {rendered}")
    return "\n".join(lines)


def resolve_output_path(data: dict[str, Any]) -> Path:
    raw = data.get("output_path") or data.get("task_state_path") or "TASK_STATE.md"
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_packet(data: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, int]]:
    redacted_data, counts = redact_value(data)
    if not isinstance(redacted_data, dict):
        raise ContractError("schema violation: redacted input must remain object")

    source_turn = redacted_data.get("source_turn", redacted_data.get("turn", None))
    meta = {
        "ts": as_text(redacted_data, "ts", utc_now()) or utc_now(),
        "source_turn": source_turn,
        "host": as_text(redacted_data, "host", "unknown"),
        "host_version": as_text(redacted_data, "host_version", "unknown"),
        "session_id": as_text(redacted_data, "session_id", "unknown"),
        "confidence": float(redacted_data.get("confidence", 0.0) or 0.0),
        "transcript_dump": as_text(redacted_data, "transcript_dump", ""),
    }

    branch_bits = [
        f"branch={as_text(redacted_data, 'branch', 'unknown')}",
        f"worktree={as_text(redacted_data, 'worktree', os.getcwd())}",
        f"session_id={meta['session_id']}",
    ]

    body = "\n".join(
        [
            "# TASK_STATE",
            "",
            "## Goal",
            as_text(redacted_data, "goal", as_text(redacted_data, "objective", "Not recorded.")) or "Not recorded.",
            "",
            "## Accepted Constraints",
            bullet_list(as_list(redacted_data, "accepted_constraints")),
            "",
            "## Current Branch / Worktree / Session",
            "- " + "\n- ".join(branch_bits),
            "",
            "## Touched Files / Symbols",
            "### Files",
            bullet_list(as_list(redacted_data, "touched_files") or as_list(redacted_data, "hot_files")),
            "",
            "### Symbols",
            bullet_list(as_list(redacted_data, "touched_symbols")),
            "",
            "## Decisions Already Made",
            bullet_list(as_list(redacted_data, "decisions")),
            "",
            "## Failing Tests / Commands / Exact Repro",
            bullet_list(as_list(redacted_data, "failing_tests") or as_list(redacted_data, "failing_commands")),
            "",
            "## Open Questions / Risks",
            bullet_list(as_list(redacted_data, "open_risks") or as_list(redacted_data, "risks")),
            "",
            "## Exact Next Action",
            as_text(redacted_data, "next_action", "Not recorded.") or "Not recorded.",
            "",
            "## Files To Reload First",
            bullet_list(as_list(redacted_data, "files_to_reload")),
            "",
            "## Raw Transcript Dump Pointer",
            meta["transcript_dump"] or "Not recorded.",
            "",
            "Meta: " + json.dumps(meta, sort_keys=True, ensure_ascii=False),
            "",
        ]
    )
    return body, meta, counts


def write_packet(data: dict[str, Any]) -> dict[str, Any]:
    path = resolve_output_path(data)
    body, meta, redactions = build_packet(data)
    path.write_text(body, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return {
        "task_state_path": str(path.resolve()),
        "meta": meta,
        "redactions": redactions,
    }


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ContractError("schema violation: input must be a JSON object")
        print(json.dumps(write_packet(data), indent=2, sort_keys=True))
        return 0
    except (json.JSONDecodeError, ContractError, OSError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
