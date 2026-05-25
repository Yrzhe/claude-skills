# appsnap

Bring what's on your Mac screen into the agent. Hover-pick a window; appsnap returns a
high-res screenshot plus the window's Accessibility-tree text as context — an Appshot-style
"use this app as context" tool. **macOS only.** No network, no model calls.

## What it does

- **Hover-pick** a window (screen dims, hover highlights, click captures, ESC cancels) — all modes use this.
- **Smart `auto` default**: probes whether the window is scrollable.
  - scrollable → **full-page scroll-stitch**: scrolls top→bottom, stitches into a *seamless* long image
    (overlap-detected, no seams), **crops out static sticky sidebars**, and splits into readable tiles
    (height ≤ `APPSNAP_TILE_RATIO`×width, default 1.5 — because vision models downscale very tall images).
  - not scrollable → single visible screenshot.
- **Screenshot is primary context**: the consuming agent reads it with its own vision (more accurate than
  local OCR). AX text is supplementary — its unique value is off-screen content the app exposes.
- Silent capture (no shutter sound). Scroll has a **manual stop** (Esc / Return / click). Infinite-up chat
  apps are detected and captured from the current position down (honest `reached_top:false`).

## Modes

| Invocation | Behavior |
|---|---|
| `appsnap.sh` | auto: hover-pick → full-page if scrollable, else single visible |
| `appsnap.sh --fullpage` | force full-page scroll-stitch |
| `appsnap.sh --visible` | hover-pick, single visible (never scroll) |
| `appsnap.sh --pick` | GUI list picker instead of hover |
| `appsnap.sh --frontmost` | grab the frontmost window |
| `appsnap.sh --open` | open the result when done · `--json` raw bundle · `--ocr` force local OCR |
| `appsnap.sh --clean` | delete captures older than `APPSNAP_RETENTION_DAYS` (default 7) |

## Setup (one-time)

```bash
python3 -m venv <skill-dir>/.venv
<skill-dir>/.venv/bin/pip install -r <skill-dir>/requirements.txt
```

Grant the terminal **Accessibility** + **Screen & System Audio Recording** in System Settings → Privacy
& Security. Captures are saved to `~/Pictures/appsnap/` (override with `APPSNAP_DIR`).

## Honest limits

- A screenshot only captures visible pixels; off-screen content comes from AX text or from scroll-stitch.
- Canvas-heavy apps (Google Docs/Sheets/Slides/Gmail) expose little/no AX text → screenshot-only (same
  ceiling as Codex Appshot).
- Sticky-region cropping is heuristic (works when side panels are truly static); full-page mode is ACTIVE
  (it scrolls the picked window) and opt-in/auto only.
- Infinite-scroll history (chat) is not fully capturable — captured from current position downward.

License: MIT.
