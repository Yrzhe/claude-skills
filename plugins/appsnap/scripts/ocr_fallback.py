#!/usr/bin/env python3
"""Run local macOS Vision OCR on a screenshot and emit Component C JSON."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


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


def load_vision():
    try:
        import Foundation  # type: ignore
        import Vision  # type: ignore
    except Exception as exc:  # pragma: no cover - host dependency
        die(f"macOS Vision PyObjC framework unavailable: {exc}", 2)
    return Foundation, Vision


def recognized_text(image_path: Path) -> str:
    foundation, vision = load_vision()

    url = foundation.NSURL.fileURLWithPath_(os.fspath(image_path))
    request = vision.VNRecognizeTextRequest.alloc().init()

    accurate = getattr(vision, "VNRequestTextRecognitionLevelAccurate", None)
    if accurate is not None:
        request.setRecognitionLevel_(accurate)
    if hasattr(request, "setUsesLanguageCorrection_"):
        request.setUsesLanguageCorrection_(True)

    handler = vision.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
    performed = handler.performRequests_error_([request], None)
    if isinstance(performed, tuple):
        ok = bool(performed[0])
        error = performed[1] if len(performed) > 1 else None
    else:
        ok = bool(performed)
        error = None
    if not ok:
        die(f"vision OCR failed: {error or 'unknown error'}", 1)

    rows: list[tuple[float, float, str]] = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if not candidates:
            continue
        text = str(candidates[0].string()).strip()
        if not text:
            continue
        try:
            box = observation.boundingBox()
            y = float(box.origin.y)
            x = float(box.origin.x)
        except Exception:
            y = 0.0
            x = 0.0
        rows.append((-y, x, text))

    rows.sort()
    return "\n".join(row[2] for row in rows)


def main() -> int:
    request = read_request()
    image_value = request.get("image_path")
    if not isinstance(image_value, str) or not image_value:
        die('input must include "image_path"', 2)

    image_path = Path(image_value).expanduser()
    if not image_path.is_file():
        die(f"image_path does not exist: {image_path}", 2)

    text = recognized_text(image_path.resolve())
    result = {
        "ok": True,
        "source": "ocr",
        "text_markdown": text,
        "char_count": len(text),
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
