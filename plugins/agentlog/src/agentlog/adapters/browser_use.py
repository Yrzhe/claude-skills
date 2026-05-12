"""Browser-use session dump adapter."""
from __future__ import annotations

import hashlib
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentlog import config
from agentlog.adapters.base import AdapterCursor, EventV0, SourceAdapter, SourceEvent
from agentlog.schema import SCHEMA_VERSION, make_event_id


DEFAULT_BROWSER_USE_DUMP = Path("~/.agentlog/browser_use_sessions.jsonl").expanduser()


class BrowserUseAdapter(SourceAdapter):
    source_type = "browser_use"

    def __init__(
        self,
        pool: Any,
        *,
        cursor_path: Path | None = None,
        dump_path: Path | None = None,
        device_id: str | None = None,
    ) -> None:
        super().__init__(pool, cursor_path=cursor_path)
        self.dump_path = Path(
            dump_path
            or os.environ.get("BROWSER_USE_SESSIONS_DUMP", "")
            or DEFAULT_BROWSER_USE_DUMP
        ).expanduser()
        self.device_id = device_id or self._device_id()
        self.host = socket.gethostname()

    def discover(self, cursor: AdapterCursor) -> list[SourceEvent]:
        if not self.dump_path.exists():
            return []

        sessions_cursor = cursor.get("sessions", {})
        if not isinstance(sessions_cursor, dict):
            sessions_cursor = {}
        session_ids = cursor.get("session_ids", [])
        if not isinstance(session_ids, list):
            session_ids = []
        seen_session_ids = [value for value in session_ids if isinstance(value, str)]

        events: list[SourceEvent] = []
        with self.dump_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                session = self._parse_session_line(line, line_number)
                if session is None:
                    continue
                session_id = session["session_id"]
                previous = sessions_cursor.get(session_id, {})
                if not isinstance(previous, dict):
                    previous = {}
                events.extend(self._new_message_events(session, previous, seen_session_ids, line_number))
                seen_session_ids = self._cursor_session_ids(seen_session_ids, session_id)
        return events

    def normalize(self, event: SourceEvent) -> EventV0 | None:
        message = event["message"]
        summary = self._summary(message)
        timestamp = self._timestamp(message.get("timestamp") or event.get("session_timestamp"))
        source_event_id = self._source_event_id(event)
        session_id = event["session_id"]
        project_name = self._project_name(event)

        return {
            "schema_version": SCHEMA_VERSION,
            "id": make_event_id(),
            "source_event_id": source_event_id,
            "timestamp": timestamp,
            "ingested_at": self._now(),
            "actor": {"id": "agent:browser-use", "name": "Browser-Use Agent", "kind": "agent"},
            "source_type": self.source_type,
            "source": {
                "device_id": self.device_id,
                "host": self.host,
                "process_id": None,
                "session_id": session_id,
            },
            "project": {"name": project_name, "path": None, "id": self._hash(project_name)[:16], "git_remote": None, "git_commit": None},
            "action": {"type": "browser_step", "status": self._status(message), "label": self._label(message)},
            "summary": summary,
            "payload": {
                "session_metadata": event.get("metadata") or {},
                "message_index": event["message_index"],
                "message_id": event.get("message_id"),
                "message": message,
                "text_excerpt": self._truncate(summary, 2000),
            },
            "artifact_refs": self._artifact_refs(message),
            "session": {"id": session_id, "title": project_name},
            "parent_id": None,
            "thread_id": session_id,
            "tags": ["browser_use", "browser"],
            "links": self._links(message),
            "metrics": {},
            "privacy": {"level": "private", "redacted": False},
            "dedupe_key": self._dedupe_key(source_event_id, summary, timestamp),
            "raw_ref": {"type": "browser_use_sessions_jsonl", "uri": f"{self.dump_path}:{event['dump_line']}"},
        }

    def _parse_session_line(self, line: str, line_number: int) -> dict[str, Any] | None:
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(raw, dict):
            return None

        session_obj = raw.get("session") if isinstance(raw.get("session"), dict) else {}
        metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        if session_obj:
            metadata = {**session_obj, **metadata}

        session_id = (
            raw.get("session_id")
            or raw.get("id")
            or raw.get("sessionId")
            or session_obj.get("id")
            or session_obj.get("session_id")
        )
        if not isinstance(session_id, str) or not session_id:
            session_id = f"dump-line-{line_number}"

        messages = raw.get("messages") or raw.get("session_messages") or raw.get("sessionMessages")
        if not isinstance(messages, list):
            return None

        return {
            "session_id": session_id,
            "metadata": metadata,
            "messages": [message for message in messages if isinstance(message, dict)],
            "timestamp": raw.get("timestamp") or metadata.get("timestamp"),
        }

    def _new_message_events(
        self,
        session: dict[str, Any],
        previous: dict[str, Any],
        session_ids: list[Any],
        line_number: int,
    ) -> list[SourceEvent]:
        session_id = session["session_id"]
        last_seen_index = int(previous.get("last_seen_index", -1) or -1)
        messages = session["messages"]
        events: list[SourceEvent] = []

        for index, message in enumerate(messages):
            if index <= last_seen_index:
                continue
            message_id = self._message_id(message, index)
            events.append(
                {
                    "session_id": session_id,
                    "metadata": session["metadata"],
                    "session_timestamp": session.get("timestamp"),
                    "message": message,
                    "message_id": message_id,
                    "message_index": index,
                    "dump_line": line_number,
                    "_cursor_update": {
                        "session_ids": self._cursor_session_ids(session_ids, session_id),
                        "sessions": {
                            session_id: {
                                "last_seen_message_id": message_id,
                                "last_seen_index": index,
                                "last_seen_at": self._now(),
                            }
                        },
                    },
                }
            )
        return events

    def _cursor_session_ids(self, existing: list[Any], session_id: str) -> list[str]:
        values = [value for value in existing if isinstance(value, str)]
        return list(dict.fromkeys([*values, session_id]))

    def _summary(self, message: dict[str, Any]) -> str:
        parts: list[str] = []
        action = message.get("action")
        thought = message.get("thought")
        if isinstance(action, str):
            parts.append(action)
        elif isinstance(action, dict):
            action_name = action.get("name") or action.get("type") or action.get("description")
            if isinstance(action_name, str):
                parts.append(action_name)
        if isinstance(thought, str):
            parts.append(thought)
        if not parts:
            for key in ("summary", "text", "message", "content"):
                value = message.get(key)
                if isinstance(value, str):
                    parts.append(value)
                    break
        return self._truncate(" - ".join(parts) or "Browser-use step", 240)

    def _status(self, message: dict[str, Any]) -> str:
        status = message.get("status")
        if status in {"completed", "blocked", "error", "in_progress"}:
            return str(status)
        if message.get("error"):
            return "error"
        if message.get("done") is True or message.get("is_done") is True:
            return "completed"
        return "completed"

    def _label(self, message: dict[str, Any]) -> str | None:
        action = message.get("action")
        if isinstance(action, str):
            return self._truncate(action, 80)
        if isinstance(action, dict):
            for key in ("name", "type", "description"):
                value = action.get(key)
                if isinstance(value, str):
                    return self._truncate(value, 80)
        return None

    def _project_name(self, event: SourceEvent) -> str:
        metadata = event.get("metadata")
        if isinstance(metadata, dict):
            for key in ("task_name", "task", "name", "title"):
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    return self._truncate(value.strip(), 120)
        return "browser-use"

    def _message_id(self, message: dict[str, Any], index: int) -> str:
        for key in ("id", "message_id", "messageId"):
            value = message.get(key)
            if isinstance(value, str) and value:
                return value
        return f"index-{index}"

    def _source_event_id(self, event: SourceEvent) -> str:
        return f"browser_use:{event['session_id']}:{event['message_id']}"

    def _artifact_refs(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        url = message.get("url") or message.get("current_url")
        if isinstance(url, str) and url:
            refs.append({"kind": "url", "uri": url, "storage": "external"})
        screenshot = message.get("screenshot") or message.get("screenshot_path")
        if isinstance(screenshot, str) and screenshot:
            refs.append({"kind": "screenshot", "uri": screenshot, "storage": "local_only"})
        return refs

    def _links(self, message: dict[str, Any]) -> list[dict[str, str]]:
        url = message.get("url") or message.get("current_url")
        if isinstance(url, str) and url:
            return [{"type": "browser_url", "url": url}]
        return []

    def _timestamp(self, value: Any) -> str:
        if isinstance(value, str) and value:
            return value.replace("Z", "+00:00")
        return self._now()

    def _device_id(self) -> str:
        env = os.environ.get("AGENTLOG_DEVICE_ID")
        if env:
            return env
        device = config.load_device()
        if device:
            return device.device_id
        return f"{socket.gethostname() or 'device'}-uninitialized"

    def _dedupe_key(self, source_event_id: str, summary: str, timestamp: str) -> str:
        return self._hash(f"{self.source_type}|{self.device_id}|{source_event_id}|{timestamp}|{summary}")

    def _hash(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _truncate(self, value: Any, limit: int) -> str:
        text = "" if value is None else str(value)
        text = " ".join(text.split())
        if len(text) <= limit:
            return text
        return text[: limit - 15].rstrip() + " ...[truncated]"
