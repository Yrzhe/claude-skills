"""Codex rollout JSONL source adapter."""
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


DEFAULT_CODEX_SESSIONS_ROOT = Path("~/.codex/sessions").expanduser()
DEFAULT_CODEX_ARCHIVE_ROOT = Path("~/.codex/archived_sessions").expanduser()
PROGRESS_CHECKPOINT_SECONDS = 30


class CodexAdapter(SourceAdapter):
    source_type = "codex"

    def __init__(
        self,
        pool: Any,
        *,
        sessions_root: Path | None = None,
        archive_root: Path | None = None,
        cursor_path: Path | None = None,
        include_archive: bool = False,
        from_date: str | None = None,
        device_id: str | None = None,
    ) -> None:
        super().__init__(pool, cursor_path=cursor_path)
        self.sessions_root = Path(
            sessions_root
            or os.environ.get("CODEX_SESSIONS_ROOT", "")
            or DEFAULT_CODEX_SESSIONS_ROOT
        ).expanduser()
        self.archive_root = Path(
            archive_root
            or os.environ.get("CODEX_ARCHIVE_ROOT", "")
            or DEFAULT_CODEX_ARCHIVE_ROOT
        ).expanduser()
        self.include_archive = include_archive
        self.from_date = from_date
        self.device_id = device_id or self._device_id()
        self.host = socket.gethostname()
        self._session_meta_by_file: dict[str, dict[str, Any]] = {}
        self._turn_context_by_file: dict[str, dict[str, Any]] = {}
        self._last_checkpoint_at: dict[str, datetime] = {}

    def discover(self, cursor: AdapterCursor) -> list[SourceEvent]:
        files_cursor = cursor.get("files", {})
        if not isinstance(files_cursor, dict):
            files_cursor = {}

        events: list[SourceEvent] = []
        for path in self._candidate_files():
            events.extend(self._read_new_events(path, files_cursor.get(str(path), {})))
        return events

    def normalize(self, event: SourceEvent) -> EventV0 | None:
        raw = event.get("raw")
        if not isinstance(raw, dict):
            return self._error_event(event, "invalid_json", "Invalid Codex JSONL row")

        self._remember_context(event, raw)

        if self._is_noise(event, raw):
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
        session_id = self._session_id(event, raw)
        cwd = self._cwd(event, raw)
        tool_name = self._tool_name(raw)

        payload: dict[str, Any] = {
            "codex_type": raw.get("type"),
            "line_index": event.get("line_index"),
            "text_excerpt": self._truncate(text, 2000),
        }
        raw_payload = raw.get("payload")
        if isinstance(raw_payload, dict):
            payload["payload_type"] = raw_payload.get("type")
            payload["phase"] = raw_payload.get("phase")
            if tool_name:
                payload["tool_name"] = tool_name
            if raw_payload.get("call_id"):
                payload["call_id"] = raw_payload["call_id"]
            if raw_payload.get("exit_code") is not None:
                payload["exit_code"] = raw_payload["exit_code"]

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
                "process_id": self._process_id(raw),
                "session_id": session_id,
            },
            "project": self._project(event, raw),
            "action": {
                "type": action_type,
                "status": self._status(raw),
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
                "type": "codex_rollout_jsonl",
                "uri": f"{event['path']}:{event['line_index']}",
            },
        }

    def _candidate_files(self) -> list[Path]:
        paths: list[Path] = []
        if self.sessions_root.exists():
            paths.extend(self.sessions_root.glob("*/*/*/rollout-*.jsonl"))
        if self.include_archive and self.archive_root.exists():
            paths.extend(self.archive_root.glob("rollout-*.jsonl"))
        return sorted(path for path in paths if self._passes_from_date(path))

    def _passes_from_date(self, path: Path) -> bool:
        if not self.from_date:
            return True
        file_date = self._date_from_path(path)
        return file_date is None or file_date >= self.from_date

    def _date_from_path(self, path: Path) -> str | None:
        parts = path.parts
        if len(parts) >= 4 and all(part.isdigit() for part in parts[-4:-1]):
            return "-".join(parts[-4:-1])
        name = path.name
        if name.startswith("rollout-") and len(name) >= 18:
            return name[8:18]
        return None

    def _read_new_events(self, path: Path, file_cursor: Any) -> list[SourceEvent]:
        stat = path.stat()
        cursor_data = file_cursor if isinstance(file_cursor, dict) else {}
        offset = int(cursor_data.get("offset", 0) or 0)
        line_index = int(cursor_data.get("line_index", 0) or 0)
        session_id = cursor_data.get("session_id") if isinstance(cursor_data.get("session_id"), str) else None

        if (
            cursor_data.get("inode") != stat.st_ino
            or int(cursor_data.get("size", 0) or 0) > stat.st_size
        ):
            offset = 0
            line_index = 0
            session_id = None

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
                    raw = None
                else:
                    try:
                        raw = json.loads(text)
                    except json.JSONDecodeError as exc:
                        raw = {"type": "parse_error", "error": str(exc), "line": text[:1000]}
                if isinstance(raw, dict) and raw.get("type") == "session_meta":
                    payload = raw.get("payload")
                    if isinstance(payload, dict) and isinstance(payload.get("id"), str):
                        session_id = payload["id"]
                events.append(
                    self._source_event(path, line_index, line_start, next_offset, stat, raw, session_id)
                )
        return events

    def _source_event(
        self,
        path: Path,
        line_index: int,
        offset: int,
        next_offset: int,
        stat: os.stat_result,
        raw: dict[str, Any] | None,
        session_id: str | None,
    ) -> SourceEvent:
        source_event = {
            "path": str(path),
            "line_index": line_index,
            "offset": offset,
            "raw": raw,
        }
        last_event_id = self._source_event_id(source_event, raw or {})
        return {
            **source_event,
            "_cursor_update": {
                "files": {
                    str(path): {
                        "inode": stat.st_ino,
                        "mtime_ns": stat.st_mtime_ns,
                        "size": stat.st_size,
                        "offset": next_offset,
                        "line_index": line_index,
                        "session_id": session_id or self._session_id(source_event, raw or {}),
                        "last_event_id": last_event_id,
                    }
                }
            },
        }

    def _remember_context(self, event: SourceEvent, raw: dict[str, Any]) -> None:
        path = str(event["path"])
        if raw.get("type") == "session_meta" and isinstance(raw.get("payload"), dict):
            self._session_meta_by_file[path] = raw["payload"]
        if raw.get("type") == "turn_context" and isinstance(raw.get("payload"), dict):
            self._turn_context_by_file[path] = raw["payload"]

    def _is_noise(self, event: SourceEvent, raw: dict[str, Any]) -> bool:
        raw_type = raw.get("type")
        if raw_type in {"session_meta", "turn_context"}:
            return True
        payload = raw.get("payload")
        payload_type = payload.get("type") if isinstance(payload, dict) else None
        if raw_type == "response_item" and payload_type in {"reasoning"}:
            return True
        if raw_type == "response_item" and self._is_memory_citation_message(payload):
            return True
        if raw_type == "event_msg":
            if payload_type == "token_count":
                return True
            if payload_type in {"exec_command_end", "tool_result"}:
                return self._empty_successful_read_result(payload)
            if self._is_repeated_wait_or_poll(payload):
                return True
            if payload_type in {"agent_message", "user_message"}:
                return not self._should_emit_progress_checkpoint(event, raw)
        return False

    def _action_type(self, raw: dict[str, Any]) -> str | None:
        raw_type = raw.get("type")
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        payload_type = payload.get("type")
        if raw_type == "parse_error":
            return "error"
        if raw_type == "event_msg":
            if payload_type == "exec_command_end":
                return "command_run"
            if payload_type in {"agent_message", "user_message"}:
                return "checkpoint"
            if self._is_error_payload(payload):
                return "error"
            return None
        if raw_type != "response_item":
            return None
        if payload_type == "message":
            role = payload.get("role")
            if role == "user":
                return "user_request"
            if role == "assistant":
                text = self._extract_text(raw)
                if self._looks_final(text):
                    return "session_completed"
                return "agent_response"
            return None
        if payload_type == "function_call":
            name = payload.get("name")
            if name == "apply_patch":
                return "file_changed"
            return "tool_call"
        if payload_type == "function_call_output":
            if self._is_error_payload(payload):
                return "error"
            return "tool_result"
        return None

    def _should_emit_progress_checkpoint(self, event: SourceEvent, raw: dict[str, Any]) -> bool:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        message = str(payload.get("message") or "")
        if self._contains_result_keyword(message):
            return True
        session_id = self._session_id(event, raw)
        timestamp = self._datetime(raw.get("timestamp"))
        last = self._last_checkpoint_at.get(session_id)
        if last is not None and (timestamp - last).total_seconds() < PROGRESS_CHECKPOINT_SECONDS:
            return False
        self._last_checkpoint_at[session_id] = timestamp
        return True

    def _actor(self, raw: dict[str, Any]) -> dict[str, str]:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        if payload.get("role") == "user" or payload.get("type") == "user_message":
            return {"id": "human:local-user", "name": "User", "kind": "human"}
        if raw.get("type") == "event_msg" and payload.get("type") in {"exec_command_end", "tool_result"}:
            return {"id": "system:codex-tools", "name": "Codex Tools", "kind": "system"}
        return {"id": "codex:local-default", "name": "Codex", "kind": "agent"}

    def _status(self, raw: dict[str, Any]) -> str:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        if raw.get("type") == "parse_error" or self._is_error_payload(payload):
            return "error"
        text = self._extract_text(raw).lower()
        if any(word in text for word in ("blocked", "cannot", "can't", "failed", "error")):
            return "blocked"
        if payload.get("status") == "in_progress":
            return "in_progress"
        return "completed"

    def _label(self, raw: dict[str, Any], action_type: str, tool_name: str | None) -> str | None:
        if tool_name:
            return tool_name
        labels = {
            "user_request": "user message",
            "agent_response": "assistant message",
            "session_completed": "session completed",
            "command_run": "command run",
            "file_changed": "file changed",
            "checkpoint": "checkpoint",
            "error": "error",
        }
        return labels.get(action_type)

    def _summary_for(self, raw: dict[str, Any], action_type: str, text: str) -> str:
        tool_name = self._tool_name(raw)
        if action_type == "tool_call" and tool_name:
            return self._truncate(f"Codex called {tool_name}.", 240)
        if action_type == "file_changed":
            return self._truncate("Codex applied a file patch.", 240)
        if action_type == "command_run":
            command = self._command_summary(raw)
            return self._truncate(f"Codex ran command: {command}", 240)
        clean = " ".join(text.split())
        if clean:
            return self._truncate(clean, 240)
        if action_type == "tool_result" and tool_name:
            return self._truncate(f"{tool_name} returned a result.", 240)
        return action_type.replace("_", " ")

    def _extract_text(self, raw: dict[str, Any]) -> str:
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            if isinstance(raw.get("error"), str):
                return raw["error"]
            return ""
        if isinstance(payload.get("message"), str):
            return payload["message"]
        if isinstance(payload.get("output"), str):
            return payload["output"]
        if isinstance(payload.get("aggregated_output"), str):
            return payload["aggregated_output"]
        content = payload.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("output_text"), str):
                    parts.append(item["output_text"])
            return "\n".join(parts)
        if isinstance(payload.get("arguments"), str):
            return payload["arguments"]
        return ""

    def _tool_name(self, raw: dict[str, Any]) -> str | None:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        if isinstance(payload.get("name"), str):
            return payload["name"]
        parsed = payload.get("parsed_cmd")
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
            return parsed[0].get("type")
        return None

    def _command_summary(self, raw: dict[str, Any]) -> str:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        command = payload.get("command")
        if isinstance(command, list):
            return " ".join(str(part) for part in command)
        arguments = payload.get("arguments")
        if isinstance(arguments, str):
            try:
                data = json.loads(arguments)
                if isinstance(data, dict) and isinstance(data.get("cmd"), str):
                    return data["cmd"]
            except json.JSONDecodeError:
                return arguments
        return "unknown"

    def _artifact_refs(self, raw: dict[str, Any]) -> list[dict[str, Any]]:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        refs: list[dict[str, Any]] = []
        parsed = payload.get("parsed_cmd")
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and isinstance(item.get("path"), str):
                    refs.append(
                        {
                            "kind": "file",
                            "uri": item["path"],
                            "storage": "local_only",
                            "metadata": {"source": "codex", "cmd_type": item.get("type")},
                        }
                    )
        if payload.get("name") == "apply_patch":
            refs.append(
                {
                    "kind": "diff",
                    "uri": "codex:apply_patch",
                    "storage": "local_only",
                    "metadata": {"call_id": payload.get("call_id")},
                }
            )
        return refs

    def _project(self, event: SourceEvent, raw: dict[str, Any]) -> dict[str, Any]:
        cwd = self._cwd(event, raw)
        name = Path(cwd).name if cwd else "unknown"
        return {
            "name": name or "unknown",
            "path": cwd,
            "id": self._sha256(cwd or name or "unknown")[:16],
            "git_remote": None,
            "git_commit": None,
        }

    def _cwd(self, event: SourceEvent, raw: dict[str, Any]) -> str | None:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        if isinstance(payload.get("cwd"), str):
            return payload["cwd"]
        if isinstance(payload.get("arguments"), str):
            try:
                args = json.loads(payload["arguments"])
                if isinstance(args, dict) and isinstance(args.get("workdir"), str):
                    return args["workdir"]
            except json.JSONDecodeError:
                pass
        path = str(event["path"])
        context = self._turn_context_by_file.get(path)
        if isinstance(context, dict) and isinstance(context.get("cwd"), str):
            return context["cwd"]
        meta = self._session_meta_by_file.get(path)
        if isinstance(meta, dict) and isinstance(meta.get("cwd"), str):
            return meta["cwd"]
        return None

    def _session_id(self, event: SourceEvent, raw: dict[str, Any]) -> str:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        if isinstance(payload.get("id"), str) and raw.get("type") == "session_meta":
            return payload["id"]
        if isinstance(payload.get("session_id"), str):
            return payload["session_id"]
        path = str(event["path"])
        meta = self._session_meta_by_file.get(path)
        if isinstance(meta, dict) and isinstance(meta.get("id"), str):
            return meta["id"]
        return Path(path).stem.replace("rollout-", "")

    def _process_id(self, raw: dict[str, Any]) -> str | None:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        process_id = payload.get("process_id")
        return f"pid-{process_id}" if process_id is not None else None

    def _source_event_id(self, event: SourceEvent, raw: dict[str, Any]) -> str:
        session_id = self._session_id(event, raw)
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        item_id = payload.get("id") or payload.get("call_id")
        if not item_id:
            item_id = f"line-{event.get('line_index')}:{raw.get('type', 'unknown')}"
        return f"{self.source_type}:{session_id}:{item_id}"

    def _timestamp(self, value: Any) -> str:
        if isinstance(value, str) and value:
            return value.replace("Z", "+00:00")
        return self._now()

    def _datetime(self, value: Any) -> datetime:
        if isinstance(value, str) and value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.now(timezone.utc)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _metrics(self, raw: dict[str, Any]) -> dict[str, Any]:
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            return {}
        return {
            key: usage[key]
            for key in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens")
            if key in usage
        }

    def _tags(self, action_type: str, tool_name: str | None) -> list[str]:
        tags = ["codex"]
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
            "actor": {"id": "codex:local-default", "name": "Codex", "kind": "agent"},
            "source_type": self.source_type,
            "source": {"device_id": self.device_id, "host": self.host, "process_id": None, "session_id": session_id},
            "project": self._project(event, raw),
            "action": {"type": "error", "status": "error", "label": code},
            "summary": self._truncate(message, 240),
            "payload": {"code": code, "text_excerpt": self._truncate(raw.get("line", message), 2000)},
            "artifact_refs": [],
            "session": {"id": session_id, "cwd": self._cwd(event, raw)},
            "parent_id": None,
            "thread_id": session_id,
            "tags": ["codex", "error"],
            "links": [],
            "metrics": {},
            "privacy": {"level": "private", "redacted": False},
            "dedupe_key": self._dedupe_key(source_event_id, message, timestamp),
            "raw_ref": {"type": "codex_rollout_jsonl", "uri": f"{event['path']}:{event['line_index']}"},
        }

    def _is_error_payload(self, payload: dict[str, Any]) -> bool:
        if payload.get("is_error") is True:
            return True
        if payload.get("exit_code") not in (None, 0):
            return True
        status = payload.get("status")
        return status == "error"

    def _contains_result_keyword(self, text: str) -> bool:
        lowered = text.lower()
        return any(
            word in lowered
            for word in ("done", "complete", "completed", "finished", "saved", "blocked", "error", "failed")
        )

    def _looks_final(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in ("done", "complete", "completed", "finished", "saved"))

    def _empty_successful_read_result(self, payload: dict[str, Any]) -> bool:
        if self._is_error_payload(payload):
            return False
        output = payload.get("aggregated_output") or payload.get("output") or payload.get("stdout")
        parsed = payload.get("parsed_cmd")
        is_read = isinstance(parsed, list) and any(
            isinstance(item, dict) and item.get("type") == "read" for item in parsed
        )
        return is_read and not str(output or "").strip()

    def _is_repeated_wait_or_poll(self, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        name = str(payload.get("name") or payload.get("tool_name") or "")
        message = str(payload.get("message") or "")
        return name in {"wait_agent", "poll"} or message.startswith("Running…")

    def _is_memory_citation_message(self, payload: Any) -> bool:
        if not isinstance(payload, dict) or payload.get("type") != "message":
            return False
        text = self._extract_text({"payload": payload})
        return text.strip().startswith("<oai-mem-citation>")

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
