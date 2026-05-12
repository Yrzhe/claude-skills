# agentlog

A multi-agent, multi-device activity pool for solo AI power users.

You run agents across several Claude Code windows, a few Codex CLIs, a Maestri canvas, and maybe a VPS. **agentlog** captures notable activity from all of them, normalizes it to one schema, and syncs it through a private GitHub repo so every device sees the same pool.

## What it does

- Captures events from `Claude Code`, `Codex`, `Maestri`, `browser-use` (extensible)
- Stores in a private GitHub repo you own (`~/.agent-seeds/`)
- Provides a unified `agentlog pool` / `agentlog recap` view across all sources
- Designed for **one person, many agents, many machines** — not team collaboration (yet)

## Quick start

```bash
# 1. Create your private pool repo (one time, anywhere)
gh repo create agent-seeds --private --confirm

# 2. Initialize on each device
agentlog init --repo git@github.com:YOUR_USER/agent-seeds.git

# 3. Run one poll cycle (smoke test)
agentlog poll --once --source claude_code

# 4. See what's in the pool
agentlog pool --last 4h

# 5. Cross-source day recap
agentlog recap
```

## What it is NOT

- Not a replacement for Claude Code's `seed` skill (single-machine tweet capture). Both coexist.
- Not a team product. Each user has their own pool repo.
- Not a logging service. Self-hosted via GitHub.

## Design

See `docs/design/` for the merged v0.5 spec. Key separations:

- **This repo** = the open-source skill template (you install it)
- **`~/.agent-seeds/`** = your private GitHub repo with your data (you create it)

The two never nest.

## Status

v0 in design. Pool storage + adapter schema designs are done. Implementation in progress.
