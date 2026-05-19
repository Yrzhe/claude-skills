# Host Capability Matrix

Use this matrix to keep portability claims honest. V1 is a policy and recovery layer. It enforces native compaction only where the host exposes a hook-rich lifecycle seam.

| Host class | Capability tier | V1 can do | V1 must not claim |
|---|---|---|---|
| Claude Code | `hook-rich` | Run `UserPromptSubmit`, `PreCompact`, and `SessionStart` hooks; score signals; write `TASK_STATE.md`; dump transcript pointer; log decisions; block or allow native PreCompact snapshot-first; rehydrate state after compact/start. | Perfect recall, universal post-compact audit, or control over summary quality beyond the host hook surface. |
| Codex CLI | `advise-persist` | Run session/prompt/stop hooks where configured; write state; log decisions; advise compact/fork/prune; use compact prompt text for local/open compaction paths. | Control over opaque server compaction content or guaranteed compaction timing. |
| Codex server compaction | `advise-persist` | Snapshot before compaction and provide reload/recall guidance afterward when observable. | Human-auditable compaction item or deterministic preservation inside the server blob. |
| MCP-only agents such as Cursor/Windsurf-like surfaces | `persist-only` | Save/search/state/handoff through external tools or local files. | Native compaction timing, PreCompact blocking, or summary verification. |
| Direct API implementation controlled by the user | `persist-only` by default, custom if wrapped | Use explicit thresholds and compact endpoint if the wrapper owns the loop. | Generalize that control to hosted CLI/IDE agents. |
| Unknown host | `persist-only` | Downgrade conservatively, save state, log decision, ask before destructive action. | Any automatic compaction enforcement. |

## Action Downgrade Rules

| Decision action | `hook-rich` | `advise-persist` | `persist-only` |
|---|---|---|---|
| `NOOP` | Allowed | Allowed | Allowed |
| `ZERO_LLM_PRUNE` | Allowed if the host can replace or quarantine context; otherwise advise | Advise/persist | Advise/persist |
| `SAVE_STATE` | Write local state | Write local state | Write local state |
| `PREPARE_FOR_COMPACT` | Snapshot, then allow/advise native compaction | Snapshot and advise only | Snapshot and advise only |
| `FORCED_COMPACT` | Allowed only after snapshot through PreCompact-style interception | Degrade to `PREPARE_FOR_COMPACT` | Degrade to `PREPARE_FOR_COMPACT` |
| `FORK_OR_RESET` | Recommend fresh thread/session | Recommend fresh thread/session | Recommend fresh thread/session |
| `ASK_USER` | Ask before destructive action | Ask before destructive action | Ask before destructive action |

## Acceptance Rule

If a host cannot prove it can intercept compaction before native summary generation, describe the integration as **advise/persist** or **persist-only**. Do not call it forced compaction.
