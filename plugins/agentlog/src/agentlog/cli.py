"""agentlog CLI entry point.

This is the v0.5 skeleton. Commands are wired but some delegate to modules
still under construction (pool, adapters, sync, recap). Implemented now:
- agentlog init [--repo URL]
- agentlog status
- agentlog poll --once --source claude_code   (delegates once adapter lands)
- agentlog event push <json>

Other commands print "not yet implemented" with a pointer to the design doc.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import config


def _ok(msg: str) -> None:
    print(msg)


def _err(msg: str, code: int = 1) -> int:
    print(f"agentlog: {msg}", file=sys.stderr)
    return code


# ---------------------------------------------------------------- init


def cmd_init(args: argparse.Namespace) -> int:
    root = config.pool_root()
    if root.exists() and any(root.iterdir()):
        # Existing pool: check it's a git repo
        if (root / ".git").exists():
            _ok(f"Pool already initialized at {root}")
        else:
            return _err(
                f"{root} exists and is non-empty but is not a git repo. "
                "Remove it or set AGENTLOG_POOL to a different path."
            )
    else:
        root.mkdir(parents=True, exist_ok=True)
        if args.repo:
            _ok(f"Cloning {args.repo} into {root} ...")
            r = subprocess.run(
                ["git", "clone", args.repo, str(root)],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                return _err(f"git clone failed:\n{r.stderr}")
        else:
            _ok(f"Initializing empty pool at {root} (no remote configured)")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "README.md").write_text(
                "# agent-seeds (private pool for agentlog)\n\n"
                "This repo stores your normalized multi-agent activity.\n"
                "Do not edit manually.\n"
            )
            (root / ".gitignore").write_text(
                "state/cursors/\nstate/quarantine/\nstate/sync.lock\nstate/this-device.json\n"
            )
            (root / ".gitattributes").write_text(
                "pool/**/*.jsonl merge=union\n*.jsonl text eol=lf\n"
            )

    # Ensure directory skeleton
    for sub in ("pool", "sessions", "artifacts", "state", "indexes/daily"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    config.cursors_dir().mkdir(parents=True, exist_ok=True)
    config.devices_dir().mkdir(parents=True, exist_ok=True)
    config.quarantine_dir().mkdir(parents=True, exist_ok=True)

    # Device identity
    dev = config.init_device(force=False)
    _ok(f"Device: {dev.device_id}  (host: {dev.host})")
    _ok(f"Pool root: {root}")
    _ok("Done. Next: `agentlog poll --once --source claude_code` to smoke test.")
    return 0


# ---------------------------------------------------------------- status


def cmd_status(args: argparse.Namespace) -> int:
    root = config.pool_root()
    if not root.exists():
        return _err(f"Pool not initialized. Run `agentlog init [--repo URL]` first.")
    dev = config.load_device()
    if dev is None:
        return _err("No device id. Run `agentlog init` to generate one.")

    print(f"Pool root: {root}")
    print(f"Device:    {dev.device_id} ({dev.host})")

    # Git remote + branch
    try:
        remote = subprocess.run(
            ["git", "-C", str(root), "remote", "-v"],
            capture_output=True, text=True,
        ).stdout.strip()
        print(f"Remote:\n{remote or '  (none)'}")
    except Exception as e:
        print(f"Git status unavailable: {e}")

    # Cursor files
    cursors = list(config.cursors_dir().glob("*.json"))
    if cursors:
        print("Adapter cursors:")
        for c in sorted(cursors):
            try:
                data = json.loads(c.read_text())
                summary = f"({len(data)} keys)"
            except Exception:
                summary = "(unreadable)"
            print(f"  - {c.name} {summary}")
    else:
        print("Adapter cursors: (none yet)")

    # Quarantine size
    quar = list(config.quarantine_dir().glob("*.jsonl"))
    if quar:
        total = sum(p.stat().st_size for p in quar)
        print(f"Quarantine: {len(quar)} files, {total} bytes")

    return 0


# ---------------------------------------------------------------- poll


def cmd_poll(args: argparse.Namespace) -> int:
    source = args.source
    if not source:
        return _err("--source required for now (only `claude_code` supported in v0)")

    if source != "claude_code":
        return _err(f"adapter `{source}` not yet implemented (see docs/design/03-spec-v0.5-merged.md §3.3)")

    try:
        from .pool import Pool  # provided by Cistern
        from .adapters.claude_code import ClaudeCodeAdapter  # provided by Junction
    except ImportError as e:
        return _err(
            f"adapter modules not yet built: {e}. "
            "Cistern and Junction are still writing pool.py and claude_code.py."
        )

    dev = config.load_device()
    if dev is None:
        return _err("No device id. Run `agentlog init` first.")

    pool = Pool(root_dir=config.pool_root(), device_id=dev.device_id)
    adapter = ClaudeCodeAdapter(pool=pool, device_id=dev.device_id)
    result = adapter.pollOnce()
    print(f"Emitted: {result['emitted']}, skipped: {result['skipped']}")
    return 0


# ---------------------------------------------------------------- event push


def cmd_event_push(args: argparse.Namespace) -> int:
    try:
        event = json.loads(args.json)
    except json.JSONDecodeError as e:
        return _err(f"invalid JSON: {e}")

    try:
        from .pool import Pool
        from .schema import validate, make_event_id
    except ImportError as e:
        return _err(f"core modules not yet built: {e}")

    dev = config.load_device()
    if dev is None:
        return _err("Run `agentlog init` first.")

    # Backfill required fields when caller omits them
    event.setdefault("id", make_event_id())
    event.setdefault("schema_version", "agentlog.event.v0")
    event.setdefault("source_type", "manual")
    event.setdefault("source", {})
    event["source"].setdefault("device_id", dev.device_id)

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    event.setdefault("timestamp", now)
    event["ingested_at"] = now
    event.setdefault("payload", {})
    event.setdefault("artifact_refs", [])
    event.setdefault("actor", {"id": "manual", "name": "manual", "kind": "human"})
    event.setdefault("project", {"name": "unknown"})

    pool = Pool(root_dir=config.pool_root(), device_id=dev.device_id)
    result = pool.append(event, flush=args.flush)
    print(json.dumps({
        "ok": result.ok,
        "event_id": result.event_id,
        "shard": str(result.shard_path),
        "duplicate": result.duplicate,
    }, indent=2))
    return 0


# ---------------------------------------------------------------- pool / recap


def cmd_pool(args: argparse.Namespace) -> int:
    from datetime import datetime, timezone
    from .reader import walk_events, parse_window, now_utc
    from . import recap as _recap

    since = None
    if args.last:
        try:
            since = now_utc() - parse_window(args.last)
        except ValueError as e:
            return _err(str(e))

    events = list(walk_events(
        since=since,
        sources=[args.source] if args.source else None,
        projects=[args.project] if args.project else None,
    ))

    if not events:
        print("(no events match filters)")
        return 0

    if args.by:
        print(_recap.format_grouped(events, by=args.by))
    else:
        print(_recap.format_flat(events, limit=args.limit))
    return 0


def cmd_recap(args: argparse.Namespace) -> int:
    from datetime import datetime, timezone, timedelta, date as date_cls
    from .reader import walk_events
    from . import recap as _recap

    if args.date:
        try:
            d = date_cls.fromisoformat(args.date)
        except ValueError:
            return _err(f"invalid --date: {args.date} (use YYYY-MM-DD)")
    else:
        d = datetime.now(timezone.utc).date()

    since = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    until = since + timedelta(days=1)
    events = list(walk_events(since=since, until=until))
    print(_recap.format_recap(d.isoformat(), events, by=args.by))
    return 0


# ---------------------------------------------------------------- migrate-from-seed


def cmd_migrate_seed(args: argparse.Namespace) -> int:
    from pathlib import Path as _P
    from .pool import Pool
    from .migrate_seed import migrate, DEFAULT_SEED_DIR

    dev = config.load_device()
    if dev is None:
        return _err("Run `agentlog init` first.")

    seed_dir = _P(args.seed_dir).expanduser() if args.seed_dir else DEFAULT_SEED_DIR
    if not seed_dir.exists():
        return _err(f"seed dir not found: {seed_dir}")

    pool = Pool(root_dir=config.pool_root(), device_id=dev.device_id)
    result = migrate(pool, seed_dir=seed_dir, device_id=dev.device_id, dry_run=args.dry_run)

    mode = "DRY RUN" if args.dry_run else "migrated"
    print(f"{mode}: {result.sessions_scanned} sessions scanned, "
          f"{result.turns_emitted} turns emitted, "
          f"{result.quarantined} quarantined")
    if args.dry_run:
        print("(re-run without --dry-run to write)")
    return 0


# ---------------------------------------------------------------- stubs


def cmd_stub(name: str):
    def _fn(args):
        return _err(
            f"`agentlog {name}` not yet implemented in v0. "
            f"See docs/design/03-spec-v0.5-merged.md §5 for spec."
        )
    return _fn


# ---------------------------------------------------------------- main


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentlog", description="Multi-agent multi-device activity pool")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="initialize pool repo on this device")
    p_init.add_argument("--repo", help="GitHub repo URL to clone (skip for empty local init)")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="show pool / device / sync status")
    p_status.set_defaults(func=cmd_status)

    p_poll = sub.add_parser("poll", help="run adapter poll cycle")
    p_poll.add_argument("--source", help="adapter source_type (e.g. claude_code)")
    p_poll.add_argument("--once", action="store_true", help="single poll, do not loop")
    p_poll.set_defaults(func=cmd_poll)

    p_event = sub.add_parser("event", help="event operations")
    event_sub = p_event.add_subparsers(dest="event_cmd", required=True)
    p_event_push = event_sub.add_parser("push", help="manually push an event")
    p_event_push.add_argument("json", help="event JSON string")
    p_event_push.add_argument("--flush", action="store_true", help="trigger immediate push")
    p_event_push.set_defaults(func=cmd_event_push)

    p_pool = sub.add_parser("pool", help="view events in the pool")
    p_pool.add_argument("--last", help="time window (e.g. 4h, 2d, 1w)")
    p_pool.add_argument("--by", choices=["source", "project", "agent", "device"],
                         help="group results")
    p_pool.add_argument("--source", help="filter by source_type")
    p_pool.add_argument("--project", help="filter by project name")
    p_pool.add_argument("--limit", type=int, default=50, help="max rows (flat mode)")
    p_pool.set_defaults(func=cmd_pool)

    p_recap = sub.add_parser("recap", help="per-day recap across all sources")
    p_recap.add_argument("--date", help="YYYY-MM-DD (default: today UTC)")
    p_recap.add_argument("--by", choices=["source", "project", "agent", "device"],
                          default="source", help="grouping inside the recap (default: source)")
    p_recap.set_defaults(func=cmd_recap)

    p_mig = sub.add_parser("migrate-from-seed",
                             help="import ~/.claude/skills/seed/state/sessions/*.md into agentlog pool")
    p_mig.add_argument("--dry-run", action="store_true", help="count only, do not write")
    p_mig.add_argument("--seed-dir", help="override seed sessions dir")
    p_mig.set_defaults(func=cmd_migrate_seed)

    for stub_name in ("sync", "pull", "push", "shot", "backfill", "daemon", "config"):
        sp = sub.add_parser(stub_name, help=f"{stub_name} (not yet implemented)")
        sp.set_defaults(func=cmd_stub(stub_name))

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
