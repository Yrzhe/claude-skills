"""Config + device identity for agentlog.

Pool repo defaults to ~/.agent-seeds/. Per-device id is generated at init time
and stored in <pool>/state/devices/<device_id>.json.
"""
from __future__ import annotations

import json
import os
import platform
import socket
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_POOL_ROOT = Path("~/.agent-seeds").expanduser()


@dataclass
class DeviceInfo:
    device_id: str
    host: str
    platform: str
    created_at: str  # ISO-8601


def pool_root() -> Path:
    """Return the local pool repo root, honoring AGENTLOG_POOL env if set."""
    env = os.environ.get("AGENTLOG_POOL")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_POOL_ROOT


def state_dir() -> Path:
    return pool_root() / "state"


def cursors_dir() -> Path:
    return state_dir() / "cursors"


def devices_dir() -> Path:
    return state_dir() / "devices"


def quarantine_dir() -> Path:
    return state_dir() / "quarantine"


def pool_data_dir() -> Path:
    return pool_root() / "pool"


def artifacts_dir() -> Path:
    return pool_root() / "artifacts"


def _device_id_file() -> Path:
    # The active device's id is recorded in state/this-device.json so multiple
    # device files (one per known device, mirrored via git) can coexist.
    return state_dir() / "this-device.json"


def load_device() -> Optional[DeviceInfo]:
    f = _device_id_file()
    if not f.exists():
        return None
    data = json.loads(f.read_text())
    return DeviceInfo(**data)


def generate_device_id() -> str:
    """Stable but human-readable device id.

    Format: <hostname-slug>-<short-uuid>. Hostname slug uses lowercase and -
    only. Short uuid keeps it unique across reinstalls on the same host.
    """
    host = socket.gethostname()
    slug = "".join(c.lower() if c.isalnum() else "-" for c in host).strip("-") or "device"
    short = uuid.uuid4().hex[:8]
    return f"{slug}-{short}"


def init_device(force: bool = False) -> DeviceInfo:
    """Create this-device.json if missing (or rewrite when force=True)."""
    f = _device_id_file()
    if f.exists() and not force:
        existing = load_device()
        assert existing is not None
        return existing

    from datetime import datetime, timezone

    info = DeviceInfo(
        device_id=generate_device_id(),
        host=socket.gethostname(),
        platform=platform.platform(),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    state_dir().mkdir(parents=True, exist_ok=True)
    devices_dir().mkdir(parents=True, exist_ok=True)

    # Atomic write to state/this-device.json
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(info.__dict__, indent=2))
    tmp.replace(f)

    # Mirror device record under devices/<id>.json so other devices see it via git pull
    per_dev = devices_dir() / f"{info.device_id}.json"
    per_dev.write_text(json.dumps(info.__dict__, indent=2))

    return info
