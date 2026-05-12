from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.adapters.claude_code import ClaudeCodeAdapter  # noqa: E402
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


def user_row(text: str, *, uuid: str = "user-1", session: str = "session-1") -> dict:
    return {
        "type": "user",
        "uuid": uuid,
        "timestamp": "2026-05-12T10:00:00.000Z",
        "sessionId": session,
        "cwd": "/tmp/project-alpha",
        "message": {"role": "user", "content": text},
    }


def assistant_text_row(text: str, *, uuid: str = "assistant-1", session: str = "session-1") -> dict:
    return {
        "type": "assistant",
        "uuid": uuid,
        "timestamp": "2026-05-12T10:00:01.000Z",
        "sessionId": session,
        "cwd": "/tmp/project-alpha",
        "message": {
            "role": "assistant",
            "id": f"msg-{uuid}",
            "content": [{"type": "text", "text": text}],
        },
    }


def assistant_tool_use_row(tool: str, *, uuid: str = "tool-use-1", session: str = "session-1") -> dict:
    return {
        "type": "assistant",
        "uuid": uuid,
        "timestamp": "2026-05-12T10:00:02.000Z",
        "sessionId": session,
        "cwd": "/tmp/project-alpha",
        "message": {
            "role": "assistant",
            "id": f"msg-{uuid}",
            "content": [{"type": "tool_use", "id": f"toolu-{uuid}", "name": tool, "input": {}}],
        },
    }


def tool_result_row(
    result: dict,
    *,
    uuid: str = "tool-result-1",
    session: str = "session-1",
) -> dict:
    return {
        "type": "user",
        "uuid": uuid,
        "timestamp": "2026-05-12T10:00:03.000Z",
        "sessionId": session,
        "cwd": "/tmp/project-alpha",
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "toolu-1", "content": "ok"}],
        },
        "toolUseResult": result,
    }


def adapter(tmp_path: Path, projects_root: Path, pool: MockPool) -> ClaudeCodeAdapter:
    return ClaudeCodeAdapter(
        pool,
        projects_root=projects_root,
        cursor_path=tmp_path / "cursor.json",
        device_id="test-device",
    )


def test_noise_filter_skips_read_tool_but_keeps_user_request(tmp_path: Path) -> None:
    projects_root = tmp_path / "claude" / "projects"
    session_file = projects_root / "-tmp-project-alpha" / "session-1.jsonl"
    write_jsonl(
        session_file,
        [
            assistant_tool_use_row("Read", uuid="read-tool"),
            user_row("Implement the adapter prototype.", uuid="user-task"),
        ],
    )
    pool = MockPool()

    result = adapter(tmp_path, projects_root, pool).pollOnce()

    assert result["skipped"] == 1
    assert result["emitted"] == 1
    assert [event["action"]["type"] for event in pool.events] == ["user_request"]
    file_cursor = result["cursor"]["files"][str(session_file)]
    assert file_cursor["line_index"] == 2
    assert file_cursor["offset"] == session_file.stat().st_size


def test_cursor_incrementally_advances_without_reemitting_old_lines(tmp_path: Path) -> None:
    projects_root = tmp_path / "claude" / "projects"
    session_file = projects_root / "-tmp-project-alpha" / "session-1.jsonl"
    write_jsonl(session_file, [user_row("First task.", uuid="user-1")])
    pool = MockPool()
    claude = adapter(tmp_path, projects_root, pool)

    first = claude.pollOnce()
    assert first["emitted"] == 1
    assert len(pool.events) == 1

    second = claude.pollOnce()
    assert second["emitted"] == 0
    assert len(pool.events) == 1

    write_jsonl(session_file, [user_row("Second task.", uuid="user-2")])
    third = claude.pollOnce()

    assert third["emitted"] == 1
    assert len(pool.events) == 2
    assert pool.events[-1]["summary"] == "Second task."
    assert third["cursor"]["files"][str(session_file)]["line_index"] == 2


def test_action_type_mapping_uses_v05_event_action_enum(tmp_path: Path) -> None:
    projects_root = tmp_path / "claude" / "projects"
    session_file = projects_root / "-tmp-project-alpha" / "session-1.jsonl"
    write_jsonl(
        session_file,
        [
            user_row("Please update the file.", uuid="user-1"),
            assistant_text_row("I will make the requested change now.", uuid="assistant-1"),
            assistant_tool_use_row("Bash", uuid="bash-1"),
            tool_result_row({"type": "create", "filePath": "/tmp/project-alpha/out.txt"}, uuid="result-1"),
            assistant_text_row("Done, completed and saved.", uuid="done-1"),
        ],
    )
    pool = MockPool()

    result = adapter(tmp_path, projects_root, pool).pollOnce()

    assert result["emitted"] == 5
    assert [event["action"]["type"] for event in pool.events] == [
        "user_request",
        "agent_response",
        "tool_call",
        "file_changed",
        "session_completed",
    ]
    assert pool.flushes == [False, False, False, False, True]
    for event in pool.events:
        validate(event)
        assert event["schema_version"] == "agentlog.event.v0"
        assert "action_type" not in event
