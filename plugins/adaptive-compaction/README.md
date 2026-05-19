# adaptive-compaction

An add-on policy & recovery layer that decides **WHEN** a coding agent should
compact, prune, snapshot, or fork — replacing dumb fixed-percent
auto-compaction with an adaptive, signal-driven decision. Built for
**Claude Code**, with safe degradation on Codex and MCP-only hosts (see
capability tiers). No model calls, no network, zero added token cost in the
hot path.

**It does not compact for you.** It scores every turn deterministically and,
at a real compaction boundary, snapshots your state and gates that compaction
(block / allow-with-snapshot). It cannot start a compaction on its own — the
native threshold or you (`/compact`) trigger it; for non-space conditions it
surfaces the call and you act. It decides WHEN; you stay in control.

## Why

Fixed-threshold auto-compaction (e.g. "summarize at 95% of the window") fires
on the wrong signal. Quality degrades from *context rot* well before the
window is full, and a blind summary mid-task drops the exact file paths,
failing test, and accepted plan you were working on. This skill replaces
"compact at N%" with "compact when the evidence says it helps".

## What it decides

Four deterministic signals, scored with no LLM call:

| Signal | Question |
|---|---|
| **Headroom** | How close to the effective window are we? |
| **Relevance** | Does the incoming turn still match the active objective? |
| **Burden** | How many tokens are reclaimable garbage (dup reads, superseded writes, errored inputs)? |
| **Continuity** | Is there an open edit / failing test / unfinished plan that must not be interrupted? |

These map through a canonical decision table to one action:
`NOOP · ZERO_LLM_PRUNE · SAVE_STATE · PREPARE_FOR_COMPACT · FORCED_COMPACT ·
FORK_OR_RESET · ASK_USER`.

Two hard disciplines: never let a compaction proceed mid-task unless at the
hard cap, and on a topic shift prefer `FORK_OR_RESET` over an in-place
destructive summary.

## Host capability tiers

| Tier | Host | What it can enforce |
|---|---|---|
| `hook-rich` | Claude Code | Real PreCompact interception → host-scoped `FORCED_COMPACT` |
| `advise-persist` | Codex | Persist state + shape prompts; forced paths degrade to `PREPARE_FOR_COMPACT` |
| `persist-only` | MCP-only / API | Save / search / state only; no native compaction control claimed |

`FORCED_COMPACT` is emitted **only** on `hook-rich`. Everywhere else it
degrades safely and snapshots first.

## Install

The skill self-installs its hooks. Ask the agent to "install the
adaptive-compaction hooks" — it wires the PreCompact / SessionStart /
UserPromptSubmit hooks (templates in `assets/hooks/`) and can raise
`autoCompactWindow` so the adaptive policy has room to act before the native
threshold fires. See the **Install It Yourself** section in `SKILL.md`.

## Safety

- Non-destructive pruning — every removed blob has a restore pointer (disk
  path + sha256).
- State snapshots run a redaction pass (API keys, tokens, private keys,
  emails) before write.
- No network, no model calls anywhere in v1.

## Limitations (v1)

- Relevance is lexical-only (embeddings deferred to a later version).
- MCP persistence layer deferred to v1.5 (v1 = hooks + local files).
- Native auto-compact threshold is user-configurable on Codex; on Claude Code
  it relies on PreCompact interception.
- The policy does not initiate a compaction by itself. It gates and snapshots
  a compaction the native threshold or the user triggers; for relevance /
  topic / burden conditions while the window is not full, it surfaces a prompt
  and you run `/compact`. Full any-condition auto-execution needs an external
  supervisor (deferred to v1.5).

License: MIT.
