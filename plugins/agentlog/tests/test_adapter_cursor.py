from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.adapters.cursor import CursorAdapter  # noqa: E402
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
        return AppendResult(
            ok=True, event_id=event["id"], shard_path=Path("/tmp/mock"), duplicate=False
        )


def _make_workspace(
    storage_root: Path,
    workspace_hash: str,
    folder_uri: str,
    chat_data: dict,
) -> Path:
    ws_dir = storage_root / workspace_hash
    ws_dir.mkdir(parents=True, exist_ok=True)
    (ws_dir / "workspace.json").write_text(json.dumps({"folder": folder_uri}))

    db = ws_dir / "state.vscdb"
    conn = sqlite3.connect(db)
    try:
        conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value BLOB)")
        conn.execute(
            "INSERT INTO ItemTable VALUES (?, ?)",
            (
                "workbench.panel.aichat.view.aichat.chatdata",
                json.dumps(chat_data).encode("utf-8"),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return ws_dir


def _chat_data_with_two_turns() -> dict:
    return {
        "tabs": [
            {
                "tabId": "tab-a",
                "chatTitle": "implement context layer",
                "bubbles": [
                    {"type": "user", "text": "add a Cursor adapter to agentlog"},
                    {"type": "ai", "text": "I'll start by reading the base adapter."},
                    {"type": "user", "text": "use SQLite directly"},
                    {"type": "ai", "text": "Done. 3 new tests pass."},
                ],
            }
        ]
    }


def adapter(tmp_path: Path, storage_root: Path, pool: MockPool) -> CursorAdapter:
    return CursorAdapter(
        pool,
        storage_root=storage_root,
        cursor_path=tmp_path / "cursor.json",
        device_id="test-device",
    )


def test_cursor_adapter_emits_events_for_each_bubble(tmp_path: Path) -> None:
    storage = tmp_path / "Cursor" / "User" / "workspaceStorage"
    _make_workspace(
        storage,
        workspace_hash="abc123",
        folder_uri="file:///Users/me/projects/agentlog",
        chat_data=_chat_data_with_two_turns(),
    )

    pool = MockPool()
    result = adapter(tmp_path, storage, pool).pollOnce()

    assert result["emitted"] == 4
    assert pool.events[0]["source_type"] == "cursor"
    assert pool.events[0]["action"]["type"] == "user_request"
    assert pool.events[1]["action"]["type"] == "agent_response"
    assert pool.events[3]["action"]["type"] == "session_completed"
    assert pool.events[0]["project"]["name"] == "agentlog"
    assert pool.events[0]["source"]["session_id"] == "abc123:tab-a"


def test_cursor_adapter_skips_already_emitted_bubbles(tmp_path: Path) -> None:
    storage = tmp_path / "Cursor" / "User" / "workspaceStorage"
    _make_workspace(
        storage,
        workspace_hash="abc123",
        folder_uri="file:///Users/me/projects/agentlog",
        chat_data=_chat_data_with_two_turns(),
    )

    pool = MockPool()
    a = adapter(tmp_path, storage, pool)
    a.pollOnce()
    second = a.pollOnce()

    assert second["emitted"] == 0
    assert len(pool.events) == 4


def test_cursor_adapter_picks_up_new_bubbles_on_second_poll(tmp_path: Path) -> None:
    storage = tmp_path / "Cursor" / "User" / "workspaceStorage"
    ws_dir = _make_workspace(
        storage,
        workspace_hash="abc123",
        folder_uri="file:///Users/me/projects/agentlog",
        chat_data=_chat_data_with_two_turns(),
    )

    pool = MockPool()
    a = adapter(tmp_path, storage, pool)
    a.pollOnce()

    updated = _chat_data_with_two_turns()
    updated["tabs"][0]["bubbles"].append(
        {"type": "user", "text": "now wire the CLI"}
    )
    conn = sqlite3.connect(ws_dir / "state.vscdb")
    try:
        conn.execute(
            "UPDATE ItemTable SET value=? WHERE key=?",
            (
                json.dumps(updated).encode("utf-8"),
                "workbench.panel.aichat.view.aichat.chatdata",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    second = a.pollOnce()
    assert second["emitted"] == 1
    assert pool.events[-1]["action"]["type"] == "user_request"
    assert "wire the CLI" in pool.events[-1]["summary"]


def test_cursor_adapter_skips_unknown_schema_without_crashing(tmp_path: Path) -> None:
    storage = tmp_path / "Cursor" / "User" / "workspaceStorage"
    ws_dir = storage / "ghosthash"
    ws_dir.mkdir(parents=True, exist_ok=True)
    (ws_dir / "workspace.json").write_text(json.dumps({"folder": "file:///x"}))
    db = ws_dir / "state.vscdb"
    conn = sqlite3.connect(db)
    try:
        conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value BLOB)")
        conn.execute(
            "INSERT INTO ItemTable VALUES (?, ?)",
            ("some.unknown.key", b"not-our-schema"),
        )
        conn.commit()
    finally:
        conn.close()

    pool = MockPool()
    result = adapter(tmp_path, storage, pool).pollOnce()
    assert result["emitted"] == 0


def test_cursor_adapter_handles_missing_storage_root(tmp_path: Path) -> None:
    pool = MockPool()
    result = adapter(tmp_path, tmp_path / "does-not-exist", pool).pollOnce()
    assert result["emitted"] == 0
    assert result["skipped"] == 0
