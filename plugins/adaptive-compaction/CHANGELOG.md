# Changelog

All notable changes to the adaptive-compaction skill. Format: [Keep a Changelog](https://keepachangelog.com/).

## [v1.2.0] - 2026-05-20

### Added
- **Skill self-triggers user-facing alerts via the agent.** Per-turn
  `additionalContext` is now tiered: NOOP keeps the quiet status line, but
  ACT_NOW actions (FORCED_COMPACT / FORK_OR_RESET / ASK_USER) now emit an
  explicit agent directive instructing the agent to surface the situation
  to the user in plain language at the start of its next reply, with
  concrete suggested wording (translatable to any language) and the saved
  TASK_STATE path. ATTENTION actions (SAVE_STATE / PREPARE_FOR_COMPACT /
  ZERO_LLM_PRUNE) get a softer "mention if relevant" note. SKILL.md
  Operating Rules gain rule #9: "do not silently swallow non-NOOP signals".

### Net effect
- **Any-condition surfacing is now real**, without an external supervisor.
  When the policy detects relevance drop / topic shift / hard-cap pressure
  / ambiguous decision, the next turn the agent will actively tell the
  user, point to the saved state, and recommend the action. The user still
  presses `/compact` themselves — but they always know exactly when, why,
  and that nothing will be lost. No new process, no IPC, no cross-session
  hazards. Replaces the deferred v1.5 daemon (path B) with a smaller,
  in-hook design.

## [v1.1.0] - 2026-05-20

### Added
- `scripts/analyze_decision_log.py` — utility that reads
  `decision_log.jsonl`, summarizes action distribution + headroom band at
  FORCED_COMPACT events, and recommends an `autoCompactWindow` value that
  aligns the native auto-compact trigger with where the live policy wants
  to compact. Filters out PreCompact-override entries (synthetic
  headroom_frac=0) so the recommendation is based on fresh
  UserPromptSubmit decisions only.

### Fixed
- **PreCompact gate bug (high impact)**: Claude Code's PreCompact event
  does not pass token counts. The pre-existing gate logic would freshly
  score signals from a payload with `tokens_used` defaulting to 0, see
  full headroom, emit NOOP, and block EVERY native compaction attempt.
  Fix: when PreCompact fires without telemetry, replay the last
  UserPromptSubmit decision from `decision_log.jsonl` instead; if no
  prior log entry exists either, default to allow + snapshot (the
  harness triggered this event with its own reason — do not second-guess
  it without data). Manual `/compact` continues to always allow +
  snapshot. Verified against a 5-case test matrix (no-log fallback /
  replay NOOP block / replay FORCED allow / manual allow / fresh
  forced-zone allow).

### Net effect
- For the headroom condition: end-to-end automatic adaptive compaction
  on Claude Code now actually works (gate + snapshot, zero user action
  needed). Non-headroom conditions (relevance / topic / burden while
  the window is not full) still surface a prompt — full any-condition
  auto-execution requires the v1.5 external supervisor.

## [v1.0.2] - 2026-05-20

### Fixed
- Messaging accuracy / consistency with public launch copy:
  - SKILL.md description: "MCP agents" → "MCP-capable hosts" (MCP is a
    protocol, not an agent — factual correction).
  - README: headline no longer calls MCP an agent ("Built for Claude Code,
    with safe degradation on Codex and MCP-only hosts"); "never auto-compact
    mid-task" → "never let a compaction proceed mid-task" (it gates, does not
    self-execute); added explicit "It does not compact for you" note + a
    limitations bullet stating the policy does not initiate a compaction
    itself (gates/snapshots a triggered one; surfaces a prompt otherwise).
  - Synced to plugin copy + installed ~/.claude/skills copy; quick_validate
    PASS. Description change is a 2-token factual fix; pooled trigger re-check
    advisable but low-risk.

## [v1.0.1] - 2026-05-19

### Changed
- Description rewritten to English-only (no Chinese) per user requirement,
  kept under the 1024-char cap (final 989 chars).

### Fixed
- Stabilized trigger-gate measurement: pooled 4 independent 3-run gates
  (12 runs/query) after diagnosing the auto-eval harness as high-variance
  (real `claude` subprocess per run, no per-query timeout; a 7-run attempt
  deadlocked). Stable read: pos 0.778 / neg 1.00 / leaks 0 — SHIPS. The two
  remaining misses (pos-sem-1, pos-imp-3) are the same known semantic limits
  accepted at v1 ship, not a regression.

### Distribution
- Shared into the `yrzhe_skill` Claude Code plugin marketplace as
  `plugins/adaptive-compaction/` (SKILL.md + references + scripts + assets +
  `.claude-plugin/plugin.json` + README + CHANGELOG + LICENSE), registered in
  `.claude-plugin/marketplace.json`. Pre-share security audit: PASS.

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
