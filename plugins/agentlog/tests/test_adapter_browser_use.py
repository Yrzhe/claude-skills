from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.adapters.browser_use import BrowserUseAdapter  # noqa: E402
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

    def append(self, event: dict, flush: bool = False) -> AppendResult:
        validate(event)
        self.events.append(event)
        return AppendResult(ok=True, event_id=event["id"], shard_path=Path("/tmp/mock"), duplicate=False)


def make_adapter(tmp_path: Path, pool: MockPool, dump_path: Path) -> BrowserUseAdapter:
    return BrowserUseAdapter(
        pool,
        cursor_path=tmp_path / "browser-use-cursor.json",
        dump_path=dump_path,
        device_id="test-device",
    )


def write_dump(path: Path, sessions: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for session in sessions:
            f.write(json.dumps(session) + "\n")


def test_no_dump_file_is_noop(tmp_path: Path) -> None:
    pool = MockPool()
    dump_path = tmp_path / "missing" / "browser_use_sessions.jsonl"

    result = make_adapter(tmp_path, pool, dump_path).pollOnce()

    assert result["emitted"] == 0
    assert result["skipped"] == 0
    assert pool.events == []


def test_single_session_multiple_messages_emit_browser_steps(tmp_path: Path) -> None:
    pool = MockPool()
    dump_path = tmp_path / "browser_use_sessions.jsonl"
    write_dump(
        dump_path,
        [
            {
                "session_id": "browser-session-1",
                "metadata": {"task_name": "Research pricing page"},
                "messages": [
                    {
                        "id": "msg-1",
                        "timestamp": "2026-05-12T12:00:00Z",
                        "action": "open_url",
                        "thought": "Navigate to the pricing page.",
                        "url": "https://example.com/pricing",
                    },
                    {
                        "id": "msg-2",
                        "timestamp": "2026-05-12T12:00:05Z",
                        "action": {"name": "extract_text"},
                        "thought": "Read the plan cards.",
                    },
                ],
            }
        ],
    )

    result = make_adapter(tmp_path, pool, dump_path).pollOnce()

    assert result["emitted"] == 2
    assert [event["action"]["type"] for event in pool.events] == ["browser_step", "browser_step"]
    assert [event["source"]["session_id"] for event in pool.events] == [
        "browser-session-1",
        "browser-session-1",
    ]
    assert pool.events[0]["actor"] == {
        "id": "agent:browser-use",
        "name": "Browser-Use Agent",
        "kind": "agent",
    }
    assert pool.events[0]["project"]["name"] == "Research pricing page"
    assert pool.events[0]["summary"] == "open_url - Navigate to the pricing page."
    assert pool.events[0]["payload"]["message"]["url"] == "https://example.com/pricing"
    assert pool.events[0]["artifact_refs"] == [
        {"kind": "url", "uri": "https://example.com/pricing", "storage": "external"}
    ]


def test_cursor_prevents_duplicate_emits(tmp_path: Path) -> None:
    pool = MockPool()
    dump_path = tmp_path / "browser_use_sessions.jsonl"
    write_dump(
        dump_path,
        [
            {
                "session_id": "browser-session-1",
                "metadata": {"task": "Check docs"},
                "messages": [
                    {"id": "msg-1", "action": "open_url", "thought": "Open docs."},
                    {"id": "msg-2", "action": "click", "thought": "Open quickstart."},
                ],
            }
        ],
    )
    adapter = make_adapter(tmp_path, pool, dump_path)

    first = adapter.pollOnce()
    second = adapter.pollOnce()

    assert first["emitted"] == 2
    assert second["emitted"] == 0
    assert len(pool.events) == 2
    cursor = second["cursor"]
    assert cursor["session_ids"] == ["browser-session-1"]
    assert cursor["sessions"]["browser-session-1"]["last_seen_message_id"] == "msg-2"
    assert cursor["sessions"]["browser-session-1"]["last_seen_index"] == 1
