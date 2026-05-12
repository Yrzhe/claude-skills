"""Pool reader — walks shards and yields filtered events.

Read-side counterpart to pool.py. Knows the shard layout `pool/dt=*/device=*/
source=*/shard-*.jsonl` and applies time / source / project filters before
yielding sorted, source_event_id-deduped events.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from . import config


def parse_window(spec: str) -> timedelta:
    """Parse a window spec like '4h', '2d', '30m', '1w' into a timedelta.

    Raises ValueError if spec is malformed.
    """
    if not spec:
        raise ValueError("empty window spec")
    unit = spec[-1].lower()
    try:
        n = int(spec[:-1])
    except ValueError as e:
        raise ValueError(f"invalid window spec: {spec}") from e
    if unit == "m":
        return timedelta(minutes=n)
    if unit == "h":
        return timedelta(hours=n)
    if unit == "d":
        return timedelta(days=n)
    if unit == "w":
        return timedelta(weeks=n)
    raise ValueError(f"unknown unit in window spec: {spec} (use m/h/d/w)")


def _parse_iso(ts: str) -> datetime | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def walk_events(
    *,
    root_dir: Path | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    sources: Iterable[str] | None = None,
    devices: Iterable[str] | None = None,
    projects: Iterable[str] | None = None,
    dedupe: bool = True,
) -> Iterator[dict[str, Any]]:
    """Yield matching events, sorted by timestamp ascending."""
    base = (root_dir or config.pool_root()) / "pool"
    if not base.exists():
        return

    sources_set = set(sources) if sources else None
    devices_set = set(devices) if devices else None
    projects_set = set(projects) if projects else None

    since_date = since.date().isoformat() if since else None
    until_date = until.date().isoformat() if until else None

    matched_shards: list[Path] = []
    for dt_dir in sorted(base.glob("dt=*")):
        date_str = dt_dir.name[3:]
        if since_date and date_str < since_date:
            continue
        if until_date and date_str > until_date:
            continue
        for device_dir in dt_dir.glob("device=*"):
            device_name = device_dir.name[len("device=") :]
            if devices_set and device_name not in devices_set:
                continue
            for source_dir in device_dir.glob("source=*"):
                source_name = source_dir.name[len("source=") :]
                if sources_set and source_name not in sources_set:
                    continue
                matched_shards.extend(sorted(source_dir.glob("shard-*.jsonl")))

    events: list[dict[str, Any]] = []
    for shard in matched_shards:
        try:
            with shard.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    ts_dt = _parse_iso(e.get("timestamp", ""))
                    if since and ts_dt and ts_dt < since:
                        continue
                    if until and ts_dt and ts_dt > until:
                        continue

                    if projects_set:
                        proj_name = (e.get("project") or {}).get("name")
                        if proj_name not in projects_set:
                            continue

                    events.append(e)
        except OSError:
            continue

    events.sort(key=lambda e: e.get("timestamp", ""))

    if dedupe:
        seen: set[str] = set()
        for e in events:
            seid = e.get("source_event_id") or e.get("id")
            if not seid:
                yield e
                continue
            if seid in seen:
                continue
            seen.add(seid)
            yield e
    else:
        yield from events


def stats(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Compact stat summary for a list of events."""
    out = {
        "count": len(events),
        "sources": {},  # source_type -> count
        "projects": {},  # project name -> count
        "devices": {},  # device_id -> count
        "actors": {},  # actor name -> count
        "sessions": set(),  # session ids
        "first_ts": None,
        "last_ts": None,
    }
    for e in events:
        src = e.get("source_type", "?")
        out["sources"][src] = out["sources"].get(src, 0) + 1
        proj = (e.get("project") or {}).get("name") or "?"
        out["projects"][proj] = out["projects"].get(proj, 0) + 1
        dev = (e.get("source") or {}).get("device_id") or "?"
        out["devices"][dev] = out["devices"].get(dev, 0) + 1
        actor = (e.get("actor") or {}).get("name") or "?"
        out["actors"][actor] = out["actors"].get(actor, 0) + 1
        sess = (e.get("session") or {}).get("id") or (e.get("source") or {}).get("session_id")
        if sess:
            out["sessions"].add(sess)
        ts = e.get("timestamp")
        if ts:
            if out["first_ts"] is None or ts < out["first_ts"]:
                out["first_ts"] = ts
            if out["last_ts"] is None or ts > out["last_ts"]:
                out["last_ts"] = ts
    out["session_count"] = len(out["sessions"])
    out["sessions"] = sorted(out["sessions"])
    return out


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
