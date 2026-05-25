#!/usr/bin/env python3
"""Assemble capture, AX, and optional OCR outputs into the appsnap bundle."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_AX_MIN_CHARS = 80
DEFAULT_IMAGE_PRIMARY_CHARS = 1500


def image_primary_threshold() -> int:
    raw = os.environ.get("APPSNAP_IMAGE_PRIMARY_CHARS")
    if raw is None:
        return DEFAULT_IMAGE_PRIMARY_CHARS
    try:
        return max(0, int(raw))
    except ValueError:
        die("APPSNAP_IMAGE_PRIMARY_CHARS must be an integer", 2)


def die(message: str, code: int = 1) -> None:
    print(message.replace("\n", " "), file=sys.stderr)
    raise SystemExit(code)


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
    return request


def as_dict(value: Any, name: str, required: bool = True) -> dict[str, Any] | None:
    if value is None and not required:
        return None
    if not isinstance(value, dict):
        die(f"{name} must be an object", 2)
    return value


def as_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def ax_min_chars() -> int:
    raw = os.environ.get("APPSNAP_AX_MIN_CHARS")
    if raw is None:
        return DEFAULT_AX_MIN_CHARS
    try:
        parsed = int(raw)
    except ValueError:
        die("APPSNAP_AX_MIN_CHARS must be an integer", 2)
    return max(0, parsed)


def ax_is_rich(ax: dict[str, Any] | None, minimum_chars: int) -> bool:
    """AX text is rich enough to be the primary context (incl off-screen)."""
    if ax is None or ax.get("ok") is False or ax.get("ax_available") is False:
        return False
    return as_int(ax.get("char_count", len(clean_text(ax.get("text_markdown"))))) >= minimum_chars


def ocr_opt_in(request: dict[str, Any]) -> bool:
    """Local OCR is OFF by default. The consuming agent reads the high-res
    screenshot with its own vision (more accurate than macOS Vision OCR).
    Turn local OCR on only for non-vision / headless consumers."""
    if request.get("ocr_requested") is True:
        return True
    return os.environ.get("APPSNAP_OCR", "").strip().lower() in {"1", "true", "yes", "on"}


def run_ocr(image_path: str) -> dict[str, Any]:
    script = Path(__file__).with_name("ocr_fallback.py")
    proc = subprocess.run(
        [sys.executable, os.fspath(script)],
        input=json.dumps({"image_path": image_path}, ensure_ascii=False),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        die(f"OCR fallback failed: {stderr or proc.returncode}", 1)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        die(f"OCR fallback returned invalid JSON: {exc}", 1)
    if not isinstance(result, dict) or result.get("ok") is not True:
        die("OCR fallback returned an unsuccessful result", 1)
    return result


def capture_image_paths(capture: dict[str, Any]) -> list[str]:
    image_paths = capture.get("image_paths")
    if image_paths is not None:
        if not isinstance(image_paths, list) or not image_paths:
            die('capture "image_paths" must be a non-empty list', 2)
        normalized = []
        for path in image_paths:
            if not isinstance(path, str) or not path:
                die('capture "image_paths" entries must be non-empty strings', 2)
            normalized.append(path)
        return normalized

    image_path = capture.get("image_path")
    if not isinstance(image_path, str) or not image_path:
        die('capture must include "image_path" or "image_paths"', 2)
    return [image_path]


def merge_text(ax_text: str, ocr_text: str) -> str:
    if ax_text and ocr_text:
        if ocr_text in ax_text:
            return ax_text
        if ax_text in ocr_text:
            return ocr_text
        return f"{ax_text}\n\n---\n\n{ocr_text}"
    return ax_text or ocr_text



def compact_count(count: int) -> str:
    if count >= 1000:
        value = count / 1000
        return f"{value:.1f}k".replace(".0k", "k")
    return str(count)


def main() -> int:
    request = read_request()
    capture = as_dict(request.get("capture"), "capture")
    ax = as_dict(request.get("ax"), "ax", required=False)
    ocr = as_dict(request.get("ocr"), "ocr", required=False)
    assert capture is not None

    image_paths = capture_image_paths(capture)
    image_path = image_paths[0]

    minimum_chars = ax_min_chars()
    rich_ax = ax_is_rich(ax, minimum_chars)

    ax_text = clean_text(ax.get("text_markdown")) if ax else ""
    ocr_text = clean_text(ocr.get("text_markdown")) if ocr else ""

    # Local OCR is opt-in only, and only worth running when AX is thin.
    if not ocr_text and not rich_ax and ocr_opt_in(request):
        ocr = run_ocr(image_path)
        ocr_text = clean_text(ocr.get("text_markdown")) if ocr else ""

    if ax_text and ocr_text:
        text, text_source, via = merge_text(ax_text, ocr_text), "ax+ocr", "AX+OCR"
    elif ax_text:
        text, text_source, via = ax_text, "ax", "AX"
    elif ocr_text:
        text, text_source, via = ocr_text, "ocr", "OCR"
    else:
        text, text_source, via = "", "image-only", "image only"

    # The screenshot is primary context unless AX clearly returned the full
    # document. char-count alone can't prove AX completeness, so use a high
    # bar: only skip "read the image" when AX is available AND substantial.
    ax_chars = as_int((ax or {}).get("char_count", len(ax_text)))
    ax_available = bool(ax and ax.get("ok") is not False and ax.get("ax_available") is not False)
    read_image = not (ax_available and ax_chars >= image_primary_threshold())

    app = str(capture.get("app") or "Unknown app")
    title = str(capture.get("title") or "")
    truncated = bool((ax or {}).get("truncated", False))
    char_count = len(text)
    display_title = f" «{title}»" if title else ""
    tail = "; read the screenshot for visible content" if read_image else ""
    if text_source == "image-only":
        summary = f"appsnap of {app}{display_title} — image only (AX thin); read the screenshot"
    else:
        summary = f"appsnap of {app}{display_title} — {compact_count(char_count)} chars via {via}{tail}"

    result = {
        "image_path": image_path,
        "image_paths": image_paths,
        "text_markdown": text,
        "text_source": text_source,
        "read_image": read_image,
        "primary_context": "image" if read_image else "text",
        "app": app,
        "title": title,
        "truncated": truncated,
        "summary_line": summary,
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
