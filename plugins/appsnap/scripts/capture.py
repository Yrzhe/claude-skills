#!/usr/bin/env python3
"""Pick or resolve a macOS window, capture it, and emit the Component B JSON."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


GUIDANCE = (
    "Grant Accessibility and Screen & System Audio Recording to this terminal app: "
    "System Settings > Privacy & Security > Accessibility and Screen & System Audio Recording, then restart the terminal."
)


def die(message: str, code: int = 1) -> None:
    print(message.replace("\n", " "), file=sys.stderr)
    raise SystemExit(code)


def load_frameworks():
    try:
        import ApplicationServices  # type: ignore
        import Quartz  # type: ignore
    except Exception as exc:
        die(f"macOS PyObjC frameworks unavailable: {exc}", 2)
    return ApplicationServices, Quartz


ApplicationServices, Quartz = load_frameworks()


def check_permissions() -> None:
    ax_ok = bool(ApplicationServices.AXIsProcessTrusted())
    preflight = getattr(Quartz, "CGPreflightScreenCaptureAccess", None)
    screen_ok = True if preflight is None else bool(preflight())
    if not ax_ok or not screen_ok:
        die(GUIDANCE, 2)


def read_request() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {"mode": "auto"}
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"invalid stdin JSON: {exc}", 2)
    if not isinstance(request, dict):
        die("stdin JSON must be an object", 2)
    return request


def as_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def normalize_window(info: dict[str, Any]) -> dict[str, Any] | None:
    bounds = info.get(Quartz.kCGWindowBounds) or {}
    width = int(bounds.get("Width", 0) or 0)
    height = int(bounds.get("Height", 0) or 0)
    if width <= 0 or height <= 0:
        return None

    layer = as_int(info.get(Quartz.kCGWindowLayer))
    if layer != 0:
        return None

    windowid = as_int(info.get(Quartz.kCGWindowNumber))
    pid = as_int(info.get(Quartz.kCGWindowOwnerPID))
    app = str(info.get(Quartz.kCGWindowOwnerName) or "")
    if not windowid or not pid or not app:
        return None

    title = str(info.get(Quartz.kCGWindowName) or "")
    return {
        "pid": pid,
        "windowid": windowid,
        "app": app,
        "title": title,
        "bounds": {
            "x": int(bounds.get("X", 0) or 0),
            "y": int(bounds.get("Y", 0) or 0),
            "w": width,
            "h": height,
        },
    }


def list_windows() -> list[dict[str, Any]]:
    options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    raw_windows = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID) or []
    windows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for info in raw_windows:
        window = normalize_window(dict(info))
        if window is None:
            continue
        if window["windowid"] in seen:
            continue
        seen.add(window["windowid"])
        windows.append(window)
    return windows


def applescript_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def choose_window(windows: list[dict[str, Any]]) -> dict[str, Any]:
    if not windows:
        die("no on-screen application windows found", 1)

    labels = []
    for index, window in enumerate(windows, start=1):
        title = window["title"] or "(untitled)"
        labels.append(f"{index}. {window['app']} - {title} [{window['windowid']}]")

    items = ", ".join(applescript_string(label) for label in labels)
    script = (
        f"set choices to {{{items}}}\n"
        'set picked to choose from list choices with title "appsnap" '
        'with prompt "Pick a window to capture" OK button name "Capture" cancel button name "Cancel"\n'
        'if picked is false then error number -128\n'
        "return item 1 of picked\n"
    )
    proc = subprocess.run(["osascript", "-e", script], text=True, capture_output=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if "User canceled" in stderr or "-128" in stderr:
            die("window pick canceled", 1)
        die(f"window picker failed: {stderr or proc.returncode}", 1)

    selected = (proc.stdout or "").strip()
    try:
        index = int(selected.split(".", 1)[0])
    except Exception:
        die("window picker returned an unrecognized selection", 1)
    if index < 1 or index > len(windows):
        die("window picker returned an out-of-range selection", 1)
    return windows[index - 1]


def frontmost_window(windows: list[dict[str, Any]]) -> dict[str, Any]:
    if not windows:
        die("no on-screen application windows found", 1)
    return windows[0]


def window_under_mouse(windows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Best-effort: the topmost on-screen window containing the pointer.
    `windows` is front-to-back, so the first match is the one on top."""
    try:
        event = Quartz.CGEventCreate(None)
        loc = Quartz.CGEventGetLocation(event)
        x, y = float(loc.x), float(loc.y)
    except Exception:
        return None
    for window in windows:
        b = window["bounds"]
        if b["x"] <= x <= b["x"] + b["w"] and b["y"] <= y <= b["y"] + b["h"]:
            return window
    return None


