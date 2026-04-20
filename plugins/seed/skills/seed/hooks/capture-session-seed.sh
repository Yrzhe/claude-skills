#!/bin/bash
# Claude Code Stop Hook: append the current turn to a per-session seed log.
# No scoring, no judgment — pure mechanical record. Synthesis happens later
# when the user invokes /seed (the skill reads the file and helps synthesize).

SEED_DIR="$HOME/.claude/skills/seed/state/sessions"
EXTRACTOR="$HOME/.claude/skills/seed/scripts/extract_turn.py"

mkdir -p "$SEED_DIR"

# Stop hooks receive a JSON payload on stdin. Parse with python for safety.
INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

PARSED=$(
  printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
sid = d.get("session_id", "") or ""
tp  = d.get("transcript_path", "") or ""
cwd = d.get("cwd", "") or ""
print(sid)
print(tp)
print(cwd)
' 2>/dev/null
)

SESSION_ID=$(printf '%s\n' "$PARSED" | sed -n '1p')
TRANSCRIPT_PATH=$(printf '%s\n' "$PARSED" | sed -n '2p')
CWD=$(printf '%s\n' "$PARSED" | sed -n '3p')

[ -z "$SESSION_ID" ] && exit 0
[ -z "$TRANSCRIPT_PATH" ] && exit 0
[ ! -f "$TRANSCRIPT_PATH" ] && exit 0
[ ! -f "$EXTRACTOR" ] && exit 0

SESSION_FILE="$SEED_DIR/${SESSION_ID}.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

python3 "$EXTRACTOR" \
  --transcript "$TRANSCRIPT_PATH" \
  --session-id "$SESSION_ID" \
  --timestamp "$TIMESTAMP" \
  --cwd "$CWD" \
  --session-file "$SESSION_FILE" \
  >/dev/null 2>&1 || true

exit 0
