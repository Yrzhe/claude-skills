---
name: agentlog
description: Load when the user wants to view, sync, or analyze multi-agent activity across multiple devices — Claude Code / Codex / Cursor / Maestri / browser-use sessions captured to a shared GitHub-synced pool, OR wants a distilled per-project context document so a fresh agent in a different tool can pick up where another left off. Triggers on "agentlog X" commands, "what did I do today across all my agents", "show me my pool", "sync the pool", "拉一下另一台机器上的 agent 记录", "看看 vps 上跑的", "跨设备 agent log", "跨工具上下文", "switch from Codex to Claude Code", "AGENTS.md / CLAUDE.md", "项目状态文档", "agent context". Do NOT load for single-machine tweet material capture (use `seed`) or one-off project planning.
---

# agentlog · Multi-agent, multi-device activity pool + project context layer

agentlog has two layers:

- **Layer 1 — event pool**: captures notable activity from all your AI agents (Claude Code, Codex, Cursor, Maestri, browser-use) across all your machines (Macs + VPS) into one normalized event pool, synced via a private GitHub repo.
- **Layer 2 — project context**: distills the pool into a per-project `AGENTS.md` + `CLAUDE.md` + `docs/agent-context/` snapshot, so any AI coding agent entering the project reads the same up-to-date state, decisions, and next steps.

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

### Distill a project's recent activity into a context document (Layer 2)
```bash
agentlog context init --project-root .
agentlog brief --project agentlog --last 7d
```
Writes `AGENTS.md` + `CLAUDE.md` + `docs/agent-context/{state,decisions,next-steps}.md` so the next agent (Cursor / Codex / Claude Code) entering the project reads a unified state. Requires `ANTHROPIC_API_KEY`.

### Re-sync entry-file blocks after manually editing state
```bash
agentlog context sync
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
| `references/cheatsheet.md` | **Start here** — one-page mental model: commands, capture modes, push rhythm, file layout, schema |
| `references/setup.md` | Full multi-device install, GitHub remote, env vars, daemon install |
| `references/troubleshooting.md` | Common install / sync failures with root-cause + fix (UNKNOWN-0.0.0, command not found, SSH publickey, hostname collision, Cursor adapter blank) |
| `references/cli-reference.md` | Every CLI command with examples |
| `references/cursor-adapter.md` | Cursor IDE SQLite storage layout, action-type mapping, schema-drift handling |
| `references/brief.md` | Haiku distill prompt contract, event selection, idempotency rules |
| `references/context-contract.md` | AGENTS.md + CLAUDE.md double-write, decisions append-only, decision entry format |

For schema details read `src/agentlog/schema.py` directly — the type hints + validate() are the source of truth.

## When extending

- Adding a new source → implement `SourceAdapter` interface (`src/agentlog/adapters/base.py`), register in `_ADAPTER_REGISTRY` in `src/agentlog/cli.py`
- Changing event schema → bump `SCHEMA_VERSION` in `src/agentlog/schema.py` and write a converter
- Adding a CLI command → wire into `build_parser()` in `src/agentlog/cli.py`

## Status

v0 — schema + pool + 5 adapters (claude_code, codex, cursor, maestri, browser_use) + GitHub sync + daemon + shot + recap + Layer 2 (brief + context). Tests: 59 passing.
