#!/usr/bin/env python3
"""Capture a screenshot and bind it to the current session's seed file.

Modes
-----
shot.py                    → interactive window pick (screencapture -w).
                             Cursor turns into a camera; user clicks the
                             window they want captured. No guessing, no
                             Accessibility-permission dance.

shot.py <url>              → headless Chrome screenshot of URL. Accepts
                             http://, https://, or bare localhost:3000.

shot.py --note "text"      → (optional) additional context appended to the
                             marker in the session file.

Output
------
  ~/.claude/skills/seed/state/sessions/{session_id}/shots/{timestamp}.png
  (marker appended to the session's .md file so /seed can associate it)

Session-ID resolution (first match wins)
----------------------------------------
  1. --session-id CLI arg (agent passes its own session_id explicitly)
  2. $CLAUDE_SESSION_ID env var if exported
  3. Fallback: most recently modified {session_id}.md in state/sessions/
     (⚠ risky when multiple Claude Code sessions run in parallel)
  4. Error out if none
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

STATE = Path.home() / ".claude" / "skills" / "seed" / "state" / "sessions"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Arc.app/Contents/MacOS/Arc",
]


def resolve_session_id(explicit: str | None = None) -> tuple[str | None, str]:
    """Return (session_id, source). source ∈ {'arg','env','fallback','none'}."""
    if explicit:
        return (explicit.strip(), "arg")
    sid = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    if sid:
        return (sid, "env")
    if not STATE.exists():
        return (None, "none")
    candidates = list(STATE.glob("*.md"))
    if not candidates:
        return (None, "none")
    return (max(candidates, key=lambda p: p.stat().st_mtime).stem, "fallback")


def capture_interactive(out: Path) -> bool:
    """`screencapture -w` enters window-select mode — user clicks a window."""
    # -w : window selection mode
    # -o : omit window shadow
    # -x : silent (no shutter sound)
    r = subprocess.run(
        ["screencapture", "-w", "-o", "-x", str(out)],
        capture_output=True,
    )
    return r.returncode == 0 and out.exists()


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def capture_url(url: str, out: Path, width: int = 1280, height: int = 800) -> bool:
    chrome = find_chrome()
    if not chrome:
        print("ERR: no Chrome/Chromium/Edge/Arc found", file=sys.stderr)
        return False
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
        timeout=30,
    )
    if not out.exists():
        print(
            "ERR: headless chrome did not produce output. stderr:",
            r.stderr.decode("utf-8", "replace")[:500],
            file=sys.stderr,
        )
        return False
    return True


def append_marker(
    session_file: Path, shot_path: Path, timestamp: str, note: str
) -> None:
    if not session_file.exists():
        header = f"# Session Seed Log — `{session_file.stem}`\n\n"
        session_file.write_text(header, encoding="utf-8")
    block = f"\n<!-- shot -->\n**📸 Shot** ({timestamp}): `{shot_path}`"
    if note:
        block += f" — {note}"
    block += "\n\n"
    with session_file.open("a", encoding="utf-8") as f:
        f.write(block)


def normalize_target(arg: str) -> tuple[str, str]:
    """Return (mode, value). Mode is 'url' for URL-like args."""
    lower = arg.lower()
    if lower.startswith(("http://", "https://")):
        return ("url", arg)
    if lower.startswith("localhost") or lower.startswith("127.0.0.1"):
        return ("url", "http://" + arg)
    if ":" in arg and arg.split(":", 1)[1].split("/", 1)[0].isdigit():
        # host:port style, treat as URL
        return ("url", "http://" + arg)
    return ("unknown", arg)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Capture a screenshot and link it to the current seed session."
    )
    ap.add_argument(
        "target",
        nargs="?",
        help="URL to capture (omit for interactive window pick)",
    )
    ap.add_argument("--note", default="", help="Extra note stored with the marker")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument(
        "--session-id",
        default=None,
        help="Bind shot to this session (agent should pass its own session_id)",
    )
    args = ap.parse_args()

    sid, source = resolve_session_id(args.session_id)
    if not sid:
        print(
            "ERR: cannot resolve session_id. Pass --session-id, set CLAUDE_SESSION_ID, or let the Stop hook create a session file first.",
            file=sys.stderr,
        )
        return 1
    if source == "fallback":
        print(
            f"⚠ session_id resolved via fallback (most-recent file). If multiple Claude Code sessions are running, pass --session-id explicitly.",
            file=sys.stderr,
        )

    shots_dir = STATE / sid / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out = shots_dir / f"{timestamp}.png"

    if not args.target:
        ok = capture_interactive(out)
        note = args.note or "interactive window pick"
    else:
        mode, value = normalize_target(args.target)
        if mode == "url":
            ok = capture_url(value, out, args.width, args.height)
            note = args.note or f"headless: {value}"
        else:
            print(
                f"ERR: unknown target format: {args.target!r}. Pass a URL or omit for interactive mode.",
                file=sys.stderr,
            )
            return 1

    if not ok or not out.exists():
        print("ERR: capture failed", file=sys.stderr)
        return 1

    session_file = STATE / f"{sid}.md"
    append_marker(session_file, out, timestamp, note)

    # Machine-readable single line (easy to parse from skills)
    print(f"SHOT_PATH={out}")
    print(f"SESSION_FILE={session_file}")
    print(f"✅ Captured {out.name} — linked to session {sid[:8]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
