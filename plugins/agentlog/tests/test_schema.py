from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.schema import (  # noqa: E402
    EventValidationError,
    make_event_id,
    normalize_dedupe_key,
    validate,
)


def valid_event(**overrides):
    event = {
        "schema_version": "agentlog.event.v0",
        "id": make_event_id(),
        "source_event_id": "codex:session-1:line-1",
        "timestamp": "2026-05-12T17:04:31.238+08:00",
        "ingested_at": "2026-05-12T17:04:35.102+08:00",
        "actor": {"id": "codex:local-default", "name": "Codex", "kind": "agent"},
        "source_type": "codex",
        "source": {
            "device_id": "device-a",
            "host": "host-a",
            "process_id": "pid-123",
            "session_id": "session-1",
        },
        "project": {"name": "agentlog", "path": "/tmp/agentlog"},
        "action": {
            "type": "session_completed",
            "status": "completed",
            "label": "recap generated",
        },
        "summary": "Codex wrote a recap.",
        "payload": {"duration_ms": 1000, "text_excerpt": "done"},
        "artifact_refs": [
            {
                "kind": "file",
                "uri": "sessions/session-1/recap.md",
                "storage": "git",
                "bytes": 12,
            }
        ],
    }
    event.update(overrides)
    return event


def test_validate_accepts_valid_event():
    event = valid_event()

    assert validate(event) == event
    assert normalize_dedupe_key(event).startswith("sha256:")


def test_validate_rejects_missing_required_field():
    event = valid_event()
    event.pop("source_event_id")

    with pytest.raises(EventValidationError, match="source_event_id"):
        validate(event)


def test_validate_rejects_bad_enum():
    event = valid_event(source_type="unknown_agent")

    with pytest.raises(EventValidationError, match="bad source_type"):
        validate(event)


def test_validate_rejects_summary_over_240_chars():
    event = valid_event(summary="x" * 241)

    with pytest.raises(EventValidationError, match="summary exceeds"):
        validate(event)


def test_validate_accepts_cursor_source_type():
    event = valid_event(source_type="cursor")
    event["actor"] = {"id": "cursor:local-default", "name": "Cursor", "kind": "agent"}
    event["source_event_id"] = "cursor:workspace-abc:msg-1"

    assert validate(event) == event


def test_validate_accepts_decision_action_type():
    event = valid_event(
        action={
            "type": "decision",
            "status": "completed",
            "label": "use AGENTS.md double-write",
        },
        payload={
            "rationale": "covers Cursor + Codex without duplication",
            "alternatives_considered": ["single docs/agent-context.md include"],
        },
    )

    assert validate(event) == event


def test_validate_accepts_next_step_action_type():
    event = valid_event(
        action={"type": "next_step", "status": "in_progress", "label": "wire CLI"},
        payload={"priority": "high", "blocked_by": []},
    )

    assert validate(event) == event
