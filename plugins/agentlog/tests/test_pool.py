from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.pool import Pool  # noqa: E402
from agentlog.schema import EventValidationError, make_event_id  # noqa: E402


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
        "artifact_refs": [],
    }
    event.update(overrides)
    return event


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_append_valid_event_lands_in_shard(tmp_path):
    pool = Pool(tmp_path, "device-a")
    result = pool.append(valid_event(), flush=True)

    assert result.ok is True
    assert result.duplicate is False
    assert result.shard_path == (
        tmp_path
        / "pool"
        / "dt=2026-05-12"
        / "device=device-a"
        / "source=codex"
        / "shard-000.jsonl"
    )
    rows = read_jsonl(result.shard_path)
    assert rows[0]["source_event_id"] == "codex:session-1:line-1"
    assert rows[0]["dedupe_key"].startswith("sha256:")


def test_missing_required_field_goes_to_quarantine(tmp_path):
    pool = Pool(tmp_path, "device-a")
    event = valid_event()
    event.pop("summary")

    with pytest.raises(EventValidationError):
        pool.append(event)

    quarantine = tmp_path / "state" / "quarantine" / "2026-05-12.jsonl"
    rows = read_jsonl(quarantine)
    assert "summary" in rows[0]["error"]
    assert rows[0]["event"]["source_event_id"] == "codex:session-1:line-1"
    assert not (tmp_path / "pool").exists()


def test_source_event_id_is_idempotent(tmp_path):
    pool = Pool(tmp_path, "device-a")
    event = valid_event(source_event_id="codex:session-1:line-2")
    first = pool.append(event)
    second = pool.append({**event, "id": make_event_id(), "summary": "Retry"})

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.event_id == first.event_id
    assert len(read_jsonl(first.shard_path)) == 1


def test_shard_rolls_when_current_file_reaches_limit(tmp_path):
    pool = Pool(tmp_path, "device-a", shard_max_bytes=1)
    first = pool.append(valid_event(source_event_id="codex:session-1:line-3"))
    second = pool.append(
        valid_event(
            id=make_event_id(),
            source_event_id="codex:session-1:line-4",
            summary="Second event.",
        )
    )

    assert first.shard_path.name == "shard-000.jsonl"
    assert second.shard_path.name == "shard-001.jsonl"
    assert len(read_jsonl(first.shard_path)) == 1
    assert len(read_jsonl(second.shard_path)) == 1
