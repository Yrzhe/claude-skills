# agentlog · Cheatsheet

One-page mental model. Bookmark this; everything else in `references/` is detail.

## What it does in one sentence

Captures activity from every AI agent you run, across every machine, into one event pool synced through your own private GitHub repo.

## The three layers

```
agents (Claude Code, Codex, Maestri, browser-use, …)
   │
   ▼
adapters (SourceAdapter subclasses)         ← capture
   │
   ▼
~/.agent-seeds/                              ← local pool clone
pool/dt=YYYY-MM-DD/device=<id>/source=<src>/shard-NNN.jsonl
   │
   ▼ git pull --rebase / push (debounced)
github.com/YOU/agent-seeds (private repo)    ← sync hub
```

Each device runs its own adapters writing to its own shard paths. Cross-device pushes never collide because every path is uniquely owned. `merge=union` resolves the rare rebase conflict by concatenating.

## All commands at a glance

| Goal | Command |
|---|---|
| Install on a new machine | `agentlog init --repo git@github.com:YOU/agent-seeds.git` |
| See what's in the pool | `agentlog pool --last 4h` |
| Group view | `agentlog pool --by source` / `--by project` / `--by agent` / `--by device` |
| Day recap (markdown) | `agentlog recap` |
| Capture screenshot + log it | `agentlog shot <url>` or `agentlog shot` (interactive) |
| Manually emit one event | `agentlog event push '<json>'` |
| One-shot poll for testing | `agentlog poll --once --source claude_code` |
| Pull others' work | `agentlog pull` |
| Push my work now | `agentlog push --force` |
| Pull then push | `agentlog sync` |
| Status check | `agentlog status` |
| Import historic seed data | `agentlog migrate-from-seed` |
| Backfill an adapter's archive | `agentlog backfill --source codex` |
| Show daemon plist / unit | `agentlog daemon install --type launchd \| systemd` |
| Run daemon in foreground | `agentlog daemon` (Ctrl-C to stop) |
| Single iteration through daemon loop | `agentlog daemon --once` |
| Stop hook entry (Claude Code feeds stdin) | `agentlog hook stop --quiet` |

Adapters that ship today: `claude_code`, `codex`, `maestri`, `browser_use`. Adding more is a `SourceAdapter` subclass plus one line in `_ADAPTER_REGISTRY` in `cli.py`.

## Three capture modes — pick at least one

| Mode | Cadence | Latency | What it covers | When to use |
|---|---|---|---|---|
| `agentlog poll --once` | manual | seconds–minutes | any adapter | smoke test, ad-hoc |
| `agentlog daemon` (launchd/systemd) | every 30s poll, every 5min sync | up to 30s | every registered adapter | hands-off background; the default for steady-state use |
| Claude Code Stop hook | every assistant turn | ~150ms warm | only `claude_code` | near-real-time for Claude conversations specifically |

Stop hook and daemon complement each other. Hook gives instant capture for Claude Code; daemon picks up everything else (Codex sessions, Maestri canvas state, browser-use dumps) on its 30s cycle.

## When does it actually push to GitHub?

Pool commits are batched, not per-event:

| Trigger | Source |
|---|---|
| Accumulated ≥ 50 events OR ≥ 1 MB since last commit | daemon, `agentlog push` |
| 30s debounce since last push attempt | both |
| `agentlog push --force` | manual override |
| `agentlog sync` (pull → push) | manual or daemon's 5-min cycle |

So even with the Stop hook firing 100× during a long conversation, GitHub typically sees a handful of commits, not 100. If you switch machines and want the latest now, `agentlog pull` on the second machine.

## Install the recommended auto-mode (macOS)

