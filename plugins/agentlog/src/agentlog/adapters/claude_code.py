"""Claude Code JSONL source adapter."""
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
from agentlog.schema import ACTION_TYPES, SCHEMA_VERSION, make_event_id


DEFAULT_CLAUDE_PROJECTS_ROOT = Path("~/.claude/projects").expanduser()


class ClaudeCodeAdapter(SourceAdapter):
    source_type = "claude_code"

    def __init__(
        self,
        pool: Any,
        *,
        projects_root: Path | None = None,
        cursor_path: Path | None = None,
        include_eval: bool = False,
        device_id: str | None = None,
    ) -> None:
        super().__init__(pool, cursor_path=cursor_path)
        self.projects_root = Path(
            projects_root
            or os.environ.get("CLAUDE_PROJECTS_ROOT", "")
            or DEFAULT_CLAUDE_PROJECTS_ROOT
        ).expanduser()
        self.include_eval = include_eval
        self.device_id = device_id or self._device_id()
        self.host = socket.gethostname()

    def discover(self, cursor: AdapterCursor) -> list[SourceEvent]:
        files_cursor = cursor.get("files", {})
        if not isinstance(files_cursor, dict):
            files_cursor = {}

        events: list[SourceEvent] = []
        for path in sorted(self.projects_root.glob("*/*.jsonl")):
            if not self.include_eval and "/tests/eval-" in str(path):
                continue
            events.extend(self._read_new_events(path, files_cursor.get(str(path), {})))
        return events

    def normalize(self, event: SourceEvent) -> EventV0 | None:
        raw = event.get("raw")
        if not isinstance(raw, dict):
            return self._error_event(event, "invalid_json", "Invalid Claude Code JSONL row")

        if self._is_noise(raw):
            return None

        action_type = self._action_type(raw)
        if action_type is None:
            return None

        text = self._extract_text(raw)
        summary = self._summary_for(raw, action_type, text)
        if not summary:
            return None

        source_event_id = self._source_event_id(event, raw)
        timestamp = self._timestamp(raw.get("timestamp"))
        cwd = raw.get("cwd") if isinstance(raw.get("cwd"), str) else None
        session_id = self._session_id(event, raw)
        tool_name = self._tool_name(raw)
        status = self._status(raw)

        payload: dict[str, Any] = {
            "claude_type": raw.get("type"),
            "line_index": event.get("line_index"),
            "text_excerpt": self._truncate(text, 2000),
        }
        if tool_name:
            payload["tool_name"] = tool_name
        if raw.get("uuid"):
            payload["uuid"] = raw["uuid"]
        if raw.get("parentUuid"):
            payload["parent_uuid"] = raw["parentUuid"]
        if raw.get("toolUseResult") is not None:
            payload["tool_use_result"] = self._compact_tool_result(raw["toolUseResult"])

        return {
            "schema_version": SCHEMA_VERSION,
            "id": make_event_id(),
            "source_event_id": source_event_id,
            "timestamp": timestamp,
            "ingested_at": self._now(),
            "actor": self._actor(raw),
            "source_type": self.source_type,
            "source": {
                "device_id": self.device_id,
                "host": self.host,
                "process_id": None,
                "session_id": session_id,
            },
            "project": self._project(raw, event),
            "action": {
                "type": action_type,
                "status": status,
                "label": self._label(raw, action_type, tool_name),
            },
            "summary": summary,
            "payload": payload,
            "artifact_refs": self._artifact_refs(raw),
            "session": {"id": session_id, "cwd": cwd} if session_id else None,
            "parent_id": None,
            "thread_id": session_id,
            "tags": self._tags(action_type, tool_name),
            "links": [],
            "metrics": self._metrics(raw),
            "privacy": {"level": "private", "redacted": False},
            "dedupe_key": self._dedupe_key(source_event_id, summary, timestamp),
            "raw_ref": {
                "type": "claude_code_jsonl",
                "uri": f"{event['path']}:{event['line_index']}",
            },
        }

    def _read_new_events(self, path: Path, file_cursor: Any) -> list[SourceEvent]:
        stat = path.stat()
        cursor_data = file_cursor if isinstance(file_cursor, dict) else {}
        offset = int(cursor_data.get("offset", 0) or 0)
        line_index = int(cursor_data.get("line_index", 0) or 0)

        if (
            cursor_data.get("inode") != stat.st_ino
            or int(cursor_data.get("size", 0) or 0) > stat.st_size
        ):
            offset = 0
            line_index = 0

        events: list[SourceEvent] = []
        with path.open("rb") as f:
            f.seek(offset)
            while True:
                line_start = f.tell()
                raw_line = f.readline()
                if not raw_line:
                    break
                next_offset = f.tell()
                line_index += 1
                text = raw_line.decode("utf-8", errors="replace").strip()
                if not text:
                    events.append(self._source_event(path, line_index, line_start, next_offset, stat, None))
                    continue
                try:
                    raw = json.loads(text)
                except json.JSONDecodeError as exc:
                    raw = {"type": "parse_error", "error": str(exc), "line": text[:1000]}
                events.append(self._source_event(path, line_index, line_start, next_offset, stat, raw))
        return events

    def _source_event(
        self,
        path: Path,
        line_index: int,
        offset: int,
        next_offset: int,
        stat: os.stat_result,
        raw: dict[str, Any] | None,
    ) -> SourceEvent:
        return {
            "path": str(path),
            "line_index": line_index,
            "offset": offset,
            "raw": raw,
            "_cursor_update": {
                "files": {
                    str(path): {
                        "inode": stat.st_ino,
                        "mtime_ns": stat.st_mtime_ns,
                        "size": stat.st_size,
                        "offset": next_offset,
                        "line_index": line_index,
                        "last_event_id": self._source_event_id(
                            {"path": str(path), "line_index": line_index},
                            raw or {},
                        ),
                    }
                }
            },
        }

    def _is_noise(self, raw: dict[str, Any]) -> bool:
        raw_type = raw.get("type")
        if raw_type in {"queue-operation", "attachment", "system", "summary"}:
            return True
        if raw.get("isMeta") is True:
            return True
        if raw_type == "assistant":
            text = self._extract_text(raw)
            if self._contains_tool_use(raw):
                return self._tool_name(raw) in {"Read", "Grep", "Glob", "LS"} and not self._raw_has_error(raw)
            return len(text.strip()) < 20 and not self._contains_status_keyword(text)
        if raw_type == "user" and self._contains_tool_result(raw):
            return self._tool_name(raw) in {"Read", "Grep", "Glob", "LS"} and not self._raw_has_error(raw)
        return False

    def _action_type(self, raw: dict[str, Any]) -> str | None:
        if raw.get("type") == "parse_error":
            return "error"
        raw_type = raw.get("type")
        if raw_type == "user":
            if self._contains_tool_result(raw):
                if self._raw_has_error(raw):
                    return "error"
                if self._tool_result_file_path(raw):
                    return "file_changed"
                return "tool_result"
            return "user_request"
        if raw_type == "assistant":
            if self._contains_tool_use(raw):
                return "tool_call"
            text = self._extract_text(raw)
            if self._contains_status_keyword(text) and self._looks_final(text):
                return "session_completed"
            return "agent_response"
        if raw_type == "tool_result":
            return "tool_result"
        if raw_type == "tool_use":
            return "tool_call"
        if raw_type in ACTION_TYPES:
            return raw_type
        return None

    def _actor(self, raw: dict[str, Any]) -> dict[str, str]:
        if raw.get("type") == "user" and not self._contains_tool_result(raw):
            return {"id": "human:local-user", "name": "User", "kind": "human"}
        if raw.get("type") == "user" and self._contains_tool_result(raw):
            return {"id": "system:claude-code-tools", "name": "Claude Code Tools", "kind": "system"}
        return {"id": "claude_code:local-default", "name": "Claude Code", "kind": "agent"}

    def _status(self, raw: dict[str, Any]) -> str:
        if raw.get("type") == "parse_error" or self._raw_has_error(raw):
            return "error"
        text = self._extract_text(raw).lower()
        if any(word in text for word in ("blocked", "cannot", "can't", "failed", "error")):
            return "blocked"
        return "completed"

    def _label(self, raw: dict[str, Any], action_type: str, tool_name: str | None) -> str | None:
        if tool_name:
            return tool_name
        labels = {
            "user_request": "user message",
            "agent_response": "assistant message",
            "session_completed": "session completed",
            "file_changed": "file changed",
            "error": "error",
        }
        return labels.get(action_type)

    def _summary_for(self, raw: dict[str, Any], action_type: str, text: str) -> str:
        tool_name = self._tool_name(raw)
        if action_type == "tool_call" and tool_name:
            return self._truncate(f"Claude Code called {tool_name}.", 240)
        if action_type == "tool_result" and tool_name:
            return self._truncate(f"{tool_name} returned a result.", 240)
        if action_type == "file_changed":
            path = self._tool_result_file_path(raw) or "a file"
            return self._truncate(f"Claude Code changed {path}.", 240)
        if action_type == "error":
            return self._truncate(text or "Claude Code logged an error.", 240)
        clean = " ".join(text.split())
        if not clean:
            clean = action_type.replace("_", " ")
        return self._truncate(clean, 240)

    def _extract_text(self, raw: dict[str, Any]) -> str:
        message = raw.get("message")
        if isinstance(message, dict):
            return self._content_to_text(message.get("content"))
        if isinstance(raw.get("content"), str):
            return raw["content"]
        if isinstance(raw.get("error"), str):
            return raw["error"]
        return ""

    def _content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif item.get("type") == "tool_result" and isinstance(item.get("content"), str):
                    parts.append(item["content"])
            return "\n".join(parts)
        return ""

    def _contains_tool_use(self, raw: dict[str, Any]) -> bool:
        return any(item.get("type") == "tool_use" for item in self._content_items(raw))

    def _contains_tool_result(self, raw: dict[str, Any]) -> bool:
        return any(item.get("type") == "tool_result" for item in self._content_items(raw))

    def _content_items(self, raw: dict[str, Any]) -> list[dict[str, Any]]:
        content = raw.get("message", {}).get("content") if isinstance(raw.get("message"), dict) else None
        return [item for item in content if isinstance(item, dict)] if isinstance(content, list) else []

    def _tool_name(self, raw: dict[str, Any]) -> str | None:
        for item in self._content_items(raw):
            if item.get("type") == "tool_use" and isinstance(item.get("name"), str):
                return item["name"]
        result = raw.get("toolUseResult")
        if isinstance(result, dict) and isinstance(result.get("commandName"), str):
            return result["commandName"]
        return None

    def _tool_result_file_path(self, raw: dict[str, Any]) -> str | None:
        result = raw.get("toolUseResult")
        if isinstance(result, dict):
            for key in ("filePath", "path"):
                if isinstance(result.get(key), str):
                    return result[key]
            if result.get("type") in {"create", "update"} and isinstance(result.get("file"), dict):
                path = result["file"].get("path")
                if isinstance(path, str):
                    return path
        return None

    def _raw_has_error(self, raw: dict[str, Any]) -> bool:
        if raw.get("type") == "parse_error":
            return True
        result = raw.get("toolUseResult")
        if isinstance(result, dict):
            return bool(result.get("is_error") or result.get("error") or result.get("stderr"))
        return False

    def _looks_final(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in ("done", "complete", "completed", "finished", "saved"))

    def _contains_status_keyword(self, text: str) -> bool:
        lowered = text.lower()
        return any(
            word in lowered
            for word in ("done", "complete", "completed", "finished", "saved", "blocked", "error", "failed")
        )

    def _artifact_refs(self, raw: dict[str, Any]) -> list[dict[str, Any]]:
        path = self._tool_result_file_path(raw)
        if not path:
            return []
        return [{"kind": "file", "uri": path, "storage": "local_only", "metadata": {"source": "claude_code"}}]

    def _project(self, raw: dict[str, Any], event: SourceEvent) -> dict[str, Any]:
        cwd = raw.get("cwd") if isinstance(raw.get("cwd"), str) else None
        project_path = cwd or self._decode_project_dir(Path(event["path"]).parent.name)
        name = Path(project_path).name if project_path else "unknown"
        return {
            "name": name or "unknown",
            "path": project_path,
            "id": self._sha256(project_path or name or "unknown")[:16],
            "git_remote": None,
            "git_commit": raw.get("gitBranch") if isinstance(raw.get("gitBranch"), str) else None,
        }

    def _decode_project_dir(self, name: str) -> str | None:
        if not name.startswith("-"):
            return None
        return "/" + name.lstrip("-").replace("--", "/")

    def _session_id(self, event: SourceEvent, raw: dict[str, Any]) -> str:
        if isinstance(raw.get("sessionId"), str):
            return raw["sessionId"]
        return Path(event["path"]).stem

    def _source_event_id(self, event: SourceEvent, raw: dict[str, Any]) -> str:
        session_id = raw.get("sessionId") or Path(event["path"]).stem
        event_id = raw.get("uuid")
        if not event_id and isinstance(raw.get("message"), dict):
            event_id = raw["message"].get("id")
        if not event_id:
            event_id = f"line-{event.get('line_index')}"
        return f"{self.source_type}:{session_id}:{event_id}"

    def _timestamp(self, value: Any) -> str:
        if isinstance(value, str) and value:
            return value.replace("Z", "+00:00")
        return self._now()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _metrics(self, raw: dict[str, Any]) -> dict[str, Any]:
        usage = raw.get("message", {}).get("usage") if isinstance(raw.get("message"), dict) else None
        if not isinstance(usage, dict):
            return {}
        return {
            key: usage[key]
            for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
            if key in usage
        }

    def _compact_tool_result(self, result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            return {}
        compact: dict[str, Any] = {}
        for key in ("type", "filePath", "stdout", "stderr", "interrupted", "is_error", "success", "commandName"):
            if key in result:
                value = result[key]
                compact[key] = self._truncate(value, 4000) if isinstance(value, str) else value
        return compact

    def _tags(self, action_type: str, tool_name: str | None) -> list[str]:
        tags = ["claude_code"]
        if action_type in {"tool_call", "tool_result", "command_run"}:
            tags.append("tool")
        if action_type == "file_changed":
            tags.append("file")
        if action_type == "error":
            tags.append("error")
        if tool_name:
            tags.append(tool_name.lower())
        return tags

    def _error_event(self, event: SourceEvent, code: str, message: str) -> EventV0:
        raw = event.get("raw") if isinstance(event.get("raw"), dict) else {}
        timestamp = self._timestamp(raw.get("timestamp"))
        source_event_id = self._source_event_id(event, raw)
        session_id = self._session_id(event, raw)
        return {
            "schema_version": SCHEMA_VERSION,
            "id": make_event_id(),
            "source_event_id": source_event_id,
            "timestamp": timestamp,
            "ingested_at": self._now(),
            "actor": {"id": "claude_code:local-default", "name": "Claude Code", "kind": "agent"},
            "source_type": self.source_type,
            "source": {"device_id": self.device_id, "host": self.host, "process_id": None, "session_id": session_id},
            "project": self._project(raw, event),
            "action": {"type": "error", "status": "error", "label": code},
            "summary": self._truncate(message, 240),
            "payload": {"code": code, "text_excerpt": self._truncate(raw.get("line", message), 2000)},
            "artifact_refs": [],
            "session": {"id": session_id},
            "parent_id": None,
            "thread_id": session_id,
            "tags": ["claude_code", "error"],
            "links": [],
            "metrics": {},
            "privacy": {"level": "private", "redacted": False},
            "dedupe_key": self._dedupe_key(source_event_id, message, timestamp),
            "raw_ref": {"type": "claude_code_jsonl", "uri": f"{event['path']}:{event['line_index']}"},
        }

    def _device_id(self) -> str:
        env = os.environ.get("AGENTLOG_DEVICE_ID")
        if env:
            return env
        device = config.load_device()
        if device:
            return device.device_id
        return f"{socket.gethostname() or 'device'}-uninitialized"

    def _dedupe_key(self, source_event_id: str, summary: str, timestamp: str) -> str:
        return self._sha256(f"{self.source_type}|{self.device_id}|{source_event_id}|{timestamp}|{summary}")

    def _sha256(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _truncate(self, value: Any, limit: int) -> str:
        text = "" if value is None else str(value)
        text = " ".join(text.split())
        if len(text) <= limit:
            return text
        return text[: limit - 15].rstrip() + " ...[truncated]"
