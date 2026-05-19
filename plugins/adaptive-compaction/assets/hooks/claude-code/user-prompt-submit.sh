#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="${ADAPTIVE_COMPACTION_SKILL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
exec python3 "$SKILL_DIR/scripts/hook_bridge.py" claude-user-prompt-submit
