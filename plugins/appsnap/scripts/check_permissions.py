#!/usr/bin/env python3
"""Preflight local macOS permissions required by appsnap."""

from __future__ import annotations

import json
import sys


GUIDANCE = (
    "Grant Accessibility and Screen & System Audio Recording to this terminal app: "
    "System Settings > Privacy & Security > Accessibility and Screen & System Audio Recording, then restart the terminal."
)


def _load_frameworks():
    try:
        import ApplicationServices  # type: ignore
        import Quartz  # type: ignore
    except Exception as exc:  # pragma: no cover - host dependency
        print(f"macOS PyObjC frameworks unavailable: {exc}", file=sys.stderr)
        sys.exit(2)
    return ApplicationServices, Quartz


def accessibility_trusted() -> bool:
    application_services, _ = _load_frameworks()
    try:
        return bool(application_services.AXIsProcessTrusted())
    except Exception:
        return False


def screen_recording_trusted() -> bool:
    _, quartz = _load_frameworks()
    preflight = getattr(quartz, "CGPreflightScreenCaptureAccess", None)
    if preflight is None:
        # Best-effort fallback for older bindings: the capture script still verifies
        # by running screencapture and failing with a one-line error if denied.
        return True
    try:
        return bool(preflight())
    except Exception:
        return False


def main() -> int:
    permissions = {
        "accessibility": accessibility_trusted(),
        "screen_recording": screen_recording_trusted(),
    }
    missing = [name for name, ok in permissions.items() if not ok]
    if missing:
        print(GUIDANCE, file=sys.stderr)
        return 2

    print(json.dumps({"ok": True, "permissions": permissions}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
