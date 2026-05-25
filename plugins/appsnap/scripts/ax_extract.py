#!/usr/bin/env python3
"""Extract text exposed by a macOS app/window Accessibility tree."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any


GUIDANCE = (
    "Grant Accessibility to this terminal app: "
    "System Settings > Privacy & Security > Accessibility, then restart the terminal."
)

MIN_REAL_TEXT_CHARS = 500
MAX_OUTPUT_CHARS = 24000
MAX_ELEMENTS = 10000


def die(message: str, code: int = 1) -> None:
    print(message.replace("\n", " "), file=sys.stderr)
    raise SystemExit(code)


def load_frameworks():
    try:
        import ApplicationServices  # type: ignore
        import Quartz  # type: ignore
    except Exception as exc:  # pragma: no cover - host dependency
        die(f"macOS PyObjC frameworks unavailable: {exc}", 2)
    return ApplicationServices, Quartz


AS, Quartz = load_frameworks()


TEXT_ATTRIBUTES = [
    getattr(AS, "kAXValueAttribute", "AXValue"),
    getattr(AS, "kAXTitleAttribute", "AXTitle"),
    getattr(AS, "kAXDescriptionAttribute", "AXDescription"),
    getattr(AS, "kAXLabelAttribute", "AXLabel"),
]


@dataclass
class WindowInfo:
    windowid: int
    pid: int
    title: str
    x: int
    y: int
    w: int
    h: int


def read_request() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        die("stdin JSON is required", 2)
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"invalid stdin JSON: {exc}", 2)
    if not isinstance(request, dict):
        die("stdin JSON must be an object", 2)
    if "pid" not in request:
        die("stdin JSON must include pid", 2)
    try:
        request["pid"] = int(request["pid"])
    except Exception:
        die("pid must be an integer", 2)
    if request["pid"] <= 0:
        die("pid must be a positive integer", 2)
    if request.get("windowid") is not None:
        try:
            request["windowid"] = int(request["windowid"])
        except Exception:
            die("windowid must be an integer when provided", 2)
    return request


def ax_value(element: Any, attribute: str) -> Any | None:
    try:
        error, value = AS.AXUIElementCopyAttributeValue(element, attribute, None)
    except Exception:
        return None
    if error != 0:
        return None
    return value


def ax_attribute_names(element: Any) -> set[str]:
    try:
        error, names = AS.AXUIElementCopyAttributeNames(element, None)
    except Exception:
        return set()
    if error != 0 or not names:
        return set()
    return {str(name) for name in names}


def as_clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.replace("\r\n", "\n").replace("\r", "\n").split())
    if isinstance(value, bytes):
        try:
            return as_clean_text(value.decode("utf-8", "replace"))
        except Exception:
            return ""
    if isinstance(value, (int, float, bool)):
        return str(value)
    if is_ax_list(value):
        parts = [as_clean_text(item) for item in value]
        return " ".join(part for part in parts if part)
    return ""


def is_ax_list(value: Any) -> bool:
    if isinstance(value, (str, bytes, bytearray)):
        return False
    if isinstance(value, (list, tuple)):
        return True
    return hasattr(value, "__iter__") and hasattr(value, "__len__")


def role_of(element: Any) -> str:
    return as_clean_text(ax_value(element, getattr(AS, "kAXRoleAttribute", "AXRole")))


def element_texts(element: Any) -> list[str]:
    seen: set[str] = set()
    texts: list[str] = []
    available = ax_attribute_names(element)
    for attribute in TEXT_ATTRIBUTES:
        if available and str(attribute) not in available:
            continue
        text = as_clean_text(ax_value(element, str(attribute)))
        if not text or text in seen:
            continue
        seen.add(text)
        texts.append(text)
    return texts


def children_of(element: Any) -> list[Any]:
    children = ax_value(element, getattr(AS, "kAXChildrenAttribute", "AXChildren"))
    if is_ax_list(children):
        return list(children)
    return []


def list_cg_windows(pid: int) -> list[WindowInfo]:
    options = Quartz.kCGWindowListOptionAll | Quartz.kCGWindowListExcludeDesktopElements
    raw_windows = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID) or []
    windows: list[WindowInfo] = []
    for info in raw_windows:
        data = dict(info)
        if int(data.get(Quartz.kCGWindowOwnerPID, 0) or 0) != pid:
            continue
        bounds = data.get(Quartz.kCGWindowBounds) or {}
        windows.append(
            WindowInfo(
                windowid=int(data.get(Quartz.kCGWindowNumber, 0) or 0),
                pid=pid,
                title=str(data.get(Quartz.kCGWindowName) or ""),
                x=int(bounds.get("X", 0) or 0),
                y=int(bounds.get("Y", 0) or 0),
                w=int(bounds.get("Width", 0) or 0),
                h=int(bounds.get("Height", 0) or 0),
            )
        )
    return windows


def ax_point(element: Any, attribute: str) -> tuple[int, int] | None:
    value = ax_value(element, attribute)
    if value is None:
        return None
    try:
        return tuple(int(round(part)) for part in value)  # type: ignore[arg-type, return-value]
    except Exception:
        return None


def score_window(ax_window: Any, cg_window: WindowInfo) -> int:
    score = 0
    title = as_clean_text(ax_value(ax_window, getattr(AS, "kAXTitleAttribute", "AXTitle")))
    if title and cg_window.title and title == cg_window.title:
        score += 100
    elif title and cg_window.title and (title in cg_window.title or cg_window.title in title):
        score += 50

    pos = ax_point(ax_window, getattr(AS, "kAXPositionAttribute", "AXPosition"))
    size = ax_point(ax_window, getattr(AS, "kAXSizeAttribute", "AXSize"))
    if pos:
        score += max(0, 40 - abs(pos[0] - cg_window.x) - abs(pos[1] - cg_window.y))
    if size:
        score += max(0, 40 - abs(size[0] - cg_window.w) - abs(size[1] - cg_window.h))
    return score


def select_root(app: Any, pid: int, windowid: int | None) -> tuple[Any, str]:
    windows = ax_value(app, getattr(AS, "kAXWindowsAttribute", "AXWindows"))
    ax_windows = list(windows) if is_ax_list(windows) else []

    if windowid is None:
        focused = ax_value(app, getattr(AS, "kAXFocusedWindowAttribute", "AXFocusedWindow"))
        if focused is not None:
            return focused, "focused AX window"
        if ax_windows:
            return ax_windows[0], "first AX window"
        return app, "application AX root"

    cg_window = next((window for window in list_cg_windows(pid) if window.windowid == windowid), None)
    if cg_window is None:
        return app, "windowid not found in CoreGraphics list; used application AX root"
    if not ax_windows:
        return app, "application exposes no AXWindows; used application AX root"

    best = max(ax_windows, key=lambda candidate: score_window(candidate, cg_window))
    score = score_window(best, cg_window)
    if score <= 0:
        return app, "could not match CoreGraphics windowid to an AX window; used application AX root"
    return best, f"matched windowid by AX title/bounds score {score}"


def markdown_line(depth: int, role: str, texts: list[str]) -> str:
    indent = "  " * min(depth, 8)
    label = role or "AXElement"
    body = " | ".join(texts)
    if depth == 0:
        return f"# {body or label}" if body else f"# {label}"
    return f"{indent}- {label}: {body}" if body else f"{indent}- {label}"


def walk(element: Any, depth: int, lines: list[str], state: dict[str, int | bool], seen: set[int]) -> None:
    if state["element_count"] >= MAX_ELEMENTS:
        state["element_limit_hit"] = True
        return
    key = id(element)
    if key in seen:
        return
    seen.add(key)

    state["element_count"] += 1
    texts = element_texts(element)
    role = role_of(element)
    if texts:
        lines.append(markdown_line(depth, role, texts))

    for child in children_of(element):
        walk(child, depth + 1, lines, state, seen)


def truncate_markdown(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text, False
    marker = "\n\n[truncated: AX text exceeded output budget]\n"
    budget = MAX_OUTPUT_CHARS - len(marker)
    head = text[: max(0, budget)]
    last_break = head.rfind("\n")
    if last_break > MAX_OUTPUT_CHARS // 2:
        head = head[:last_break]
    return head.rstrip() + marker, True


def main() -> int:
    request = read_request()
    if not bool(AS.AXIsProcessTrusted()):
        die(GUIDANCE, 2)
    timeout = getattr(AS, "AXUIElementSetMessagingTimeout", None)
    if timeout is not None:
        try:
            timeout(AS.AXUIElementCreateSystemWide(), 2.0)
        except Exception:
            pass

    pid = request["pid"]
    windowid = request.get("windowid")
    app = AS.AXUIElementCreateApplication(pid)
    root, scope_note = select_root(app, pid, windowid)

    lines: list[str] = []
    state: dict[str, int | bool] = {"element_count": 0, "element_limit_hit": False}
    walk(root, 0, lines, state, set())
    full_text = "\n".join(lines).strip()
    text_markdown, truncated = truncate_markdown(full_text)
    element_count = int(state["element_count"])
    char_count = len(full_text)
    notes = []
    if scope_note:
        notes.append(scope_note)
    if state["element_limit_hit"]:
        notes.append(f"stopped after {MAX_ELEMENTS} AX elements")
    if char_count < MIN_REAL_TEXT_CHARS:
        notes.append(f"AX exposed fewer than {MIN_REAL_TEXT_CHARS} chars of text; use OCR fallback")

    result = {
        "ok": True,
        "source": "ax",
        "text_markdown": text_markdown,
        "char_count": char_count,
        "element_count": element_count,
        "truncated": truncated,
        "ax_available": char_count >= MIN_REAL_TEXT_CHARS,
        "note": "; ".join(notes),
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
