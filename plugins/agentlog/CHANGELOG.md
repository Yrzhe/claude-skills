# Changelog

All notable changes to `agentlog` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
