from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.adapters.codex import CodexAdapter  # noqa: E402
from agentlog.schema import validate  # noqa: E402


@dataclass
class AppendResult:
    ok: bool
    event_id: str
    shard_path: Path
    duplicate: bool
    error: str | None = None


class MockPool:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self.flushes: list[bool] = []

    def append(self, event: dict, flush: bool = False) -> AppendResult:
        validate(event)
        self.events.append(event)
        self.flushes.append(flush)
        return AppendResult(ok=True, event_id=event["id"], shard_path=Path("/tmp/mock"), duplicate=False)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def rollout_path(root: Path) -> Path:
    return root / "2026" / "05" / "12" / "rollout-2026-05-12T10-00-00-session-1.jsonl"


def session_meta() -> dict:
    return {
        "timestamp": "2026-05-12T10:00:00.000Z",
        "type": "session_meta",
        "payload": {
            "id": "session-1",
            "cwd": "/tmp/project-beta",
            "originator": "Codex Desktop",
        },
    }


def user_message(text: str, *, timestamp: str = "2026-05-12T10:00:01.000Z") -> dict:
    return {
        "timestamp": timestamp,
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "user",
            "id": f"user-{timestamp}",
            "content": [{"type": "input_text", "text": text}],
        },
    }


def progress_message(text: str, timestamp: str) -> dict:
    return {
        "timestamp": timestamp,
        "type": "event_msg",
        "payload": {"type": "agent_message", "message": text, "phase": "commentary"},
    }


def apply_patch_call() -> dict:
    return {
        "timestamp": "2026-05-12T10:00:03.000Z",
        "type": "response_item",
        "payload": {
            "type": "function_call",
            "name": "apply_patch",
            "call_id": "call-apply-patch",
            "arguments": "*** Begin Patch\n*** Update File: x.py\n@@\n-pass\n+print('ok')\n*** End Patch\n",
        },
    }


def adapter(tmp_path: Path, sessions_root: Path, pool: MockPool) -> CodexAdapter:
    return CodexAdapter(
        pool,
        sessions_root=sessions_root,
        archive_root=tmp_path / "codex" / "archived_sessions",
        cursor_path=tmp_path / "cursor.json",
        device_id="test-device",
    )


def test_noise_filter_collapses_progress_event_messages_under_30_seconds(tmp_path: Path) -> None:
    sessions_root = tmp_path / "codex" / "sessions"
    session_file = rollout_path(sessions_root)
    write_jsonl(
        session_file,
        [
            session_meta(),
            progress_message("I am scanning files.", "2026-05-12T10:00:10.000Z"),
            progress_message("Still scanning files.", "2026-05-12T10:00:20.000Z"),
            progress_message("Continuing after a wider scan.", "2026-05-12T10:00:45.000Z"),
        ],
    )
    pool = MockPool()

    result = adapter(tmp_path, sessions_root, pool).pollOnce()

    assert result["skipped"] == 2
    assert result["emitted"] == 2
    assert [event["action"]["type"] for event in pool.events] == ["checkpoint", "checkpoint"]
    assert [event["summary"] for event in pool.events] == [
        "I am scanning files.",
        "Continuing after a wider scan.",
    ]


def test_cursor_incrementally_advances_without_reemitting_old_lines(tmp_path: Path) -> None:
    sessions_root = tmp_path / "codex" / "sessions"
    session_file = rollout_path(sessions_root)
    write_jsonl(session_file, [session_meta(), user_message("First request.")])
    pool = MockPool()
    codex = adapter(tmp_path, sessions_root, pool)

    first = codex.pollOnce()
    assert first["emitted"] == 1
    assert len(pool.events) == 1

    second = codex.pollOnce()
    assert second["emitted"] == 0
    assert len(pool.events) == 1

    write_jsonl(session_file, [user_message("Second request.", timestamp="2026-05-12T10:00:05.000Z")])
    third = codex.pollOnce()

    assert third["emitted"] == 1
    assert len(pool.events) == 2
    assert pool.events[-1]["summary"] == "Second request."
    file_cursor = third["cursor"]["files"][str(session_file)]
    assert file_cursor["line_index"] == 3
    assert file_cursor["offset"] == session_file.stat().st_size
    assert file_cursor["session_id"] == "session-1"


def test_apply_patch_maps_to_file_changed_event(tmp_path: Path) -> None:
    sessions_root = tmp_path / "codex" / "sessions"
    session_file = rollout_path(sessions_root)
    write_jsonl(session_file, [session_meta(), apply_patch_call()])
    pool = MockPool()

    result = adapter(tmp_path, sessions_root, pool).pollOnce()

    assert result["emitted"] == 1
    event = pool.events[0]
    validate(event)
    assert event["source_type"] == "codex"
    assert event["action"]["type"] == "file_changed"
    assert event["action"]["label"] == "apply_patch"
    assert event["artifact_refs"] == [
        {
            "kind": "diff",
            "uri": "codex:apply_patch",
            "storage": "local_only",
            "metadata": {"call_id": "call-apply-patch"},
        }
    ]
