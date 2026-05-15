# Changelog

All notable changes to `agentlog` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `src/agentlog/__main__.py` so `python3 -m agentlog ...` works as a fallback when the entry point script isn't on PATH.
- `references/troubleshooting.md` — root-cause + fix for the four most common install failures surfaced during a real second-device (Ubuntu VPS) install: setuptools-too-old `UNKNOWN-0.0.0`, command-not-found on `~/.local/bin`, SSH publickey missing, and cross-device hostname collision.

### Changed
- `README.md` quick start: split install into two paths (pipx for end users, editable pip for hackers); added explicit `setuptools` upgrade prerequisite, `ssh -T git@github.com` verification step before `init`, and `agentlog --help` smoke step.
- `references/setup.md`: same structure (Options A/B/C), called out the `AGENTLOG_DEVICE_ID` cross-device collision risk explicitly with a fix block, added §2.5 (SSH verification) and §3.5 (set device_id per shell rc).
- `SKILL.md` reference index now points to `troubleshooting.md`.

## [0.11.0] — 2026-05-13

### Added
- **Cursor IDE adapter** (`agentlog poll --source cursor`) — reads chat
  history from per-workspace `state.vscdb` SQLite stores; tolerates Cursor
  schema drift with warning-and-skip rather than crashing.
- **Layer 2 — project context** distillation:
  - `agentlog brief --project <name> [--last 7d]` — distills recent pool
    events for one project into `docs/agent-context/{state,decisions,
    next-steps}.md` via Haiku 4.5.
  - `agentlog context init` — scaffolds AGENTS.md + CLAUDE.md +
    `docs/agent-context/` skeleton for a project.
  - `agentlog context sync` — re-syncs the managed state block in
    AGENTS.md + CLAUDE.md from `docs/agent-context/`.
- Schema: `cursor` source_type, `decision` and `next_step` action types
  (backward-compatible — payload is unchanged).
- References: `cursor-adapter.md`, `brief.md`, `context-contract.md`.

### Changed
- SKILL.md restructured to call out Layer 1 (event pool) and Layer 2
  (project context) explicitly; trigger phrases now include cross-tool
  context handoff scenarios.
- Test suite: 39 → 59 (Cursor adapter 5, context 7, brief 5, schema +3).
