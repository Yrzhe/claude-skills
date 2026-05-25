#!/usr/bin/env bash
# appsnap — one-shot: pick (or frontmost) a Mac window, capture screenshot +
# Accessibility text, assemble the bundle, print it. The screenshot is the
# primary context; the consuming agent reads it. Local OCR is opt-in (--ocr).
#
# Usage:
#   ./appsnap.sh                 # auto: hover-pick, full-page if AX says scrollable, otherwise visible capture
#   ./appsnap.sh --visible       # hover-pick single visible screenshot, never scroll
#   ./appsnap.sh --pick          # GUI list picker instead of hover
#   ./appsnap.sh --frontmost     # grab the frontmost window (no interaction)
#   ./appsnap.sh --fullpage      # ACTIVE: pick a scrollable window, scroll+stitch into one tall PNG
#   ./appsnap.sh --ocr           # also run local macOS OCR (for non-vision use)
#   ./appsnap.sh --open          # open the screenshot when done
#   ./appsnap.sh --json          # print only the raw bundle JSON
#   ./appsnap.sh --clean         # delete captures older than APPSNAP_RETENTION_DAYS (default 7) and exit
set -euo pipefail

DIR="${APPSNAP_DIR:-$HOME/Pictures/appsnap}"
RETENTION_DAYS="${APPSNAP_RETENTION_DAYS:-7}"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$SKILL_DIR/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "appsnap: venv not found. One-time setup:" >&2
  echo "  python3 -m venv \"$SKILL_DIR/.venv\"" >&2
  echo "  \"$SKILL_DIR/.venv/bin/pip\" install -r \"$SKILL_DIR/requirements.txt\"" >&2
  exit 1
fi

MODE="auto"; OCR="false"; OPEN="false"; JSON_ONLY="false"; CLEAN="false"
for arg in "$@"; do
  case "$arg" in
    --visible) MODE="visible" ;;
    --pick) MODE="pick" ;;
    --frontmost) MODE="frontmost" ;;
    --fullpage) MODE="fullpage" ;;
    --ocr) OCR="true" ;;
    --open) OPEN="true" ;;
    --json) JSON_ONLY="true" ;;
    --clean) CLEAN="true" ;;
    *) echo "appsnap: unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# --clean: delete old captures and exit (no capture).
if [[ "$CLEAN" == "true" ]]; then
  if [[ -d "$DIR" ]]; then
    n=$(find "$DIR" -type f -name '*.png' -mtime +"$RETENTION_DAYS" 2>/dev/null | wc -l | tr -d ' ')
    find "$DIR" -type f -name '*.png' -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
    echo "appsnap: removed $n screenshot(s) older than $RETENTION_DAYS days from $DIR"
  else
    echo "appsnap: no capture dir yet ($DIR)"
  fi
  exit 0
fi

# Permission preflight (exits nonzero with one-line guidance if missing).
"$PY" "$SKILL_DIR/scripts/check_permissions.py" >/dev/null

SKILL_DIR="$SKILL_DIR" MODE="$MODE" OCR="$OCR" OPEN="$OPEN" JSON_ONLY="$JSON_ONLY" "$PY" - <<'PY'
import json, os, subprocess, sys

skill = os.environ["SKILL_DIR"]
py = sys.executable
sc = os.path.join(skill, "scripts")

def run(script, payload):
    p = subprocess.run([py, os.path.join(sc, script)],
                       input=json.dumps(payload), text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(f"appsnap: {script} failed: {(p.stderr or '').strip()[:200]}\n")
        sys.exit(p.returncode)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        sys.stderr.write(f"appsnap: {script} returned non-JSON output\n")
        sys.exit(1)

cap = run("capture.py", {"mode": os.environ["MODE"]})
# In hover mode the window identity is best-effort; skip AX if it's unknown.
if cap.get("pid"):
    ax = run("ax_extract.py", {"pid": cap["pid"], "windowid": cap["windowid"]})
else:
    ax = None
asm_in = {"capture": cap, "ax": ax, "ocr": None}
if os.environ["OCR"] == "true":
    asm_in["ocr_requested"] = True
bundle = run("assemble.py", asm_in)

if os.environ["JSON_ONLY"] == "true":
    print(json.dumps(bundle, ensure_ascii=False))
    sys.exit(0)

print("─" * 70)
print(bundle["summary_line"])
paths = bundle.get("image_paths") or [bundle["image_path"]]
print("screenshots:")
for path in paths:
    print(f"  - {path}")
print(f"text_source: {bundle['text_source']}   read_image: {bundle['read_image']}   primary: {bundle['primary_context']}")
print("─" * 70)
text = bundle.get("text_markdown") or "(no AX text — read the screenshot)"
print(text if len(text) <= 4000 else text[:4000] + f"\n… (+{len(text)-4000} more chars)")
print("─" * 70)
if bundle["read_image"]:
    print("NOTE: AX text is thin/absent — open the screenshot above and read it for the visible content.")

if os.environ["OPEN"] == "true":
    for path in paths:
        subprocess.run(["open", path], check=False)
PY

# In-session retention reminder (no cron; never auto-deletes).
if [[ "$JSON_ONLY" != "true" && -d "$DIR" ]]; then
  old=$(find "$DIR" -type f -name '*.png' -mtime +"$RETENTION_DAYS" 2>/dev/null | wc -l | tr -d ' ')
  if [[ "${old:-0}" -gt 0 ]]; then
    sz=$(find "$DIR" -type f -name '*.png' -mtime +"$RETENTION_DAYS" -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)
    echo "💡 ${old} screenshot(s) older than ${RETENTION_DAYS} days (${sz:-?}) in ${DIR} — run 'appsnap.sh --clean' to delete them."
  fi
fi
