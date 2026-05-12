from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.pool import Pool  # noqa: E402
from agentlog.schema import make_event_id  # noqa: E402
from agentlog.sync import Sync  # noqa: E402


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)


def init_bare(tmp_path: Path) -> Path:
    bare = tmp_path / "remote.git"
    run(["git", "init", "--bare", str(bare)])
    return bare


def init_worktree(path: Path, remote: Path) -> Path:
    path.mkdir(parents=True)
    run(["git", "init", "-q"], cwd=path)
    run(["git", "checkout", "-b", "main"], cwd=path)
    Sync(path, "device-a").set_remote(str(remote))
    return path


def clone(remote: Path, path: Path) -> Path:
    run(["git", "clone", str(remote), str(path)])
    return path


def valid_event(source_event_id: str, device_id: str, *, summary: str | None = None) -> dict:
    return {
        "schema_version": "agentlog.event.v0",
        "id": make_event_id(),
        "source_event_id": source_event_id,
        "timestamp": "2026-05-12T17:04:31.238+08:00",
        "ingested_at": "2026-05-12T17:04:35.102+08:00",
        "actor": {"id": "codex:local-default", "name": "Codex", "kind": "agent"},
        "source_type": "codex",
        "source": {
            "device_id": device_id,
            "host": device_id,
            "process_id": "pid-123",
            "session_id": "session-1",
        },
        "project": {"name": "agentlog", "path": "/tmp/agentlog"},
        "action": {
            "type": "session_completed",
            "status": "completed",
            "label": "recap generated",
        },
        "summary": summary or f"Event {source_event_id}",
        "payload": {"duration_ms": 1000, "text_excerpt": "done"},
        "artifact_refs": [],
    }


def append(root: Path, device_id: str, source_event_id: str) -> None:
    Pool(root, device_id).append(valid_event(source_event_id, device_id), flush=True)


def pool_rows(root: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted((root / "pool").glob("**/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            rows.append(json.loads(line))
    return rows


def test_push_once_with_local_event(tmp_path: Path) -> None:
    remote = init_bare(tmp_path)
    local = init_worktree(tmp_path / "local", remote)
    append(local, "device-a", "codex:session-1:line-1")

    result = Sync(local, "device-a").push(force=True)

    assert result.ok is True
    assert result.pushed is True
    assert result.committed is True
    log = run(["git", "log", "--oneline", "-1"], cwd=local).stdout
    assert "append pool events: device-a" in log


def test_clone_to_second_device_and_pull_receives_event(tmp_path: Path) -> None:
    remote = init_bare(tmp_path)
    local = init_worktree(tmp_path / "local", remote)
    append(local, "device-a", "codex:session-1:line-1")
    assert Sync(local, "device-a").push(force=True).ok

    other = clone(remote, tmp_path / "other")
    pull = Sync(other, "device-b").pull()

    assert pull.ok is True
    assert [row["source_event_id"] for row in pool_rows(other)] == ["codex:session-1:line-1"]


def test_two_devices_different_shards_sync_without_conflict(tmp_path: Path) -> None:
    remote = init_bare(tmp_path)
    device_a = init_worktree(tmp_path / "device-a", remote)
    append(device_a, "device-a", "codex:session-1:line-1")
    assert Sync(device_a, "device-a").push(force=True).ok
    device_b = clone(remote, tmp_path / "device-b")

    append(device_a, "device-a", "codex:session-1:line-2")
    append(device_b, "device-b", "codex:session-1:line-3")

    assert Sync(device_a, "device-a").push(force=True).ok
    assert Sync(device_b, "device-b").push(force=True).ok
    assert Sync(device_a, "device-a").pull().ok

    ids = sorted(row["source_event_id"] for row in pool_rows(device_a))
    assert ids == [
        "codex:session-1:line-1",
        "codex:session-1:line-2",
        "codex:session-1:line-3",
    ]


def test_same_shard_conflict_resolves_with_union_and_jsonl_parse(tmp_path: Path) -> None:
    remote = init_bare(tmp_path)
    device_a = init_worktree(tmp_path / "device-a", remote)
    append(device_a, "same-device", "codex:session-1:line-1")
    assert Sync(device_a, "same-device").push(force=True).ok
    device_b = clone(remote, tmp_path / "device-b")

    append(device_a, "same-device", "codex:session-1:line-2")
    append(device_b, "same-device", "codex:session-1:line-3")

    assert Sync(device_a, "same-device").push(force=True).ok
    result = Sync(device_b, "same-device").push(force=True)
    assert result.ok is True
    assert Sync(device_a, "same-device").pull().ok

    ids = sorted(row["source_event_id"] for row in pool_rows(device_a))
    assert ids == [
        "codex:session-1:line-1",
        "codex:session-1:line-2",
        "codex:session-1:line-3",
    ]
