"""Maestri canvas source adapter."""
from __future__ import annotations

import hashlib
import os
import re
import socket
import subprocess
from datetime import datetime, timezone
from typing import Any

from agentlog import config
from agentlog.adapters.base import AdapterCursor, EventV0, SourceAdapter, SourceEvent
from agentlog.schema import SCHEMA_VERSION, make_event_id


LINE_NUMBER_RE = re.compile(r"^\s*\d+\t")
LIST_NAME_RE = re.compile(r'- name:\s*"([^"]+)"')
HEADER_RE = re.compile(r"^\[[^\]]+\]$")


class MaestriAdapter(SourceAdapter):
    source_type = "maestri"

    def __init__(
        self,
        pool: Any,
        *,
        cursor_path: Any | None = None,
        device_id: str | None = None,
        maestri_cli: str | None = None,
        timeout_seconds: int = 20,
    ) -> None:
        super().__init__(pool, cursor_path=cursor_path)
        self.device_id = device_id or self._device_id()
        self.host = socket.gethostname()
        self.maestri_cli = maestri_cli or os.environ.get("MAESTRI_CLI") or "maestri"
        self.timeout_seconds = timeout_seconds

    def discover(self, cursor: AdapterCursor) -> list[SourceEvent]:
        agents_cursor = cursor.get("agents", {})
        notes_cursor = cursor.get("notes", {})
        if not isinstance(agents_cursor, dict):
            agents_cursor = {}
        if not isinstance(notes_cursor, dict):
            notes_cursor = {}

        listing = self._run(["list"])
        parsed = self._parse_list(listing)
        events: list[SourceEvent] = []
        checked_at = self._now()

        for agent_name in parsed["agents"]:
            output = self._run(["check", agent_name])
            normalized = self._normalize_text(output)
            text_hash = self._hash(normalized)
            lines = self._lines(normalized)
            previous = agents_cursor.get(agent_name, {})
            if not isinstance(previous, dict):
                previous = {}
            event_kind = "agent_created" if "last_hash" not in previous else "agent_changed"
            if event_kind == "agent_created" or previous.get("last_hash") != text_hash:
                tail = self._tail_from_previous(lines, previous.get("last_seen_lines"))
                if event_kind == "agent_created" or tail:
                    events.append(
                        self._source_event(
                            kind=event_kind,
                            name=agent_name,
                            normalized=normalized,
                            text_hash=text_hash,
                            lines_count=len(lines),
                            checked_at=checked_at,
                            tail=tail or normalized,
                        )
                    )

        for note_name in parsed["notes"]:
            output = self._run(["note", "read", note_name])
            normalized = self._normalize_text(output)
            text_hash = self._hash(normalized)
            lines = self._lines(normalized)
            previous = notes_cursor.get(note_name, {})
            if not isinstance(previous, dict):
                previous = {}
            event_kind = "note_created" if "last_hash" not in previous else "note_changed"
            if event_kind == "note_created" or previous.get("last_hash") != text_hash:
                tail = self._tail_from_previous(lines, previous.get("last_seen_lines"))
                events.append(
                    self._source_event(
                        kind=event_kind,
                        name=note_name,
                        normalized=normalized,
                        text_hash=text_hash,
                        lines_count=len(lines),
                        checked_at=checked_at,
                        tail=tail or normalized,
                    )
                )

        return events

    def normalize(self, event: SourceEvent) -> EventV0 | None:
        kind = event["kind"]
        if kind == "agent_created":
            action_type = "session_started"
            summary = f"Maestri agent connected: {event['name']}"
            artifact_refs: list[dict[str, Any]] = []
            actor = {"id": f"maestri:{event['name']}", "name": event["name"], "kind": "agent"}
        elif kind == "agent_changed":
            tail = str(event.get("tail") or "")
            if self._is_noise_tail(tail):
                return None
            action_type = "agent_response" if self._looks_like_agent_response(tail) else "checkpoint"
            summary = self._truncate(f"{event['name']}: {tail}", 240)
            artifact_refs = []
            actor = {"id": f"maestri:{event['name']}", "name": event["name"], "kind": "agent"}
        elif kind == "note_created":
            action_type = "note_created"
            summary = f"Maestri note first seen: {event['name']}"
            artifact_refs = [self._note_ref(event["name"])]
            actor = {"id": "maestri:canvas", "name": "Maestri", "kind": "system"}
        elif kind == "note_changed":
            action_type = "note_updated"
            summary = f"Maestri note updated: {event['name']}"
            artifact_refs = [self._note_ref(event["name"])]
            actor = {"id": "maestri:canvas", "name": "Maestri", "kind": "system"}
        else:
            return None

        timestamp = str(event.get("checked_at") or self._now())
        source_event_id = self._source_event_id(event)
        return {
            "schema_version": SCHEMA_VERSION,
            "id": make_event_id(),
            "source_event_id": source_event_id,
            "timestamp": timestamp,
            "ingested_at": self._now(),
            "actor": actor,
            "source_type": self.source_type,
            "source": {
                "device_id": self.device_id,
                "host": self.host,
                "process_id": None,
                "session_id": event["name"] if kind.startswith("agent") else None,
            },
            "project": {"name": "maestri", "path": None, "id": "maestri", "git_remote": None, "git_commit": None},
            "action": {
                "type": action_type,
                "status": "completed",
                "label": event["name"],
            },
            "summary": summary,
            "payload": {
                "entity_type": "agent" if kind.startswith("agent") else "note",
                "entity_name": event["name"],
                "hash": event["hash"],
                "line_count": event["lines_count"],
                "text_excerpt": self._truncate(str(event.get("tail") or event.get("normalized") or ""), 2000),
            },
            "artifact_refs": artifact_refs,
            "session": {"id": event["name"]} if kind.startswith("agent") else None,
            "parent_id": None,
            "thread_id": event["name"],
            "tags": ["maestri", "agent" if kind.startswith("agent") else "note"],
            "links": [],
            "metrics": {},
            "privacy": {"level": "private", "redacted": False},
            "dedupe_key": self._dedupe_key(source_event_id, summary, timestamp),
            "raw_ref": {"type": "maestri_cli", "uri": f"maestri:{kind}:{event['name']}"},
        }

    def _run(self, args: list[str]) -> str:
        result = subprocess.run(
            [self.maestri_cli, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            detail = stderr or stdout or f"exit {result.returncode}"
            raise RuntimeError(f"maestri {' '.join(args)} failed: {detail}")
        return result.stdout

    def _parse_list(self, text: str) -> dict[str, list[str]]:
        section: str | None = None
        agents: list[str] = []
        notes: list[str] = []
        portals: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("You:"):
                # "You:" lists the local agent itself — `maestri check` cannot
                # target self, so we skip every name under this section.
                section = "_self"
                continue
            if line.startswith("Connected agents:"):
                section = "agents"
                continue
            if line.startswith("Connected notes"):
                section = "notes"
                continue
            if line.startswith("Connected portals"):
                section = "portals"
                continue
            match = LIST_NAME_RE.search(line)
            if not match:
                continue
            name = match.group(1)
            if section == "agents":
                agents.append(name)
            elif section == "notes":
                notes.append(name)
            elif section == "portals":
                portals.append(name)
            # section == "_self" or None: drop silently

        return {
            "agents": list(dict.fromkeys(agents)),
            "notes": list(dict.fromkeys(notes)),
            "portals": list(dict.fromkeys(portals)),
        }

    def _source_event(
        self,
        *,
        kind: str,
        name: str,
        normalized: str,
        text_hash: str,
        lines_count: int,
        checked_at: str,
        tail: str,
    ) -> SourceEvent:
        cursor_key = "agents" if kind.startswith("agent") else "notes"
        return {
            "kind": kind,
            "name": name,
            "normalized": normalized,
            "hash": text_hash,
            "lines_count": lines_count,
            "checked_at": checked_at,
            "tail": tail,
            "_cursor_update": {
                cursor_key: {
                    name: {
                        "last_hash": text_hash,
                        "last_seen_lines": lines_count,
                        "last_checked_at": checked_at,
                    }
                }
            },
        }

    def _normalize_text(self, text: str) -> str:
        lines: list[str] = []
        for raw_line in text.splitlines():
            line = LINE_NUMBER_RE.sub("", raw_line).strip()
            if not line:
                continue
            if HEADER_RE.match(line):
                continue
            if self._is_spinner_or_prompt(line):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _is_spinner_or_prompt(self, line: str) -> bool:
        if line.startswith(("✻", "✳", "❯")):
            return True
        if "Running…" in line or "Running..." in line:
            return True
        if line in {"⏵⏵", "⏺"}:
            return True
        return False

    def _tail_from_previous(self, lines: list[str], previous_count: Any) -> str:
        if isinstance(previous_count, int) and previous_count >= 0:
            return "\n".join(lines[previous_count:])
        return "\n".join(lines)

    def _lines(self, normalized: str) -> list[str]:
        return [line for line in normalized.splitlines() if line.strip()]

    def _is_noise_tail(self, tail: str) -> bool:
        lines = self._lines(self._normalize_text(tail))
        return not lines

    def _looks_like_agent_response(self, tail: str) -> bool:
        lowered = tail.lower()
        return any(word in lowered for word in ("done", "complete", "completed", "finished", "blocked", "error", "note:"))

    def _note_ref(self, note_name: str) -> dict[str, Any]:
        return {"kind": "note", "uri": note_name, "storage": "external", "metadata": {"source": "maestri"}}

    def _source_event_id(self, event: SourceEvent) -> str:
        entity = "agent" if str(event["kind"]).startswith("agent") else "note"
        return f"maestri:{entity}:{event['name']}:{event['hash']}"

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
        return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _truncate(self, value: Any, limit: int) -> str:
        text = "" if value is None else str(value)
        text = " ".join(text.split())
        if len(text) <= limit:
            return text
        return text[: limit - 15].rstrip() + " ...[truncated]"
