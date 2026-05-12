"""Screenshot capture, persisted to the pool as an EventV0 + artifact.

Two modes:
  - `shot()`            interactive window pick (macOS `screencapture -w`)
  - `shot(url=...)`     headless Chrome screenshot of a URL

Output goes to <pool>/artifacts/screenshots/YYYY-MM-DD/<ts>.png and a
`checkpoint`-action event with the artifact_ref pointing at the file is
appended to the pool.

The screenshot artifact lives inside the pool tree, so once committed it
syncs across devices via the existing `agentlog sync` flow.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config
from .schema import make_event_id


CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Arc.app/Contents/MacOS/Arc",
]


@dataclass
class ShotResult:
    ok: bool
    path: Path | None
    event_id: str | None
    sha256: str | None
    bytes: int | None
    note: str | None = None
    error: str | None = None


def _find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def _normalize_url(target: str) -> tuple[str, str]:
    """Return (mode, value). mode in {'url', 'unknown'}."""
    low = target.lower()
    if low.startswith(("http://", "https://")):
        return ("url", target)
    if low.startswith(("localhost", "127.0.0.1")):
        return ("url", "http://" + target)
    if ":" in target and target.split(":", 1)[1].split("/", 1)[0].isdigit():
        return ("url", "http://" + target)
    return ("unknown", target)


def _capture_interactive(out: Path) -> tuple[bool, str | None]:
    """macOS `screencapture -w` — user clicks the window to capture."""
    if not shutil.which("screencapture"):
        return (False, "screencapture not found (interactive mode is macOS-only)")
    r = subprocess.run(
        ["screencapture", "-w", "-o", "-x", str(out)],
        capture_output=True,
    )
    if r.returncode != 0 or not out.exists():
        return (False, f"screencapture failed: rc={r.returncode}")
    return (True, None)


def _capture_url(
    url: str, out: Path, *, width: int = 1280, height: int = 800, timeout: int = 30
) -> tuple[bool, str | None]:
    chrome = _find_chrome()
    if not chrome:
        return (False, "no headless browser found (Chrome / Chromium / Edge / Arc)")
    try:
        r = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size={width},{height}",
                f"--screenshot={out}",
                url,
            ],
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return (False, f"chrome screenshot timed out after {timeout}s")
    if not out.exists():
        err = r.stderr.decode("utf-8", "replace")[:300]
        return (False, f"chrome produced no output: {err}")
    return (True, None)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _build_event(
    *,
    device_id: str,
    artifact_uri: str,
    sha256: str,
    bytes_: int,
    note: str,
    target_label: str,
    session_id: str | None,
    project_name: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    summary = f"shot: {target_label}"
    if note:
        summary = f"{summary} — {note}"
    if len(summary) > 240:
        summary = summary[:239] + "…"

    event: dict[str, Any] = {
        "schema_version": "agentlog.event.v0",
        "id": make_event_id(),
        "source_event_id": f"shot:{device_id}:{now}",
        "timestamp": now,
        "ingested_at": now,
        "actor": {"id": "human:shot", "name": "User", "kind": "human"},
        "source_type": "manual",
        "source": {"device_id": device_id},
        "project": {"name": project_name},
        "action": {"type": "checkpoint", "status": "completed", "label": "shot"},
        "summary": summary,
        "payload": {
            "target": target_label,
            "note": note,
        },
        "artifact_refs": [
            {
                "kind": "screenshot",
                "uri": artifact_uri,
                "storage": "git",
                "sha256": sha256,
                "bytes": bytes_,
                "mime_type": "image/png",
            }
        ],
        "tags": ["shot"],
    }
    if session_id:
        event["source"]["session_id"] = session_id
    return event


def take_shot(
    *,
    target: str | None = None,
    note: str = "",
    width: int = 1280,
    height: int = 800,
    session_id: str | None = None,
    project: str = "shot",
    flush: bool = False,
) -> ShotResult:
    """Capture a screenshot, emit an event to the pool, return the result."""
    from .pool import Pool

    dev = config.load_device()
    if dev is None:
        return ShotResult(
            ok=False, path=None, event_id=None, sha256=None, bytes=None,
            error="device not initialized — run `agentlog init` first",
        )

    pool_root = config.pool_root()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    shots_dir = pool_root / "artifacts" / "screenshots" / today
    shots_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out = shots_dir / f"{ts}.png"

    if target:
        mode, value = _normalize_url(target)
        if mode != "url":
            return ShotResult(
                ok=False, path=None, event_id=None, sha256=None, bytes=None,
                error=f"unrecognized target {target!r} — pass a URL or omit for interactive mode",
            )
        ok, err = _capture_url(value, out, width=width, height=height)
        target_label = value
    else:
        ok, err = _capture_interactive(out)
        target_label = "interactive"

    if not ok or not out.exists():
        return ShotResult(
            ok=False, path=None, event_id=None, sha256=None, bytes=None, error=err,
        )

    digest = _sha256(out)
    bytes_ = out.stat().st_size
    artifact_uri = "file://" + str(out.relative_to(pool_root))

    event = _build_event(
        device_id=dev.device_id,
        artifact_uri=artifact_uri,
        sha256=digest,
        bytes_=bytes_,
        note=note,
        target_label=target_label,
        session_id=session_id,
        project_name=project,
    )

    pool = Pool(root_dir=pool_root, device_id=dev.device_id)
    append_result = pool.append(event, flush=flush)

    return ShotResult(
        ok=append_result.ok,
        path=out,
        event_id=append_result.event_id,
        sha256=digest,
        bytes=bytes_,
        note=note or target_label,
    )
