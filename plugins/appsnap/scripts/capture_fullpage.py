#!/usr/bin/env python3
"""Active full-page capture: scroll a picked window and stitch frames."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    import numpy as np
    from PIL import Image, ImageChops, ImageStat
except Exception as exc:  # pragma: no cover - host dependency
    print(f"image dependencies unavailable: {exc}", file=sys.stderr)
    raise SystemExit(2)


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


def read_request() -> dict[str, Any]:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"invalid stdin JSON: {exc}", 2)
    if not isinstance(payload, dict):
        die("stdin JSON must be an object", 2)
    for key in ("pid", "windowid", "app", "title", "bounds"):
        if key not in payload:
            die(f"missing required field: {key}", 2)
    if not int(payload.get("pid") or 0) or not int(payload.get("windowid") or 0):
        die("fullpage capture requires nonzero pid and windowid", 2)
    return payload


def output_dir() -> Path:
    raw = os.environ.get("APPSNAP_DIR")
    base = Path(raw).expanduser() if raw else (Path.home() / "Pictures" / "appsnap")
    base.mkdir(parents=True, exist_ok=True)
    return base


def max_frames() -> int:
    raw = os.environ.get("APPSNAP_FULLPAGE_MAX_FRAMES", "30")
    try:
        value = int(raw)
    except ValueError:
        die("APPSNAP_FULLPAGE_MAX_FRAMES must be an integer", 2)
    return max(2, min(value, 100))


def up_max_frames() -> int:
    raw = os.environ.get("APPSNAP_UP_MAX_FRAMES", "15")
    try:
        value = int(raw)
    except ValueError:
        die("APPSNAP_UP_MAX_FRAMES must be an integer", 2)
    return max(1, min(value, 100))


def tile_ratio() -> float:
    raw = os.environ.get("APPSNAP_TILE_RATIO", "1.5")
    try:
        value = float(raw)
    except ValueError:
        die("APPSNAP_TILE_RATIO must be a number", 2)
    return max(0.5, min(value, 4.0))


def tile_height_limit(width: int) -> int:
    ratio_limit = max(1, int(width * tile_ratio()))
    raw_backstop = os.environ.get("APPSNAP_TILE_MAX_PX")
    if raw_backstop is None or not raw_backstop.strip():
        return ratio_limit
    try:
        backstop = int(raw_backstop)
    except ValueError:
        die("APPSNAP_TILE_MAX_PX must be an integer", 2)
    return max(1, min(ratio_limit, backstop))


def raise_window(pid: int, window: dict[str, Any]) -> None:
    try:
        app = ApplicationServices.AXUIElementCreateApplication(pid)
        windows, err = ApplicationServices.AXUIElementCopyAttributeValue(app, "AXWindows", None)
        if err == 0 and windows:
            target = windows[0]
            title = str(window.get("title") or "")
            bounds = window.get("bounds") or {}
            for candidate in windows:
                score = 0
                candidate_title, title_err = ApplicationServices.AXUIElementCopyAttributeValue(candidate, "AXTitle", None)
                if title and title_err == 0 and str(candidate_title) == title:
                    score += 2
                pos, pos_err = ApplicationServices.AXUIElementCopyAttributeValue(candidate, "AXPosition", None)
                size, size_err = ApplicationServices.AXUIElementCopyAttributeValue(candidate, "AXSize", None)
                if pos_err == 0 and size_err == 0:
                    try:
                        if abs(float(pos.x) - float(bounds.get("x", 0))) <= 4:
                            score += 1
                        if abs(float(pos.y) - float(bounds.get("y", 0))) <= 4:
                            score += 1
                        if abs(float(size.width) - float(bounds.get("w", 0))) <= 8:
                            score += 1
                        if abs(float(size.height) - float(bounds.get("h", 0))) <= 8:
                            score += 1
                    except Exception:
                        pass
                if score >= 2:
                    target = candidate
                    break
            ApplicationServices.AXUIElementPerformAction(target, "AXRaise")
    except Exception:
        pass

    app_name = str(window.get("app") or "")
    if app_name:
        subprocess.run(
            ["osascript", "-e", f'tell application "{app_name}" to activate'],
            text=True,
            capture_output=True,
            check=False,
        )
    time.sleep(0.35)


def move_pointer_into_window(bounds: dict[str, Any]) -> None:
    try:
        x = int(bounds.get("x") or 0) + max(40, int((bounds.get("w") or 800) * 0.50))
        y = int(bounds.get("y") or 0) + max(80, int((bounds.get("h") or 600) * 0.50))
        Quartz.CGWarpMouseCursorPosition((x, y))
        Quartz.CGAssociateMouseAndMouseCursorPosition(True)
        time.sleep(0.1)
    except Exception:
        pass


def capture_frame(windowid: int, frame_dir: Path, index: int) -> Path:
    path = frame_dir / f"frame-{index:03d}.png"
    proc = subprocess.run(
        ["screencapture", "-x", "-l", str(windowid), "-o", str(path)],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        die(f"screencapture failed: {stderr or proc.returncode}", 1)
    if not path.is_file() or path.stat().st_size <= 0:
        die("screencapture did not create a non-empty frame", 1)
    return path


def scroll_window(bounds: dict[str, Any], direction: str) -> None:
    height = int(bounds.get("h") or 900)
    scroll_pixels = max(350, int(height * 0.70))
    if direction == "up":
        delta = scroll_pixels
    elif direction == "down":
        delta = -scroll_pixels
    else:
        die("scroll direction must be up or down", 2)
    event = Quartz.CGEventCreateScrollWheelEvent(
        None,
        Quartz.kCGScrollEventUnitPixel,
        1,
        delta,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def user_stop_pressed() -> bool:
    state = Quartz.kCGEventSourceStateHIDSystemState
    try:
        esc = bool(Quartz.CGEventSourceKeyState(state, 53))
        enter = bool(Quartz.CGEventSourceKeyState(state, 36))
        left_mouse = bool(Quartz.CGEventSourceButtonState(state, 0))
        return esc or enter or left_mouse
    except Exception:
        return False


def wait_after_scroll() -> bool:
    delay = float(os.environ.get("APPSNAP_FULLPAGE_SCROLL_DELAY", "0.65"))
    deadline = time.monotonic() + max(0.0, delay)
    while time.monotonic() < deadline:
        if user_stop_pressed():
            return True
        time.sleep(0.05)
    return user_stop_pressed()


def wait_for_stop_release(timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and user_stop_pressed():
        time.sleep(0.05)


def gray_small(image: Image.Image, width: int = 420) -> Image.Image:
    image = image.convert("L")
    if image.width <= width:
        return image
    height = max(1, int(image.height * (width / image.width)))
    return image.resize((width, height), Image.Resampling.BILINEAR)


def rms_diff(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(gray_small(a), gray_small(b))
    stat = ImageStat.Stat(diff)
    return sum(value * value for value in stat.rms) ** 0.5


def unchanged_top_height(prev: Image.Image, curr: Image.Image) -> int:
    limit = min(prev.height, curr.height, max(80, int(prev.height * 0.30)))
    prev_g = prev.convert("L")
    curr_g = curr.convert("L")
    same_until = 0
    sample_step = 8
    for y in range(0, limit, sample_step):
        p = prev_g.crop((0, y, prev.width, min(y + sample_step, prev.height)))
        c = curr_g.crop((0, y, curr.width, min(y + sample_step, curr.height)))
        if rms_diff(p, c) > 4.0:
            break
        same_until = y + sample_step
    return min(same_until, limit)


def content_crop(image: Image.Image, top: int) -> Image.Image:
    top = max(0, min(top, image.height - 1))
    return image.crop((0, top, image.width, image.height))


def best_overlap(prev: Image.Image, curr: Image.Image) -> int:
    max_overlap = min(prev.height, curr.height, int(prev.height * 0.85), int(curr.height * 0.85))
    min_overlap = min(max_overlap, 80)
    if max_overlap <= min_overlap:
        return 0
    step = max(12, max_overlap // 80)
    best = (10**9, 0)
    for overlap in range(min_overlap, max_overlap + 1, step):
        a = prev.crop((0, prev.height - overlap, prev.width, prev.height))
        b = curr.crop((0, 0, curr.width, overlap))
        score = rms_diff(a, b)
        if score < best[0]:
            best = (score, overlap)
    return best[1] if best[0] < 18.0 else 0


def _rgb_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGB"), dtype=np.int16)


def _largest_true_run(values: np.ndarray) -> tuple[int, int]:
    best_start = 0
    best_end = len(values)
    best_len = -1
    start: int | None = None
    for index, value in enumerate(values):
        if bool(value):
            if start is None:
                start = index
        elif start is not None:
            run_len = index - start
            if run_len > best_len:
                best_start, best_end, best_len = start, index, run_len
            start = None
    if start is not None:
        run_len = len(values) - start
        if run_len > best_len:
            best_start, best_end = start, len(values)
    return best_start, best_end


def detect_stitch_region(images: list[Image.Image]) -> tuple[int, int, int, int]:
    """Find the horizontally scrolling content band and static top/bottom rows."""
    if len(images) < 2:
        return 0, images[0].width, 0, 0

    width, height = images[0].size
    if any(image.size != (width, height) for image in images):
        return 0, width, 0, 0

    arrays = np.stack([_rgb_array(image) for image in images], axis=0)
    pixel_range = arrays.max(axis=0) - arrays.min(axis=0)
    static_pixels = np.all(pixel_range <= 8, axis=2)
    changed_pixels = ~static_pixels

    row_changed = changed_pixels.mean(axis=1)
    col_changed = changed_pixels.mean(axis=0)

    row_threshold = max(0.015, min(0.12, float(np.percentile(row_changed, 75)) * 0.35))
    col_threshold = max(0.015, min(0.12, float(np.percentile(col_changed, 75)) * 0.35))

    changing_rows = row_changed > row_threshold
    changing_cols = col_changed > col_threshold

    row_start, row_end = _largest_true_run(changing_rows)
    col_start, col_end = _largest_true_run(changing_cols)

    if row_end - row_start < max(80, int(height * 0.20)):
        row_start, row_end = 0, height
    if col_end - col_start < max(120, int(width * 0.20)):
        col_start, col_end = 0, width

    # Keep a little context so antialiasing at the scroll column edge is not cut.
    pad_x = min(96, max(24, width // 32))
    x0 = max(0, col_start - pad_x)
    x1 = min(width, col_end + pad_x)

    first = _rgb_array(images[0])
    inspect_top = int(height * 0.18)
    inspect_bottom = max(inspect_top + 1, int(height * 0.95))

    def static_side_has_content(side: np.ndarray) -> bool:
        if side.size == 0 or side.shape[1] < max(24, width // 40):
            return False
        background = np.median(side.reshape(-1, 3), axis=0)
        distance = np.mean(np.abs(side - background), axis=2)
        density = float(np.mean(distance > 18))
        spread = float(np.std(side))
        return density > 0.025 or spread > 18.0

    if not static_side_has_content(first[inspect_top:inspect_bottom, :x0]):
        x0 = 0
    if not static_side_has_content(first[inspect_top:inspect_bottom, x1:]):
        x1 = width

    static_top = max(0, row_start)
    static_bottom = max(0, height - row_end)
    if static_top > int(height * 0.35):
        static_top = 0
    if static_bottom > int(height * 0.35):
        static_bottom = 0
    return x0, x1, static_top, static_bottom


def crop_scroll_area(image: Image.Image, x0: int, x1: int, top: int, bottom: int) -> Image.Image:
    lower = image.height - max(0, bottom)
    if lower <= top:
        return image.crop((x0, 0, x1, image.height))
    return image.crop((x0, top, x1, lower))


def central_match_array(image: Image.Image) -> np.ndarray:
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    if gray.size == 0:
        return gray
    left = int(gray.shape[1] * 0.25)
    right = int(gray.shape[1] * 0.75)
    if right <= left:
        left, right = 0, gray.shape[1]
    strip = gray[:, left:right]
    if strip.shape[1] > 420:
        step = max(1, strip.shape[1] // 420)
        strip = strip[:, ::step]
    return strip


def overlap_score(prev_strip: np.ndarray, curr_strip: np.ndarray, overlap: int) -> float:
    a = prev_strip[-overlap:, :]
    b = curr_strip[:overlap, :]
    if a.shape != b.shape or a.size == 0:
        return float("inf")
    return float(np.mean(np.abs(a - b)))


def best_numpy_overlap(prev: Image.Image, curr: Image.Image) -> int:
    max_overlap = min(prev.height, curr.height, int(prev.height * 0.92), int(curr.height * 0.92))
    min_overlap = min(max_overlap, max(48, int(min(prev.height, curr.height) * 0.08)))
    if max_overlap <= min_overlap:
        return 0

    prev_strip = central_match_array(prev)
    curr_strip = central_match_array(curr)
    if prev_strip.size == 0 or curr_strip.size == 0:
        return 0

    coarse_step = max(8, (max_overlap - min_overlap) // 90)
    candidates = range(min_overlap, max_overlap + 1, coarse_step)
    coarse = sorted((overlap_score(prev_strip, curr_strip, value), value) for value in candidates)
    if not coarse:
        return 0

    _, coarse_best = coarse[0]
    refine_start = max(min_overlap, coarse_best - coarse_step)
    refine_end = min(max_overlap, coarse_best + coarse_step)
    refined = sorted((overlap_score(prev_strip, curr_strip, value), value) for value in range(refine_start, refine_end + 1))
    if not refined:
        return 0

    best_score, best_value = refined[0]
    if not np.isfinite(best_score):
        return 0

    baseline = min(
        overlap_score(prev_strip, curr_strip, min_overlap),
        overlap_score(prev_strip, curr_strip, max_overlap),
    )
    # Animated/lazy-loaded regions can make every candidate poor. In that case
    # return 0 and the caller falls back to naive append for this pair.
    if best_score > 28.0 and best_score > baseline * 0.72:
        return 0
    return int(best_value)


def numpy_near_identical(prev: Image.Image, curr: Image.Image) -> bool:
    if prev.size != curr.size:
        return False
    prev_arr = np.asarray(prev.convert("L"), dtype=np.int16)
    curr_arr = np.asarray(curr.convert("L"), dtype=np.int16)
    if prev_arr.size == 0:
        return True
    return float(np.mean(np.abs(prev_arr - curr_arr))) < 2.0


def near_identical(prev: Image.Image, curr: Image.Image, static_top: int) -> bool:
    a = content_crop(prev, static_top)
    b = content_crop(curr, static_top)
    if a.size != b.size:
        b = b.resize(a.size, Image.Resampling.BILINEAR)
    return rms_diff(a, b) < 2.5


def stitch_frames(frame_paths: list[Path]) -> Image.Image:
    images = [Image.open(path).convert("RGBA") for path in frame_paths]
    if not images:
        die("no frames captured", 1)

    x0, x1, static_top, static_bottom = detect_stitch_region(images)
    header = images[0].crop((x0, 0, x1, static_top)) if static_top > 0 else None
    footer = (
        images[-1].crop((x0, images[-1].height - static_bottom, x1, images[-1].height))
        if static_bottom > 0
        else None
    )
    scroll_frames = [crop_scroll_area(image, x0, x1, static_top, static_bottom) for image in images]

    stitched = scroll_frames[0].copy()
    for prev, curr in zip(scroll_frames, scroll_frames[1:]):
        if numpy_near_identical(prev, curr):
            continue
        try:
            overlap = best_numpy_overlap(prev, curr)
        except Exception:
            overlap = 0
        addition = curr.crop((0, overlap, curr.width, curr.height))
        if addition.height <= 0:
            continue
        canvas = Image.new("RGBA", (stitched.width, stitched.height + addition.height), (255, 255, 255, 0))
        canvas.paste(stitched, (0, 0))
        canvas.paste(addition, (0, stitched.height))
        stitched = canvas

    pieces = [part for part in (header, stitched, footer) if part is not None and part.height > 0]
    if len(pieces) > 1:
        total_height = sum(part.height for part in pieces)
        canvas = Image.new("RGBA", (stitched.width, total_height), (255, 255, 255, 0))
        y = 0
        for part in pieces:
            canvas.paste(part, (0, y))
            y += part.height
        stitched.close()
        stitched = canvas

    for image in scroll_frames:
        image.close()
    if header is not None:
        header.close()
    if footer is not None:
        footer.close()
    for image in images:
        image.close()
    return stitched


def load_frame(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def go_to_top(windowid: int, bounds: dict[str, Any], frame_dir: Path) -> tuple[Path, bool, str, str]:
    """Return the current/top frame path, reached_top, stopped_by, note."""
    current_path = capture_frame(windowid, frame_dir, -1)
    current = load_frame(current_path)
    note = ""

    for index in range(up_max_frames()):
        if user_stop_pressed():
            current.close()
            return current_path, False, "user", note
        scroll_window(bounds, "up")
        if wait_after_scroll():
            current.close()
            return current_path, False, "user", note

        next_path = capture_frame(windowid, frame_dir, -(index + 2))
        next_image = load_frame(next_path)
        static_top = unchanged_top_height(current, next_image)
        if near_identical(current, next_image, static_top):
            current.close()
            next_image.close()
            current_path.unlink(missing_ok=True)
            return next_path, True, "bottom", note

        current.close()
        current_path.unlink(missing_ok=True)
        current_path = next_path
        current = next_image

    current.close()
    note = "infinite-up detected; captured from current position downward, not full history"
    return current_path, False, "max_frames", note


def capture_downward(
    windowid: int,
    bounds: dict[str, Any],
    frame_dir: Path,
    start_path: Path,
    up_stopped_by: str,
) -> tuple[list[Path], str, bool]:
    frames = [start_path]
    previous = load_frame(start_path)
    stopped_by = "max_frames"
    reached_bottom = False

    if up_stopped_by == "user":
        previous.close()
        return frames, "user", False

    for index in range(1, max_frames()):
        if user_stop_pressed():
            stopped_by = "user"
            break
        scroll_window(bounds, "down")
        if wait_after_scroll():
            stopped_by = "user"
            break

        path = capture_frame(windowid, frame_dir, index)
        current = load_frame(path)
        static_top = unchanged_top_height(previous, current)
        if near_identical(previous, current, static_top):
            current.close()
            path.unlink(missing_ok=True)
            stopped_by = "bottom"
            reached_bottom = True
            break

        frames.append(path)
        previous.close()
        previous = current

    previous.close()
    return frames, stopped_by, reached_bottom


def save_tiles(stitched: Image.Image) -> tuple[list[str], list[dict[str, int]]]:
    limit = tile_height_limit(stitched.width)
    base = output_dir()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    height = stitched.height

    # Build tile boundaries, then fold a too-short final sliver into the
    # previous tile so we never emit a tiny leftover strip as its own image.
    boundaries: list[list[int]] = []
    top = 0
    while top < height:
        boundaries.append([top, min(top + limit, height)])
        top += limit
    min_tail = max(120, limit // 8)
    if len(boundaries) >= 2 and (boundaries[-1][1] - boundaries[-1][0]) < min_tail:
        boundaries[-2][1] = boundaries[-1][1]
        boundaries.pop()

    image_paths: list[str] = []
    dimensions: list[dict[str, int]] = []
    total = len(boundaries)
    for index, (t, b) in enumerate(boundaries, start=1):
        tile = stitched.crop((0, t, stitched.width, b))
        suffix = f"{index:02d}-of-{total:02d}"
        out = base / f"appsnap-fullpage-{stamp}-{suffix}.png"
        tile.save(out)
        dimensions.append({"width": tile.width, "height": tile.height})
        image_paths.append(os.fspath(out.resolve()))
        tile.close()
    return image_paths, dimensions


def main() -> int:
    window = read_request()
    pid = int(window["pid"])
    windowid = int(window["windowid"])
    bounds = window.get("bounds") or {}
    frame_limit = max_frames()
    frame_dir = Path(tempfile.mkdtemp(prefix="appsnap-fullpage-frames-"))

    raise_window(pid, window)
    move_pointer_into_window(bounds)
    wait_for_stop_release()

    start_path, reached_top, up_stopped_by, note = go_to_top(windowid, bounds, frame_dir)
    frames, stopped_by, reached_bottom = capture_downward(windowid, bounds, frame_dir, start_path, up_stopped_by)
    if not frames:
        die("no non-duplicate frames captured", 1)

    stitched = stitch_frames(frames)
    width, height = stitched.size
    image_paths, tile_dimensions = save_tiles(stitched)
    stitched.close()

    result = {
        "ok": True,
        "image_paths": image_paths,
        "stitched": True,
        "frames": len(frames),
        "stopped_by": stopped_by,
        "reached_top": reached_top,
        "reached_bottom": reached_bottom,
        "pid": pid,
        "windowid": windowid,
        "app": window.get("app", ""),
        "title": window.get("title", ""),
        "bounds": bounds,
        "width": width,
        "height": height,
        "tile_dimensions": tile_dimensions,
        "note": note,
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        die(f"capture_fullpage failed: {exc}", 1)
