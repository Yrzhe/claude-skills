# Decision Policy

V1 is an adaptive compaction policy and recovery layer. It scores four signals, emits one action, persists state before risky transitions, and only enforces native compaction where the host exposes a real hook surface.

## Four Signals

| Signal | Meaning | Use |
|---|---|---|
| Headroom | Free usable context after reserved output budget | Urgency signal. Forces action only near hard cap. |
| Relevance | Lexical plus structural overlap between the incoming prompt and objective, hot files, symbols, and plan | Topic-shift signal. Low relevance prefers fork/reset, not in-place compaction. |
| Burden | Reclaimable stale context: duplicate reads, superseded writes, stale errored inputs, oversized outputs | Cleanup signal. Runs zero-LLM pruning before summaries. |
| Continuity | Active task value: edits, failing tests, unresolved errors, uncheckpointed plan | Safety signal. Blocks mid-task compaction unless hard cap. |

## Defaults

| Key | Default |
|---|---:|
| `healthy_headroom_min` | `0.40` |
| `soft_headroom_low` | `0.20` |
| `forced_headroom_floor` | `0.175` |
| `hard_cap_floor` | `0.125` |
| `thrash_cooldown_turns` | `6` |
| `min_recovery_ratio` | `0.20` |
| `zero_llm_success_ratio` | `0.60` |
| `topic_shift_confirmation_turns` | `2` |
| `large_output_quarantine_tokens` | `5000` |
| `error_input_purge_turns` | `4` |

These are trace-tunable defaults, not universal constants.

## Canonical Table

| Headroom | Relevance | Burden | Continuity | Action |
|---|---|---|---|---|
| Healthy | High | Low | Any | `NOOP` |
| Healthy | High | High | Low/Medium | `ZERO_LLM_PRUNE` |
| Healthy | Low topic shift | Any | Low | `FORK_OR_RESET` |
| Healthy | Low | Any | High | `ASK_USER` |
| Soft | High | High | Low | `ZERO_LLM_PRUNE`; compact only at boundary |
| Soft | Low topic shift | Any | Low/Medium | `FORK_OR_RESET` |
| Forced | High | Any | Low | `FORCED_COMPACT` only on `hook-rich`; otherwise `PREPARE_FOR_COMPACT` |
| Forced | Any | Any | High | `SAVE_STATE` unless hard cap |
| Hard cap | Any | Any | Any | Snapshot, then `FORCED_COMPACT` on `hook-rich`; otherwise `PREPARE_FOR_COMPACT` |
| Recent compact | Any | Any | Any | Thrash guard: `NOOP`, `ZERO_LLM_PRUNE`, or `SAVE_STATE` |

## Hard Disciplines

1. Never auto-compact mid-task unless hard cap. Continuity flags force `SAVE_STATE`, `NOOP`, or `ZERO_LLM_PRUNE` before hard cap.
2. Topic shift with healthy headroom prefers `FORK_OR_RESET`, not in-place compact.

## Locked Q Decisions

- Q2: Fork/reset by default on topic shift plus healthy headroom. Cutoff is two low-relevance turns or one explicit new-task marker with more than 25-30% free headroom. Low relevance plus high continuity asks the user.
- Q3: MVP relevance is deterministic lexical plus structural overlap. No model calls. SBERT is deferred. Ask-agent-1-token is rejected for v1.
- Q4: Zero-LLM pruning always runs before LLM summary. If pruning recovers enough burden, defer summarization.

## a/b/c/d Mapping

| Case | Meaning | Action |
|---|---|---|
| a | Not enough space | Snapshot, then `FORCED_COMPACT` on hook-rich or `PREPARE_FOR_COMPACT` elsewhere. |
| b | Space is enough but context is burdened | `ZERO_LLM_PRUNE`; compact only at a boundary. |
| c | Relevant task and plenty of space | `NOOP`, with optional deterministic pruning if burden is high. |
| d | Relevant task but low space | Snapshot, then forced/prepare path; active facts must be preserved. |

