---
name: agentlog
description: Load when the user wants to view, sync, or analyze multi-agent activity across multiple devices — Claude Code / Codex / Maestri / browser-use sessions captured to a shared GitHub-synced pool. Triggers on "agentlog X" commands, "what did I do today across all my agents", "show me my pool", "sync the pool", "拉一下另一台机器上的 agent 记录", "看看 vps 上跑的", "跨设备 agent log". Do NOT load for single-machine tweet material capture (use `seed`) or one-off project planning.
---

# agentlog · Multi-agent, multi-device activity pool

agentlog captures notable activity from all your AI agents (Claude Code, Codex, Maestri canvas, browser-use, etc.) across all your machines (Macs + VPS) into one normalized event pool, synced via a private GitHub repo. It's the **"one person, many agents"** version of team activity dashboards.

## Boundaries (when NOT to use)

| Task | Use this instead |
|---|---|
| Capture a single Claude Code session for tweet drafting | `seed` skill |
| One-off project planning / brainstorming | `planner` / `brainstorming` |
| Team collaboration / sharing with others | (not supported in v0) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Device A (Mac)              Device B (VPS)                  │
│  ─────────────────           ─────────────────              │
│  Claude Code                 Claude Code                     │
│  Codex                       Codex                           │
│  Maestri canvas              (scripts)                       │
│  browser-use                                                 │
│       ↓                            ↓                          │
│  agentlog adapters           agentlog adapters               │
│       ↓                            ↓                          │
│  ~/.agent-seeds/             ~/.agent-seeds/                 │
│  (local pool clone)          (local pool clone)              │
│       ↓                            ↓                          │
│        └──── GitHub (private repo) ────┘                     │
└─────────────────────────────────────────────────────────────┘
```

Each agent → adapter → local pool shard → GitHub. Other devices pull. Everyone sees a unified feed.

## Setup

Detailed: `references/setup.md`. Quick version:

```bash
gh repo create agent-seeds --private --confirm
agentlog init --repo git@github.com:YOUR_USER/agent-seeds.git
agentlog poll --once --source claude_code   # smoke test
```

On each additional device: same `agentlog init` command. Pool syncs via GitHub.

## Common flows

### See what I did across all agents today
```bash
agentlog recap
```

### Live feed of last 4 hours, all sources
```bash
agentlog pool --last 4h
```

### Group view by project / agent / source
```bash
agentlog pool --by project
agentlog recap --by agent
```

### Pull everything from other machines now
```bash
agentlog pull
```

### Push current local changes immediately
```bash
agentlog push --force
```

### Manually log an event from a script
```bash
agentlog event push '{"action":{"type":"checkpoint","status":"completed","label":"deploy success"},"summary":"shipped api v2"}'
```

### Migrate historical seed data (one-time)
```bash
agentlog migrate-from-seed --dry-run
agentlog migrate-from-seed
```

### Run the background daemon (auto poll + sync)
```bash
agentlog daemon install   # macOS launchd or Linux systemd
agentlog daemon start
```

## Reference index

| File | Covers |
|---|---|
| `references/setup.md` | Full multi-device install, GitHub PAT vs ssh, repo permissions |
| `references/schema-v0.md` | Event schema fields, validation rules, examples |
| `references/cli-reference.md` | Every CLI flag with examples |
| `references/adapters/claude-code.md` | ClaudeCodeAdapter config + extension hooks |
| `references/adapters/codex.md` | CodexAdapter config + backfill |
| `references/adapters/maestri.md` | MaestriAdapter polling tuning |
| `references/adapters/browser-use.md` | BrowserUseAdapter session config |
| `references/troubleshooting.md` | Git sync conflicts, corrupted cursors, adapter failures |
| `references/upgrade-from-seed.md` | How agentlog and seed coexist; migration details |
| `docs/design/03-spec-v0.5-merged.md` | Authoritative v0.5 spec (read first if extending) |

## When extending

- Adding a new source → implement `SourceAdapter` interface (`src/agentlog/adapters/base.py`), register in CLI
- Changing event schema → bump `schema_version`, write a converter in `src/agentlog/migrations/`
- Adding a CLI command → see `src/agentlog/cli.py`

The full design rationale (why GitHub sync, why per-device sharding, why two-layer dedupe) lives in `docs/design/`. Read those before non-trivial changes.

## Status

v0 — implementation in progress. Functional smoke test target: end-to-end Claude Code → pool → recap on a single Mac. Subsequent: Codex adapter, multi-device, Maestri adapter, BrowserUse adapter.
