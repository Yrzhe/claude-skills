"""Filesystem paths and permission helpers."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from .constants import APP_DIR_NAME, AUTH_FILE, CONFIG_FILE, DB_FILE


def app_home() -> Path:
    override = os.environ.get("GROK_CLI_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / APP_DIR_NAME


def ensure_app_home() -> Path:
    home = app_home()
    home.mkdir(parents=True, exist_ok=True)
    try:
        home.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except OSError:
        # Windows ignores POSIX mode bits in many configurations.
        pass
    return home


def auth_path() -> Path:
    return ensure_app_home() / AUTH_FILE


def config_path() -> Path:
    return ensure_app_home() / CONFIG_FILE


def db_path() -> Path:
    return ensure_app_home() / DB_FILE


def write_private_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
