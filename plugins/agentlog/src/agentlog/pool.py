from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fcntl

from .schema import EventValidationError, normalize_dedupe_key, validate


DEFAULT_SHARD_MAX_BYTES = 64 * 1024 * 1024
SOURCE_EVENT_RING_SIZE = 5_000


@dataclass(frozen=True)
class AppendResult:
    ok: bool
    event_id: str
    shard_path: Path
    duplicate: bool
    error: str | None = None


class Pool:
    def __init__(
        self,
        root_dir: Path,
        device_id: str,
        *,
        shard_max_bytes: int = DEFAULT_SHARD_MAX_BYTES,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.device_id = device_id
        self.shard_max_bytes = shard_max_bytes
        self.state_dir = self.root_dir / "state"
        self.cursor_dir = self.state_dir / "cursors"
        self.quarantine_dir = self.state_dir / "quarantine"
        self.lock_path = self.state_dir / "pool.lock"
        self.source_event_index_path = self.cursor_dir / "source_event_ids.jsonl"
        self._source_event_ring: deque[str] = deque(maxlen=SOURCE_EVENT_RING_SIZE)
        self._source_event_map: dict[str, tuple[str, Path]] = {}

        self.cursor_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self._load_source_event_index()

    def append(self, event: dict[str, Any], *, flush: bool = False) -> AppendResult:
        event_to_write = dict(event)
        try:
            validate(event_to_write)
            event_to_write.setdefault("dedupe_key", normalize_dedupe_key(event_to_write))
        except EventValidationError as exc:
            self._write_quarantine(event, str(exc))
            raise

        source_event_id = event_to_write["source_event_id"]
        with self._locked():
            duplicate = self._source_event_map.get(source_event_id)
            if duplicate is not None:
                event_id, shard_path = duplicate
                return AppendResult(
                    ok=True,
                    event_id=event_id,
                    shard_path=shard_path,
                    duplicate=True,
                )

            shard_path = self._current_shard_path(event_to_write)
            line = json.dumps(event_to_write, ensure_ascii=False, sort_keys=True) + "\n"
            self._append_line(shard_path, line, flush=True)
            json.loads(line)

            self._record_source_event_id(
                source_event_id=source_event_id,
                event_id=event_to_write["id"],
                shard_path=shard_path,
            )

        return AppendResult(
            ok=True,
            event_id=event_to_write["id"],
            shard_path=shard_path,
            duplicate=False,
        )

    def _load_source_event_index(self) -> None:
        if not self.source_event_index_path.exists():
            return

        entries: deque[dict[str, Any]] = deque(maxlen=SOURCE_EVENT_RING_SIZE)
        with self.source_event_index_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        for entry in entries:
            source_event_id = entry.get("source_event_id")
            event_id = entry.get("event_id")
            shard_path = entry.get("shard_path")
            if not source_event_id or not event_id or not shard_path:
                continue
            self._source_event_ring.append(source_event_id)
            self._source_event_map[source_event_id] = (
                event_id,
                self.root_dir / shard_path,
            )

    def _record_source_event_id(
        self, *, source_event_id: str, event_id: str, shard_path: Path
    ) -> None:
        if (
            len(self._source_event_ring) == SOURCE_EVENT_RING_SIZE
            and source_event_id not in self._source_event_map
        ):
            oldest = self._source_event_ring[0]
            self._source_event_map.pop(oldest, None)
        self._source_event_ring.append(source_event_id)
        self._source_event_map[source_event_id] = (event_id, shard_path)

        record = {
            "source_event_id": source_event_id,
            "event_id": event_id,
            "shard_path": str(shard_path.relative_to(self.root_dir)),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
        line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        self._append_line(self.source_event_index_path, line, flush=True)

    def _current_shard_path(self, event: dict[str, Any]) -> Path:
        day = _event_day(event)
        source_type = event["source_type"]
        shard_dir = (
            self.root_dir
            / "pool"
            / f"dt={day}"
            / f"device={self.device_id}"
            / f"source={source_type}"
        )
        shard_dir.mkdir(parents=True, exist_ok=True)

        shard_number = 0
        while True:
            candidate = shard_dir / f"shard-{shard_number:03d}.jsonl"
            if not candidate.exists() or candidate.stat().st_size < self.shard_max_bytes:
                return candidate
            shard_number += 1

    def _write_quarantine(self, event: dict[str, Any], error: str) -> None:
        day = _best_effort_day(event)
        path = self.quarantine_dir / f"{day}.jsonl"
        record = {
            "error": error,
            "event": event,
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
        }
        line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        with self._locked():
            self._append_line(path, line, flush=True)

    def _append_line(self, path: Path, line: str, *, flush: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(line)
            if flush:
                file.flush()
                os.fsync(file.fileno())

    def _locked(self) -> _FileLock:
        return _FileLock(self.lock_path)


class _FileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._file: Any = None

    def __enter__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a+", encoding="utf-8")
        fcntl.flock(self._file.fileno(), fcntl.LOCK_EX)
        return None

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._file is None:
            return
        fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()


def _event_day(event: dict[str, Any]) -> str:
    return datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).date().isoformat()


def _best_effort_day(event: dict[str, Any]) -> str:
    for field in ("timestamp", "ingested_at"):
        value = event.get(field)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                pass
    return datetime.now(timezone.utc).date().isoformat()
