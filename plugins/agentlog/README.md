# agentlog

A **multi-agent, multi-device activity pool** for solo AI power users.

You run agents across several Claude Code windows, a few Codex CLIs, a Maestri canvas, and maybe a VPS. `agentlog` captures notable activity from all of them, normalizes it to one schema, and syncs through a private GitHub repo so every device sees the same pool. Designed for **one person, many agents, many machines** — not team collaboration.

> Built by **[@yrzhe_top](https://x.com/yrzhe_top)** ([Yrzhe](https://github.com/Yrzhe)).
> If `agentlog` saved you from re-explaining context to yet another agent, a follow on X is the only ad I'll put here. The skill stays open-source either way.

## What it does

- Captures events from **Claude Code**, **Codex**, **Maestri**, **browser-use** out of the box; pluggable via a `SourceAdapter` ABC
- Normalizes everything to one **EventV0** schema (single line of JSON, validated, dedup-keyed)
- Stores in a private GitHub repo **you own** at `~/.agent-seeds/`
- Provides a unified `agentlog pool` / `agentlog recap` view across all sources + devices
- Optional Claude Code **Stop hook** for near-real-time capture (~150ms warm)
- Optional **daemon** (launchd / systemd) for fully hands-off background sync

## Why it exists

The default model of every AI tool is "this conversation lives in this app." When you run 4 Claude Code windows + 2 Codex CLIs across two machines for two weeks, that becomes "where did I do the X thing again?" `agentlog` is the boring infrastructure answer: every agent dumps events into one pool, you query the pool.

## Quick start

```bash
# Get the source
git clone https://github.com/Yrzhe/claude-skills.git ~/code/claude-skills

# Install — option A: pipx (recommended for end users, isolates dependencies)
pipx install ~/code/claude-skills/plugins/agentlog

# Install — option B: editable pip (for hacking the skill)
pip install --upgrade pip setuptools wheel   # required: system setuptools is often <61
pip install -e ~/code/claude-skills/plugins/agentlog

# Verify install (you should see the subcommand list)
agentlog --help | head -5
# If `agentlog` isn't found but the install succeeded, also try: python3 -m agentlog --help

# Create your private pool repo (one time, anywhere)
gh repo create agent-seeds --private --confirm

# Verify GitHub SSH access before init (the next step clones via SSH)
ssh -T git@github.com   # expect: "Hi <user>! You've successfully authenticated..."

# Initialize on each device (run on every machine you want to capture from)
agentlog init --repo git@github.com:YOUR_USER/agent-seeds.git

# Smoke test
agentlog poll --once --source claude_code
agentlog pool --last 4h
agentlog recap
```

Full setup, daemon install, Stop hook install: see [`references/setup.md`](references/setup.md). Every command flag with examples: [`references/cli-reference.md`](references/cli-reference.md). Common install / sync failures and fixes: [`references/troubleshooting.md`](references/troubleshooting.md).

## What it is NOT

- Not a replacement for the `seed` skill (single-machine tweet capture). They coexist; their hooks can both be installed.
- Not a team product. Each user has their own pool repo with their own access control.
- Not a hosted service. Self-hosted via GitHub. Your data, your repo, your bandwidth.

## Architecture, briefly

```
agents ─► adapter ─► local pool clone ──┐
                    (~/.agent-seeds/)   │
                                        ▼
                              GitHub (private repo)
                                        ▲
agents ─► adapter ─► local pool clone ──┘
                    (~/.agent-seeds/)
```

- Per-device sharded JSONL paths (`pool/dt=YYYY-MM-DD/device=<id>/source=<src>/shard-NNN.jsonl`) → cross-device writes never collide
- `merge=union` git driver concatenates if conflicts happen during rebase
- Two-layer dedupe: deterministic `source_event_id` (adapter assigns) + sha256 `dedupe_key` (pool fallback)
- Sync: 30s push debounce, batched 50-events / 1MB, pull-before-push with rebase

## Status

**v0 feature-complete** as of 2026-05-13. Schema + pool + 4 adapters (claude_code, codex, maestri, browser_use) + GitHub sync + daemon + screenshot capture + Stop hook + recap + 39/39 tests passing.

## Extending

- New adapter: subclass `SourceAdapter` (`src/agentlog/adapters/base.py`), register in `_ADAPTER_REGISTRY` (`src/agentlog/cli.py`)
- New CLI command: wire into `build_parser()` in `src/agentlog/cli.py`
- Schema change: bump `SCHEMA_VERSION` in `src/agentlog/schema.py` and ship a converter

## License

MIT.
