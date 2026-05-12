"""Tests for the pool reader + recap formatters."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agentlog import recap as recap_mod
from agentlog.reader import parse_window, stats, walk_events


def _ev(ts: str, source: str = "claude_code", project: str = "p1",
        device: str = "dev1", action: str = "agent_response",
        summary: str = "hello") -> dict:
    """Build a minimally-valid event dict for tests."""
    return {
        "schema_version": "agentlog.event.v0",
        "id": f"id-{ts}-{source}",
        "source_event_id": f"{source}:s:{ts}",
        "timestamp": ts,
        "ingested_at": ts,
        "actor": {"id": "a", "name": "Claude Code", "kind": "agent"},
        "source_type": source,
        "source": {"device_id": device, "session_id": "s"},
        "project": {"name": project},
        "action": {"type": action, "status": "completed"},
        "summary": summary,
        "payload": {},
        "artifact_refs": [],
    }


def _write_shard(root: Path, *, date: str, device: str, source: str,
                  events: list[dict]) -> Path:
    p = root / "pool" / f"dt={date}" / f"device={device}" / f"source={source}" / "shard-000.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return p


def test_parse_window():
    assert parse_window("30m") == timedelta(minutes=30)
    assert parse_window("4h") == timedelta(hours=4)
    assert parse_window("2d") == timedelta(days=2)
    assert parse_window("1w") == timedelta(weeks=1)
    with pytest.raises(ValueError):
        parse_window("nope")
    with pytest.raises(ValueError):
        parse_window("5x")


def test_walk_events_filters_by_source_and_project(tmp_path: Path):
    _write_shard(tmp_path, date="2026-05-12", device="dev1", source="claude_code",
                  events=[
                      _ev("2026-05-12T10:00:00+00:00", source="claude_code", project="A"),
                      _ev("2026-05-12T11:00:00+00:00", source="claude_code", project="B"),
                  ])
    _write_shard(tmp_path, date="2026-05-12", device="dev1", source="codex",
                  events=[_ev("2026-05-12T12:00:00+00:00", source="codex", project="A")])

    all_ev = list(walk_events(root_dir=tmp_path))
    assert len(all_ev) == 3

    only_a = list(walk_events(root_dir=tmp_path, projects=["A"]))
    assert len(only_a) == 2

    only_codex = list(walk_events(root_dir=tmp_path, sources=["codex"]))
    assert len(only_codex) == 1
    assert only_codex[0]["source_type"] == "codex"


def test_walk_events_dedupes_by_source_event_id(tmp_path: Path):
    # Two shards on different dates, same source_event_id (simulating a re-emitted event)
    e1 = _ev("2026-05-11T10:00:00+00:00")
    e1["source_event_id"] = "claude_code:s:dup"
    e2 = _ev("2026-05-12T10:00:00+00:00")
    e2["source_event_id"] = "claude_code:s:dup"
    _write_shard(tmp_path, date="2026-05-11", device="dev1", source="claude_code", events=[e1])
    _write_shard(tmp_path, date="2026-05-12", device="dev1", source="claude_code", events=[e2])
    out = list(walk_events(root_dir=tmp_path))
    assert len(out) == 1, "should dedupe across shards by source_event_id"


def test_walk_events_time_window(tmp_path: Path):
    _write_shard(tmp_path, date="2026-05-12", device="dev1", source="claude_code",
                  events=[
                      _ev("2026-05-12T09:00:00+00:00"),
                      _ev("2026-05-12T15:00:00+00:00"),
                  ])
    since = datetime(2026, 5, 12, 12, 0, tzinfo=timezone.utc)
    out = list(walk_events(root_dir=tmp_path, since=since))
    assert len(out) == 1
    assert out[0]["timestamp"] == "2026-05-12T15:00:00+00:00"


def test_stats_counts_correctly(tmp_path: Path):
    events = [
        _ev("2026-05-12T10:00:00+00:00", source="claude_code", project="A"),
        _ev("2026-05-12T11:00:00+00:00", source="claude_code", project="B"),
        _ev("2026-05-12T12:00:00+00:00", source="codex", project="A"),
    ]
    s = stats(events)
    assert s["count"] == 3
    assert s["sources"]["claude_code"] == 2
    assert s["sources"]["codex"] == 1
    assert s["projects"]["A"] == 2


def test_format_recap_renders_markdown(tmp_path: Path):
    events = [
        _ev("2026-05-12T10:00:00+00:00", source="claude_code", project="agentlog"),
        _ev("2026-05-12T11:00:00+00:00", source="codex", project="agentlog"),
    ]
    out = recap_mod.format_recap("2026-05-12", events, by="source")
    assert "# 2026-05-12 · agentlog recap" in out
    assert "**2 events**" in out
    assert "claude_code" in out and "codex" in out
    assert "agentlog" in out


def test_format_recap_empty_day():
    out = recap_mod.format_recap("2026-05-12", [], by="source")
    assert "no events" in out