def capture_interactive() -> Path:
    """macOS native window picker: screen dims, hover highlights a window,
    click captures it, ESC cancels. Returns the captured PNG path."""
    output = output_path()
    proc = subprocess.run(
        ["screencapture", "-x", "-w", "-o", str(output)],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        die(f"screencapture failed: {stderr or proc.returncode}", 1)
    # On ESC/cancel screencapture exits 0 but writes no file.
    if not output.is_file() or output.stat().st_size <= 0:
        die("hover capture canceled (no window selected)", 1)
    return output.resolve()


def output_dir() -> Path:
    """Stable, discoverable capture location (override with APPSNAP_DIR)."""
    raw = os.environ.get("APPSNAP_DIR")
    base = Path(raw).expanduser() if raw else (Path.home() / "Pictures" / "appsnap")
    base.mkdir(parents=True, exist_ok=True)
    return base


def output_path() -> Path:
    return output_dir() / f"appsnap-{time.strftime('%Y%m%d-%H%M%S')}.png"


def capture_window(window: dict[str, Any]) -> Path:
    output = output_path()
    proc = subprocess.run(
        ["screencapture", "-x", "-l", str(window["windowid"]), "-o", str(output)],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        die(f"screencapture failed: {stderr or proc.returncode}", 1)
    if not output.is_file() or output.stat().st_size <= 0:
        die("screencapture did not create a non-empty png", 1)
    return output.resolve()


def capture_fullpage(window: dict[str, Any]) -> dict[str, Any]:
    script = Path(__file__).resolve().with_name("capture_fullpage.py")
    proc = subprocess.run(
        [sys.executable, os.fspath(script)],
        input=json.dumps(window),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        die(f"capture_fullpage failed: {stderr or proc.returncode}", proc.returncode)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        die("capture_fullpage returned non-JSON output", 1)
    if not isinstance(result, dict) or not result.get("ok"):
        die("capture_fullpage returned an unsuccessful result", 1)
    return result


def ax_value(element: Any, attribute: str) -> Any | None:
    try:
        error, value = ApplicationServices.AXUIElementCopyAttributeValue(element, attribute, None)
    except Exception:
        return None
    if error != 0:
        return None
    return value


def ax_attribute_names(element: Any) -> set[str]:
    try:
        error, names = ApplicationServices.AXUIElementCopyAttributeNames(element, None)
    except Exception:
        return set()
    if error != 0 or not names:
        return set()
    return {str(name) for name in names}


def is_ax_list(value: Any) -> bool:
    if isinstance(value, (str, bytes, bytearray)):
        return False
    if isinstance(value, (list, tuple)):
        return True
    return hasattr(value, "__iter__") and hasattr(value, "__len__")


def ax_point(element: Any, attribute: str) -> tuple[int, int] | None:
    value = ax_value(element, attribute)
    if value is None:
        return None
    try:
        return tuple(int(round(part)) for part in value)  # type: ignore[arg-type, return-value]
    except Exception:
        return None


def select_ax_window(pid: int, window: dict[str, Any]) -> Any | None:
    app = ApplicationServices.AXUIElementCreateApplication(pid)
    ax_windows = ax_value(app, getattr(ApplicationServices, "kAXWindowsAttribute", "AXWindows"))
    candidates = list(ax_windows) if is_ax_list(ax_windows) else []
    if not candidates:
        focused = ax_value(app, getattr(ApplicationServices, "kAXFocusedWindowAttribute", "AXFocusedWindow"))
        return focused or app

    title = str(window.get("title") or "")
    bounds = window.get("bounds") or {}

    def score(candidate: Any) -> int:
        total = 0
        candidate_title = ax_value(candidate, getattr(ApplicationServices, "kAXTitleAttribute", "AXTitle"))
        if title and candidate_title:
            candidate_title = str(candidate_title)
            if candidate_title == title:
                total += 100
            elif title in candidate_title or candidate_title in title:
                total += 40
        pos = ax_point(candidate, getattr(ApplicationServices, "kAXPositionAttribute", "AXPosition"))
        size = ax_point(candidate, getattr(ApplicationServices, "kAXSizeAttribute", "AXSize"))
        if pos:
            total += max(0, 40 - abs(pos[0] - int(bounds.get("x", 0))) - abs(pos[1] - int(bounds.get("y", 0))))
        if size:
            total += max(0, 40 - abs(size[0] - int(bounds.get("w", 0))) - abs(size[1] - int(bounds.get("h", 0))))
        return total

    best = max(candidates, key=score)
    return best if score(best) > 0 else candidates[0]


def children_of(element: Any) -> list[Any]:
    children = ax_value(element, getattr(ApplicationServices, "kAXChildrenAttribute", "AXChildren"))
    return list(children) if is_ax_list(children) else []


def role_of(element: Any) -> str:
    role = ax_value(element, getattr(ApplicationServices, "kAXRoleAttribute", "AXRole"))
    return str(role or "")


def ax_tree_has_scrollable(root: Any, max_elements: int = 160, max_depth: int = 8) -> bool:
    queue: list[tuple[Any, int]] = [(root, 0)]
    seen: set[int] = set()
    visited = 0
    scroll_roles = {"AXScrollArea", "AXScrollBar"}
    scroll_attrs = {
        "AXVerticalScrollBar",
        "AXHorizontalScrollBar",
        "AXVisibleChildren",
        "AXScrollBar",
    }

    while queue and visited < max_elements:
        element, depth = queue.pop(0)
        key = id(element)
        if key in seen:
            continue
        seen.add(key)
        visited += 1

        role = role_of(element)
        if role in scroll_roles:
            return True

        attrs = ax_attribute_names(element)
        if attrs.intersection(scroll_attrs):
            if "AXVerticalScrollBar" in attrs:
                bar = ax_value(element, "AXVerticalScrollBar")
                if bar is not None:
                    return True
            elif role in {"AXWebArea", "AXList", "AXTable", "AXOutline", "AXCollection"}:
                return True

        if depth < max_depth:
            for child in children_of(element):
                queue.append((child, depth + 1))
    return False


def is_scrollable_window(window: dict[str, Any]) -> bool:
    pid = as_int(window.get("pid"))
    if pid <= 0:
        return False
    try:
        root = select_ax_window(pid, window)
        if root is None:
            return False
        return ax_tree_has_scrollable(root)
    except Exception:
        return False


def main() -> int:
    request = read_request()
    mode = request.get("mode", "auto")
    if mode not in {"auto", "hover", "visible", "pick", "frontmost", "fullpage"}:
        die('mode must be "auto", "hover", "visible", "pick", "frontmost", or "fullpage"', 2)

    check_permissions()

    if mode in {"auto", "hover", "visible", "fullpage"}:
        # Native dim+hover+click picker captures the image directly; recover
        # the clicked window's identity from the pointer. This also leaves the
        # pointer over the picked window so scroll-wheel events land there.
        image_path = capture_interactive()
        windows = list_windows()
        window = window_under_mouse(windows) or {
            "pid": 0, "windowid": 0, "app": "", "title": "",
            "bounds": {"x": 0, "y": 0, "w": 0, "h": 0},
        }
        want_full = mode == "fullpage" or (mode == "auto" and is_scrollable_window(window))
        if want_full and window.get("windowid"):
            result = capture_fullpage(window)
            print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
            return 0
        # visible / hover, auto-non-scrollable, or fullpage with no recovered
        # window → fall through to the single hover screenshot already captured.
    else:
        windows = list_windows()
        window = choose_window(windows) if mode == "pick" else frontmost_window(windows)
        image_path = capture_window(window)

    result = {
        "ok": True,
        "pid": window["pid"],
        "windowid": window["windowid"],
        "app": window["app"],
        "title": window["title"],
        "bounds": window["bounds"],
        "image_path": os.fspath(image_path),
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
