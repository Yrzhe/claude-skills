"""Tests for the seed → agentlog migrator."""
from __future__ import annotations

import json
from pathlib import Path

from agentlog.migrate_seed import migrate, _iter_turns, _summary
from agentlog.pool import Pool


SEED_SAMPLE = """\
# Session Seed Log — `12a338ba-84c1-47fa-aa96-efb9b5a17b27`

## 2026-04-21 00:07:29
<!-- turn-uuid: df7fc179-351f-4283-8692-8ef2fda45294 -->
**cwd:** `/Users/me/projectA`

**User:**

Hello there, please do thing X.

**Tools:**
- `Bash` — ls
- `Read` — /etc/hosts

## 2026-04-21 00:08:00
<!-- turn-uuid: another-uuid -->
**cwd:** `/Users/me/projectA`

**User:**

Follow up question.

**Tools:**

(no tools)
"""


def test_iter_turns_splits_correctly():
    turns = list(_iter_turns(SEED_SAMPLE))
    assert len(turns) == 2
    assert turns[0]["timestamp"].startswith("2026-04-21T00:07:29")
    assert turns[0]["turn_uuid"] == "df7fc179-351f-4283-8692-8ef2fda45294"
    assert turns[0]["cwd"] == "/Users/me/projectA"
    assert "Hello there" in turns[0]["user_text"]
    assert "Bash" in turns[0]["tools"]
    assert "Read" in turns[0]["tools"]
    assert turns[1]["tools"] == []


def test_summary_truncates_and_strips():
    s = _summary("hi" * 200, 3)
    assert len(s) <= 240


def test_migrate_writes_events_to_pool(tmp_path: Path):
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "session-1.md").write_text(SEED_SAMPLE)

    pool_root = tmp_path / "pool"
    pool = Pool(root_dir=pool_root, device_id="dev-test")

    result = migrate(pool, seed_dir=seed_dir, device_id="dev-test", dry_run=False)
    assert result.sessions_scanned == 1
    assert result.turns_emitted == 2
    assert result.quarantined == 0

    shards = list(pool_root.glob("pool/dt=*/device=dev-test/source=claude_code_seed/shard-*.jsonl"))
    assert shards, "expected at least one shard written"
    lines = shards[0].read_text().strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["source_type"] == "claude_code_seed"
    assert first["source_event_id"] == "seed:session-1:df7fc179-351f-4283-8692-8ef2fda45294"
    assert first["payload"]["tool_count"] == 2
    assert "claude_code" in first["tags"]


def test_migrate_dry_run_does_not_write(tmp_path: Path):
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "session-2.md").write_text(SEED_SAMPLE)

    pool_root = tmp_path / "pool"
    pool = Pool(root_dir=pool_root, device_id="dev-test")

    result = migrate(pool, seed_dir=seed_dir, device_id="dev-test", dry_run=True)
    assert result.turns_emitted == 2
    shards = list(pool_root.glob("pool/**/*.jsonl"))
    assert not shards, "dry run should not write any shards"
