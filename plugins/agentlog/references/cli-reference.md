# agentlog · CLI reference

Every command, with the flags that exist today.

## Setup / state

### `agentlog init [--repo URL]`
Initialize the local pool. If `--repo` is given, clones it; otherwise creates an empty local-only pool. Generates a per-device `device_id`.

### `agentlog status`
Prints pool root, device id, git remote, cursor files, quarantine size. Use this when something feels off.

### `agentlog config set remote <URL>`
Set or change the git remote. Useful if you initialized without `--repo`.

## Capturing

### `agentlog poll --source <name> [--once]`
Runs one or more adapter poll cycles. `--once` (recommended for ad-hoc use) returns immediately. Available sources:

| Source | What it reads |
|---|---|
| `claude_code` | `~/.claude/projects/*/*.jsonl` (live Claude Code sessions) |
| `codex` | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` |
| `maestri` | Maestri canvas state via `maestri list` / `maestri check` / `maestri note read` |
| `browser_use` | Local dump at `~/.agentlog/browser_use_sessions.jsonl` |

### `agentlog shot [TARGET] [--note TEXT]`
Capture a screenshot and emit a `checkpoint` event with an embedded artifact ref.

- `agentlog shot` → interactive window pick (`screencapture -w`, macOS)
- `agentlog shot https://example.com` → headless Chrome screenshot
- `agentlog shot localhost:3000` → normalized to `http://localhost:3000`

Flags: `--note`, `--width`, `--height`, `--session-id`, `--project`, `--flush`.

### `agentlog event push '<JSON>' [--flush]`
Manually push a hand-built event from a script. Defaults are filled in so you can pass a minimal stub:

```bash
agentlog event push '{
  "action": {"type": "checkpoint", "status": "completed", "label": "release"},
  "summary": "shipped api v2.1",
  "project": {"name": "api"}
}'
```

### `agentlog backfill --source <name> [--from YYYY-MM-DD]`
Re-scan an adapter's full history (CodexAdapter ignores archive dirs by default; use this to grab them).

### `agentlog migrate-from-seed [--dry-run] [--seed-dir PATH]`
One-time importer for `~/.claude/skills/seed/state/sessions/*.md` (existing seed users only).

## Reading

### `agentlog pool [--last 4h] [--source X] [--project Y] [--by source|project|agent|device] [--limit 50]`
List events. `--last 4h|2d|30m|1w` filters by recency. `--by` switches to grouped output.

### `agentlog recap [--date YYYY-MM-DD] [--by source|project|agent|device]`
Per-day markdown summary, intended as input to a downstream LLM. Date defaults to today (UTC).

## Sync

### `agentlog sync`
`pull` then `push`. Most common command.

### `agentlog pull`
Fetch + rebase remote on local. Safe even if nothing changed.

### `agentlog push [--force]`
Commit local pool changes and push. `--force` bypasses the 30s push debounce.

## Daemon

### `agentlog daemon [--once] [--sources X,Y] [--poll-interval 30] [--sync-interval 300]`
Foreground loop. Polls all sources every `poll-interval`, syncs every `sync-interval`.

### `agentlog daemon install --type launchd|systemd [--bin PATH]`
Prints the unit/plist to stdout. Pipe to the right path, then load it (see `references/setup.md`).

## Quick mental model

- **append once**: `agentlog poll --once --source claude_code` (one shot)
- **append continuously**: `agentlog daemon` (background loop)
- **read**: `agentlog pool --last 4h` (flat) or `agentlog recap` (grouped)
- **share**: `agentlog sync` (pull + push)
