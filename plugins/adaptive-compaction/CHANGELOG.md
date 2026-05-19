# Changelog

All notable changes to the adaptive-compaction skill. Format: [Keep a Changelog](https://keepachangelog.com/).

## [v1] - 2026-05-19

### Added
- **adaptive-compaction skill v1** — add-on policy & recovery layer that
  decides WHEN a coding agent should compact/prune/snapshot/fork, replacing
  fixed-percent auto-compaction.
- Tool-agnostic decision core: `score_signals.py` (deterministic 4-signal
  scorer — headroom/relevance/burden/continuity, lexical relevance, no model
  call), `decide.py` (canonical decision table + `thresholds.json`,
  host-capability-aware downgrade).
- Zero-LLM pruning `prune_zero_llm.py` (dedup / supersede / error-purge /
  quarantine — non-destructive, restore pointers).
- Recovery: `state_packet.py` (operational TASK_STATE schema + secret
  redaction), `decision_log.py` (append-only JSONL for Q6 metrics).
- `hook_bridge.py` + Claude Code hooks (PreCompact block/allow snapshot-first
  = v1 host-scoped FORCED_COMPACT; SessionStart; UserPromptSubmit) + Codex
  hooks.json/config.toml at advise/persist level.
- References: contract, decision-policy, capability-matrix, eval-protocol,
  risk-acceptance-tests. SKILL.md navigator (231 lines) incl. "Coexisting
  With Native Auto-Compaction".
- Backed by 3 independent deep-research passes + 3-role Codex design review
  (docs/architecture/00-DESIGN.md is the canonical spec).

### Changed
- USER OVERRIDE of the conservative reconciliation: v1 auto-triggers native
  compaction, host-scoped (Claude Code real PreCompact interception;
  Codex/MCP-only degrade to advise/persist). No universal claim.
- MCP persistence deferred to v1.5 (v1 = hooks + local files).

### Known limitations
- Trigger eval: pos 78% / neg 100% / leaks 0 — SHIPS (concrete gate ≥70%).
  Two positives miss (pos-sem-1 "context rot" semantic; pos-imp-3 "forgetting
  the plan, add something on top") — flagged for a future skill-improve cycle.
- Native auto-compact threshold is not user-configurable on Claude Code
  (relies on PreCompact interception); configurable on Codex.
- Relevance is lexical-only in v1 (embeddings = v3, after Q6 trace corpus).
