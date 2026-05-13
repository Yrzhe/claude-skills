"""Cursor IDE chat history adapter.

Reads Cursor's per-workspace state.vscdb SQLite file and emits one
EventV0 per chat bubble. Designed to tolerate Cursor schema drift:
unknown keys are skipped with a logger.warning, never crashed on.

Cursor stores chat data in `ItemTable` at the key
`workbench.panel.aichat.view.aichat.chatdata` as a JSON blob of shape:
    {
      "tabs": [
        {"tabId": str, "chatTitle": str|None,
         "bubbles": [{"type": "user"|"ai", "text": str, ...}, ...]}
      ]
    }
Schema may evolve; this adapter degrades to "emit nothing for this
workspace" rather than crashing the whole poll.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import socket
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from agentlog import config
from agentlog.adapters.base import AdapterCursor, EventV0, SourceAdapter, SourceEvent
from agentlog.schema import SCHEMA_VERSION, make_event_id


logger = logging.getLogger(__name__)

DEFAULT_CURSOR_STORAGE_ROOT = (
    Path("~/Library/Application Support/Cursor/User/workspaceStorage").expanduser()
)
CHATDATA_KEY = "workbench.panel.aichat.view.aichat.chatdata"


class CursorAdapter(SourceAdapter):
    source_type = "cursor"

    def __init__(
        self,
        pool: Any,
        *,
        storage_root: Path | None = None,
        cursor_path: Path | None = None,
        device_id: str | None = None,
    ) -> None:
        super().__init__(pool, cursor_path=cursor_path)
        self.storage_root = Path(
            storage_root
            or os.environ.get("CURSOR_STORAGE_ROOT", "")
            or DEFAULT_CURSOR_STORAGE_ROOT
        ).expanduser()
        self.device_id = device_id or self._device_id()
        self.host = socket.gethostname()

    def discover(self, cursor: AdapterCursor) -> list[SourceEvent]:
        if not self.storage_root.exists():
            return []
        workspaces_cursor = cursor.get("workspaces", {})
        if not isinstance(workspaces_cursor, dict):
            workspaces_cursor = {}

        events: list[SourceEvent] = []
        for ws_dir in sorted(p for p in self.storage_root.iterdir() if p.is_dir()):
            workspace_hash = ws_dir.name
            ws_cursor = workspaces_cursor.get(workspace_hash, {})
            if not isinstance(ws_cursor, dict):
                ws_cursor = {}
            events.extend(self._read_workspace(ws_dir, workspace_hash, ws_cursor))
        return events

    def _read_workspace(
        self,
        ws_dir: Path,
        workspace_hash: str,
        ws_cursor: dict[str, Any],
    ) -> list[SourceEvent]:
        db = ws_dir / "state.vscdb"
        if not db.exists():
            return []
        chat_data = self._load_chatdata(db, workspace_hash)
        if chat_data is None:
            return []

        folder_path = self._workspace_folder(ws_dir)
        project_name = self._project_name(folder_path)

        tabs_cursor = ws_cursor.get("tabs", {})
        if not isinstance(tabs_cursor, dict):
            tabs_cursor = {}

        events: list[SourceEvent] = []
        tabs = chat_data.get("tabs") if isinstance(chat_data, dict) else None
        if not isinstance(tabs, list):
            logger.warning(
                "cursor workspace %s chatdata has no `tabs` array; skipping",
                workspace_hash,
            )
            return []

        for tab in tabs:
            if not isinstance(tab, dict):
                continue
            tab_id = self._tab_id(tab)
            bubbles = tab.get("bubbles")
            if not isinstance(bubbles, list):
                continue

            already_emitted = int(tabs_cursor.get(tab_id, 0) or 0)
            for idx, bubble in enumerate(bubbles):
                if idx < already_emitted:
                    continue
                if not isinstance(bubble, dict):
                    continue
                is_last = idx == len(bubbles) - 1
                events.append(
                    self._source_event(
                        workspace_hash=workspace_hash,
                        folder_path=folder_path,
                        project_name=project_name,
                        tab_id=tab_id,
                        chat_title=tab.get("chatTitle"),
                        bubble_idx=idx,
                        bubble=bubble,
                        is_last=is_last,
                        total_bubbles=len(bubbles),
                    )
                )
        return events

    def normalize(self, event: SourceEvent) -> EventV0 | None:
        bubble = event["bubble"]
        text = self._bubble_text(bubble)
        if not text:
            return None

        bubble_type = bubble.get("type")
        if bubble_type == "user":
            action_type = "user_request"
            actor = {"id": "human:local-user", "name": "User", "kind": "human"}
        elif bubble_type == "ai":
            action_type = "session_completed" if event["is_last"] else "agent_response"
            actor = {"id": "cursor:local-default", "name": "Cursor", "kind": "agent"}
        else:
            return None

        workspace_hash = event["workspace_hash"]
        tab_id = event["tab_id"]
        session_id = f"{workspace_hash}:{tab_id}"
        source_event_id = f"cursor:{workspace_hash}:{tab_id}:{event['bubble_idx']}"
        timestamp = self._now()

        summary = self._truncate(" ".join(text.split()), 240) or "(empty)"

        return {
            "schema_version": SCHEMA_VERSION,
            "id": make_event_id(),
            "source_event_id": source_event_id,
            "timestamp": timestamp,
            "ingested_at": timestamp,
            "actor": actor,
            "source_type": self.source_type,
            "source": {
                "device_id": self.device_id,
                "host": self.host,
                "process_id": None,
                "session_id": session_id,
            },
            "project": {
                "name": event["project_name"],
                "path": event["folder_path"],
                "id": self._sha256(event["folder_path"] or event["project_name"])[:16],
                "git_remote": None,
                "git_commit": None,
            },
            "action": {
                "type": action_type,
                "status": "completed",
                "label": event.get("chat_title") or "cursor chat",
            },
            "summary": summary,
            "payload": {
                "bubble_type": bubble_type,
                "bubble_idx": event["bubble_idx"],
                "tab_id": tab_id,
                "text_excerpt": self._truncate(text, 2000),
            },
            "artifact_refs": [],
            "session": {"id": session_id, "cwd": event["folder_path"]},
            "parent_id": None,
            "thread_id": session_id,
            "tags": ["cursor", bubble_type],
            "links": [],
            "metrics": {},
            "privacy": {"level": "private", "redacted": False},
            "dedupe_key": self._dedupe_key(source_event_id, summary, timestamp),
            "raw_ref": {
                "type": "cursor_state_vscdb",
                "uri": f"workspaceStorage/{workspace_hash}/state.vscdb#{tab_id}:{event['bubble_idx']}",
            },
        }

    def _source_event(
        self,
        *,
        workspace_hash: str,
        folder_path: str | None,
        project_name: str,
        tab_id: str,
        chat_title: Any,
        bubble_idx: int,
        bubble: dict[str, Any],
        is_last: bool,
        total_bubbles: int,
    ) -> SourceEvent:
        return {
            "workspace_hash": workspace_hash,
            "folder_path": folder_path,
            "project_name": project_name,
            "tab_id": tab_id,
            "chat_title": chat_title if isinstance(chat_title, str) else None,
            "bubble_idx": bubble_idx,
            "bubble": bubble,
            "is_last": is_last,
            "_cursor_update": {
                "workspaces": {
                    workspace_hash: {
                        "tabs": {tab_id: bubble_idx + 1},
                        "last_seen_total": total_bubbles,
                    }
                }
            },
        }

    def _load_chatdata(self, db: Path, workspace_hash: str) -> Any:
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        except sqlite3.Error as exc:
            logger.warning("cursor: cannot open %s: %s", db, exc)
            return None
        try:
            cur = conn.execute(
                "SELECT value FROM ItemTable WHERE key = ?", (CHATDATA_KEY,)
            )
            row = cur.fetchone()
        except sqlite3.Error as exc:
            logger.warning(
                "cursor workspace %s: ItemTable read failed: %s",
                workspace_hash,
                exc,
            )
            return None
        finally:
            conn.close()

        if row is None:
            return None
        value = row[0]
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8")
            except UnicodeDecodeError as exc:
                logger.warning(
                    "cursor workspace %s: chatdata not utf-8: %s",
                    workspace_hash,
                    exc,
                )
                return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            logger.warning(
                "cursor workspace %s: chatdata not valid JSON: %s",
                workspace_hash,
                exc,
            )
            return None

    def _workspace_folder(self, ws_dir: Path) -> str | None:
        ws_json = ws_dir / "workspace.json"
        if not ws_json.exists():
            return None
        try:
            data = json.loads(ws_json.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        folder = data.get("folder") if isinstance(data, dict) else None
        if not isinstance(folder, str):
            return None
        if folder.startswith("file://"):
            return unquote(urlparse(folder).path)
        return folder

    @staticmethod
    def _project_name(folder_path: str | None) -> str:
        if not folder_path:
            return "unknown"
        return Path(folder_path).name or "unknown"

    @staticmethod
    def _tab_id(tab: dict[str, Any]) -> str:
        tab_id = tab.get("tabId")
        if isinstance(tab_id, str) and tab_id:
            return tab_id
        return "default"

    @staticmethod
    def _bubble_text(bubble: dict[str, Any]) -> str:
        for key in ("text", "content", "message"):
            value = bubble.get(key)
            if isinstance(value, str):
                return value
        return ""

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _device_id(self) -> str:
        env = os.environ.get("AGENTLOG_DEVICE_ID")
        if env:
            return env
        device = config.load_device()
        if device:
            return device.device_id
        return f"{socket.gethostname() or 'device'}-uninitialized"

    def _dedupe_key(self, source_event_id: str, summary: str, timestamp: str) -> str:
        return self._sha256(
            f"{self.source_type}|{self.device_id}|{source_event_id}|{timestamp}|{summary}"
        )

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _truncate(value: Any, limit: int) -> str:
        text = "" if value is None else str(value)
        if len(text) <= limit:
            return text
        return text[: limit - 15].rstrip() + " ...[truncated]"
