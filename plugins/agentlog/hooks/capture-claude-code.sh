#!/usr/bin/env bash
# Claude Code Stop hook → agentlog per-session capture.
#
# Install:
#   1. cp this file to ~/.claude/hooks/agentlog-stop.sh
#   2. chmod +x ~/.claude/hooks/agentlog-stop.sh
#   3. In ~/.claude/settings.json, add to the Stop hook list:
#        { "hooks": [{ "command": "bash ~/.claude/hooks/agentlog-stop.sh", "type": "command" }], "matcher": "" }
#
# What it does:
#   Claude Code pipes a JSON payload describing the just-finished turn on stdin.
#   We forward it to `agentlog hook stop`, which captures the new events from
#   that single transcript file into the pool. Much faster than a full poll.
#
# We always exit 0: never block Claude Code's exit on agentlog problems.

set +e

# Locate agentlog. Prefer the venv install, fall back to PATH.
AGENTLOG_BIN=""
for candidate in \
  "$HOME/.virtualenvs/agentlog/bin/agentlog" \
  "$(command -v agentlog 2>/dev/null)"
do
  if [ -x "$candidate" ]; then
    AGENTLOG_BIN="$candidate"
    break
  fi
done

if [ -z "$AGENTLOG_BIN" ]; then
  exit 0
fi

# Run synchronously so stdin (the Stop-hook JSON payload) is read in full.
# Swallow output so it doesn't appear in the user-visible status line. Per-
# session capture is one file read + a few pool appends — fast enough to not
# block the user's prompt.
"$AGENTLOG_BIN" hook stop --quiet >/dev/null 2>&1

# Always exit 0: never block Claude Code on agentlog problems.
exit 0
