"""Foreground daemon loop for agentlog.

Runs periodic poll cycles over all configured adapters plus periodic git sync.
Sync is lazy-imported so this module is usable before sync.py lands. SIGTERM/
SIGINT exits cleanly. The launchd / systemd plist generators in this file are
helpers — they print to stdout and the user installs them manually.
"""
from __future__ import annotations

import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from . import config


DEFAULT_POLL_INTERVAL_S = 30
DEFAULT_SYNC_INTERVAL_S = 300
DEFAULT_SOURCES = ("claude_code", "codex")


@dataclass
class DaemonStats:
    polls: int = 0
    syncs: int = 0
    errors: int = 0
    last_poll_at: str | None = None
    last_sync_at: str | None = None
    started_at: str = ""
    per_source_emitted: dict[str, int] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _try_poll(source: str, stats: DaemonStats) -> None:
    from .pool import Pool
    from . import cli as _cli

    cls, err = _cli._load_adapter(source)
    if cls is None:
        sys.stderr.write(f"[daemon] poll skip {source}: {err}\n")
        return
    dev = config.load_device()
    if dev is None:
        sys.stderr.write("[daemon] no device; run `agentlog init`\n")
        return
    pool = Pool(root_dir=config.pool_root(), device_id=dev.device_id)
    adapter = cls(pool=pool, device_id=dev.device_id)
    try:
        result = adapter.pollOnce()
        emitted = result.get("emitted", 0)
        stats.per_source_emitted[source] = stats.per_source_emitted.get(source, 0) + emitted
        stats.last_poll_at = _now_iso()
        if emitted:
            sys.stderr.write(f"[daemon] {_now_iso()} {source}: +{emitted}\n")
    except Exception as e:
        stats.errors += 1
        sys.stderr.write(f"[daemon] poll error {source}: {e!r}\n")


def _try_sync(stats: DaemonStats) -> None:
    """Lazy-import sync.py; no-op if not yet implemented."""
    try:
        from .sync import Sync  # noqa: F401
    except ImportError:
        return  # sync not built yet — silently skip
    try:
        from .sync import Sync as _Sync
        dev = config.load_device()
        if dev is None:
            return
        s = _Sync(root_dir=config.pool_root(), device_id=dev.device_id)
        s.sync()
        stats.syncs += 1
        stats.last_sync_at = _now_iso()
        sys.stderr.write(f"[daemon] {_now_iso()} sync ok\n")
    except Exception as e:
        stats.errors += 1
        sys.stderr.write(f"[daemon] sync error: {e!r}\n")


class _Stop:
    def __init__(self) -> None:
        self.flag = False
        signal.signal(signal.SIGTERM, self._set)
        signal.signal(signal.SIGINT, self._set)

    def _set(self, *_a) -> None:
        self.flag = True


def run(
    *,
    sources: Iterable[str] = DEFAULT_SOURCES,
    poll_interval_s: int = DEFAULT_POLL_INTERVAL_S,
    sync_interval_s: int = DEFAULT_SYNC_INTERVAL_S,
    once: bool = False,
) -> DaemonStats:
    """Run the daemon loop. Returns the final stats."""
    stats = DaemonStats(started_at=_now_iso())
    stop = _Stop()
    last_sync = 0.0
    sys.stderr.write(
        f"[daemon] started {stats.started_at} sources={list(sources)} "
        f"poll_interval={poll_interval_s}s sync_interval={sync_interval_s}s\n"
    )

    while not stop.flag:
        stats.polls += 1
        for source in sources:
            if stop.flag:
                break
            _try_poll(source, stats)
        if time.time() - last_sync > sync_interval_s and not stop.flag:
            _try_sync(stats)
            last_sync = time.time()
        if once or stop.flag:
            break
        # short-sleep loop so SIGTERM is responsive
        for _ in range(poll_interval_s * 10):
            if stop.flag:
                break
            time.sleep(0.1)

    sys.stderr.write(f"[daemon] stopped at {_now_iso()} polls={stats.polls} "
                      f"syncs={stats.syncs} errors={stats.errors}\n")
    return stats


# ---------------------------------------------------------------- install helpers


def launchd_plist(
    *, label: str = "ai.agentlog.daemon",
    agentlog_bin: str | None = None,
    pool: str | None = None,
) -> str:
    """Return a launchd plist string to drop into ~/Library/LaunchAgents/."""
    bin_path = agentlog_bin or "/usr/local/bin/agentlog"
    pool_env = pool or str(config.pool_root())
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{bin_path}</string>
    <string>daemon</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>AGENTLOG_POOL</key>
    <string>{pool_env}</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>{pool_env}/state/daemon.log</string>
  <key>StandardErrorPath</key>
  <string>{pool_env}/state/daemon.log</string>
</dict>
</plist>
"""


def systemd_unit(
    *, agentlog_bin: str | None = None,
    pool: str | None = None,
    user: str | None = None,
) -> str:
    """Return a systemd user unit string (drop into ~/.config/systemd/user/)."""
    bin_path = agentlog_bin or "/usr/local/bin/agentlog"
    pool_env = pool or str(config.pool_root())
    return f"""[Unit]
Description=agentlog daemon
After=network-online.target

[Service]
Type=simple
ExecStart={bin_path} daemon
Environment=AGENTLOG_POOL={pool_env}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""
