"""Source adapter base class."""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from agentlog.config import cursors_dir


AdapterCursor = dict[str, Any]
SourceEvent = dict[str, Any]
EventV0 = dict[str, Any]


class SourceAdapter(ABC):
    """Base class for adapters that normalize external logs into EventV0."""

    source_type: str

    def __init__(self, pool: Any, *, cursor_path: Path | None = None) -> None:
        self.pool = pool
        self.cursor_path = cursor_path or cursors_dir() / f"{self.source_type}.json"

    def loadCursor(self) -> AdapterCursor:
        if not self.cursor_path.exists():
            return {}
        with self.cursor_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"cursor must be a JSON object: {self.cursor_path}")
        return data

    def saveCursor(self, cursor: AdapterCursor) -> None:
        self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cursor_path.with_name(f".{self.cursor_path.name}.{os.getpid()}.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(cursor, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(self.cursor_path)

    @abstractmethod
    def discover(self, cursor: AdapterCursor) -> list[SourceEvent]:
        """Return source events after the current cursor."""

    @abstractmethod
    def normalize(self, event: SourceEvent) -> EventV0 | None:
        """Convert a source event to EventV0, or return None for noise."""

    def pollOnce(self) -> dict[str, Any]:
        cursor = self.loadCursor()
        emitted = 0
        skipped = 0

        for source_event in self.discover(cursor):
            event = self.normalize(source_event)
            if event is None:
                skipped += 1
                self.advanceCursor(cursor, source_event, None)
                self.saveCursor(cursor)
                continue

            flush = event.get("action", {}).get("type") == "session_completed"
            result = self.pool.append(event, flush=flush)
            emitted += 1
            self.advanceCursor(cursor, source_event, result)
            self.saveCursor(cursor)

        return {"emitted": emitted, "skipped": skipped, "cursor": cursor}

    def advanceCursor(
        self,
        cursor: AdapterCursor,
        source_event: SourceEvent,
        append_result: Any | None,
    ) -> None:
        update = source_event.get("_cursor_update")
        if isinstance(update, dict):
            self._deep_merge(cursor, update)

    def _deep_merge(self, target: AdapterCursor, update: AdapterCursor) -> None:
        for key, value in update.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
