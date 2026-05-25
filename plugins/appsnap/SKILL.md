---
name: appsnap
description: 'Capture a Mac app window as agent context. Use when the user asks to snap, inspect, read, capture, summarize, or work from the current Mac window, a visible app, a selected window, or an app screenshot. Strongly prefer for Appshot-like requests, "what is on this window", "use this app as context", and "grab the window text". SKIP for remote websites/files that can be fetched directly, for controlling the UI, clicking, typing, automating actions, or extracting hidden Google Docs/Sheets/Slides/Gmail canvas text beyond what macOS Accessibility exposes.'
---

# appsnap

Capture one selected macOS window and return the screenshot plus extracted text as context.

## Scope

- Use local macOS APIs only. Do not use network or model calls inside scripts.
- Treat the result as passive context. Do not click, type, or control the app.
- Exception: default auto mode and `--fullpage` / `{"mode":"fullpage"}` may be ACTIVE. Auto hover-picks a
  window and scroll-stitches only when a bounded AX probe finds a scrollable area. `--visible` forces a
  passive single visible screenshot.
- **The screenshot is primary context; you (the consuming agent) read it with your own vision.** Accessibility (AX) text is supplementary: its unique value is off-screen / not-scrolled-into-view content. Local OCR is OFF by default — your own vision reads a high-res screenshot more accurately than macOS Vision OCR. Only opt into OCR for non-vision / headless consumers.
- Be honest for canvas-heavy apps (Google Docs, Sheets, Slides, Gmail, many browsers): AX may expose little or no text. In that case `assemble.py` returns `read_image:true` and you must read the screenshot for the visible content. Off-screen canvas text is not reachable by anyone unless the app exposes it through AX.

## One-time setup

Scripts need macOS PyObjC frameworks. Create a venv and install:

```bash
python3 -m venv <skill-dir>/.venv
<skill-dir>/.venv/bin/pip install -r <skill-dir>/requirements.txt
```

Run every script below with `<skill-dir>/.venv/bin/python` (not the system python3).

## Flow

1. Check permissions:

   ```bash
   python3 <skill-dir>/scripts/check_permissions.py
   ```

   If it exits nonzero, stop and show its one-line stderr guidance.

2. Capture a window:

   ```bash
   python3 <skill-dir>/scripts/capture.py
   ```

   Stdin is optional. Default is `{"mode":"auto"}`. Use `{"mode":"visible"}` for hover-pick without scrolling,
   `{"mode":"fullpage"}` to force active scroll-stitching, or `{"mode":"frontmost"}` only when the user
   explicitly wants the frontmost window.

3. Extract AX text with the capture output:

   ```bash
   python3 <skill-dir>/scripts/ax_extract.py
   ```

   Pass `{"pid":123,"windowid":456}` from the capture JSON. If `ax_extract.py` is unavailable or returns `ax_available:false`, continue to OCR.

4. Assemble the final bundle (OCR stays off by default):

   ```bash
   python3 <skill-dir>/scripts/assemble.py
   ```

   Pass `{"capture":{...},"ax":{...},"ocr":null}`. To force local OCR for a
   non-vision consumer, pass `{"ocr_requested":true}` or set `APPSNAP_OCR=1`.

5. Present the bundle to the current agent and ACT ON `read_image`:

   - Always surface `image_path` (the high-res screenshot) and `text_markdown`.
     For full-page capture, surface every path in `image_paths`.
   - If `read_image` is `true` (AX was thin/absent — common for browsers and
     canvas apps), **read the screenshot yourself** for the visible content;
     `text_markdown` only covers what AX exposed.
   - If `read_image` is `false`, AX returned the full document; `text_markdown`
     is the primary context and the image is confirmation.

`scripts/ocr_fallback.py` exists for the opt-in / headless path: pass
`{"image_path":"<abs png>"}`; it recovers visible text only.

## Script Contracts

### `scripts/capture.py`

Input:

```json
{"mode":"auto"}
```

Output:

```json
{"ok":true,"pid":123,"windowid":456,"app":"Safari","title":"...","bounds":{"x":0,"y":0,"w":1440,"h":900},"image_path":"/abs/window.png"}
```

For opt-in active full-page mode:

```json
{"ok":true,"pid":123,"windowid":456,"app":"Safari","title":"...","bounds":{"x":0,"y":0,"w":1440,"h":900},"image_paths":["/abs/page-01.png"],"stitched":true,"frames":5,"stopped_by":"bottom"}
```

### `scripts/ax_extract.py`

Input:

```json
{"pid":123,"windowid":456}
```

Output:

```json
{"ok":true,"source":"ax","text_markdown":"...","char_count":123,"element_count":45,"truncated":false,"ax_available":true,"note":""}
```

### `scripts/ocr_fallback.py`

Input:

```json
{"image_path":"/abs/window.png"}
```

Output:

```json
{"ok":true,"source":"ocr","text_markdown":"...","char_count":123}
```

### `scripts/assemble.py`

Input:

```json
{"capture":{},"ax":{},"ocr":null}
```

Output:

```json
{"image_path":"/abs/window.png","image_paths":["/abs/window.png"],"text_markdown":"...","text_source":"ax|ax+ocr|ocr|image-only","read_image":true,"primary_context":"image|text","app":"Safari","title":"...","truncated":false,"summary_line":"appsnap of Safari «title» — 123 chars via AX; read the screenshot for visible content"}
```

`read_image:true` ⇒ AX was thin/absent; the consuming agent must read the screenshot. `text_source:"image-only"` ⇒ no text from AX (and OCR not requested); the screenshot is the only context — this is a valid result, not an error.

## Housekeeping

Captures are saved to `~/Pictures/appsnap/` (override with `APPSNAP_DIR`). The one-shot `appsnap.sh`
prints an in-session reminder when screenshots older than `APPSNAP_RETENTION_DAYS` (default 7) exist, and
`appsnap.sh --clean` deletes them. When you see that reminder, surface it to the user and offer to run
`--clean` — never auto-delete.

## Failure Rules

- Scripts read JSON from stdin and write JSON to stdout.
- Scripts write one-line stderr and exit nonzero on errors.
- If permissions are missing, stop before capture or extraction.
- If both AX and OCR produce no text, report that no text was available and keep the screenshot path as the only usable context.