```bash
# 1. Stop hook
cp <agentlog-dir>/hooks/capture-claude-code.sh ~/.claude/hooks/agentlog-stop.sh
chmod +x ~/.claude/hooks/agentlog-stop.sh
# Add to ~/.claude/settings.json under "Stop":
#   { "hooks": [{ "command": "bash ~/.claude/hooks/agentlog-stop.sh", "type": "command" }], "matcher": "" }

# 2. Daemon (launchd)
agentlog daemon install --type launchd --bin "$(which agentlog)" \
  > ~/Library/LaunchAgents/ai.agentlog.daemon.plist
launchctl load ~/Library/LaunchAgents/ai.agentlog.daemon.plist

# 3. Verify
launchctl list | grep agentlog       # PID printed = running
tail -f ~/.agent-seeds/state/daemon.log
```

systemd flow on Linux is the same shape: `agentlog daemon install --type systemd > ~/.config/systemd/user/agentlog.service` then `systemctl --user enable --now agentlog`.

## File layout you should know

```
~/.agent-seeds/                              ← your private pool clone
├── pool/                                    ← shards, append-only, git-tracked
├── artifacts/screenshots/YYYY-MM-DD/        ← agentlog shot outputs, git-tracked
├── sessions/                                ← reserved (future derived md)
├── indexes/                                 ← reserved (future recap cache)
├── state/                                   ← LOCAL ONLY (gitignored)
│   ├── cursors/<source>.json                ← adapter progress tracker
│   ├── devices/<id>.json                    ← per-device record
│   ├── this-device.json                     ← this machine's identity
│   ├── quarantine/*.jsonl                   ← failed-validation events
│   ├── sync.lock                            ← fcntl lock during sync
│   └── daemon.log                           ← launchd/systemd stdout+stderr
└── .gitattributes                           ← pool/**/*.jsonl merge=union
```

Things you should never hand-edit: anything under `pool/` or `state/cursors/`. Both are mechanical state and editing them risks de-syncing devices.

## EventV0 schema (one JSON line per event)

| Field | Purpose |
|---|---|
| `schema_version` | always `agentlog.event.v0` |
| `id` | UUIDv7, locally unique |
| `source_event_id` | adapter-assigned; first-line dedupe |
| `dedupe_key` | sha256 fallback; second-line dedupe |
| `timestamp` / `ingested_at` | when the source event happened / when we saw it |
| `actor` | `{id, name, kind: human/agent/system}` |
| `source_type` | `claude_code` / `codex` / `maestri` / `browser_use` / `manual` |
| `source.{device_id, host, process_id, session_id}` | provenance |
| `project.{name, path}` | where the work happened |
| `action.{type, status, label}` | 14 enum types: tool_call, agent_response, file_changed, … |
| `summary` | ≤ 240 chars, single line |
| `payload` | adapter-specific structured data |
| `artifact_refs[]` | `{kind, uri, sha256, bytes, mime_type}` for files / screenshots / urls |

Authoritative spec lives in `src/agentlog/schema.py` — `validate()` is the source of truth, not this table.

## Troubleshooting

| Symptom | First check |
|---|---|
| `agentlog pool` shows nothing recent | `launchctl list \| grep agentlog` (daemon running?) + `tail ~/.agent-seeds/state/daemon.log` (errors?) |
| GitHub push rejected | `agentlog pull` then `agentlog push` |
| Hook silently does nothing | `bash ~/.claude/hooks/agentlog-stop.sh < /dev/null` (must exit 0); `which agentlog` (resolvable from hook env?) |
| New device, no events showing | `agentlog status` — is the right pool URL on the right device id? |
| `quarantine/` has files | one or more events failed validation; read the file, the rejection reason is on each line |

## What it is NOT (so future-you doesn't get confused)

- Not a team product. Each user runs their own pool repo with their own ACL.
- Not a SaaS. There is no `agentlog.io`. Your data sits in your GitHub.
- Not a replacement for the `seed` skill (which still works for single-machine tweet-material capture). Both coexist.
- Not an auto-discoverer. Each device needs `agentlog init --repo <URL>` once. The skill doesn't know which pool repo to use until you tell that machine.
