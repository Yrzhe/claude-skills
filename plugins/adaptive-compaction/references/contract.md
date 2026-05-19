# Shared Script I/O Contract (v1)

All `scripts/*` exchange JSON via stdin->stdout. Conform exactly. Source of
truth: `docs/architecture/00-DESIGN.md` sec3, sec4, sec7. One contract change =
update this file first, then dependents.

## 1. Host telemetry (input to `score_signals.py`)

```json
{
  "host": "claude-code | codex | mcp-only | api | unknown",
  "host_capability_tier": "hook-rich | advise-persist | persist-only",
  "tokens_used": 152000,
  "effective_window": 200000,
  "reserved_output": 20000,
  "user_prompt": "string -- the incoming turn",
  "objective": "current accepted goal text or null",
  "accepted_constraints": ["..."],
  "hot_files": ["path", "..."],
  "touched_symbols": ["sym", "..."],
  "plan_items": ["..."],
  "recent_turns": [
    {"role": "user|assistant|tool", "summary": "string", "tokens": 1234}
  ],
  "tool_events": [
    {"type": "read|write|edit|tool", "target": "path|tool", "content_hash": "sha256", "tokens": 999, "errored": false, "turn": 12}
  ],
  "turns_since_last_compaction": 7,
  "explicit_new_task_marker": false
}
```

`host_capability_tier` mapping (fixed): `claude-code`->`hook-rich`;
`codex`->`advise-persist`; `mcp-only`/`api`->`persist-only`;
`unknown`->`persist-only` (conservative downgrade, risk R18).

## 2. Signal scores (output of `score_signals.py`, input to `decide.py`)

```json
{
  "headroom_frac": 0.24,                // (effective_window - reserved_output - tokens_used) / effective_window, clamp [0,1]
  "relevance": 0.0,                     // [0,1] lexical+structural overlap of user_prompt vs objective/hot_files/symbols/plan; NO model call
  "relevance_confidence": 0.0,          // [0,1]
  "low_relevance_streak": 2,            // consecutive low-relevance user turns (caller-tracked, passed back in)
  "burden_tokens": 48000,               // est. reclaimable: dup reads + superseded writes + errored inputs + oversized outputs
  "reclaimable_burden_frac": 0.0,       // burden_tokens / tokens_used, clamp [0,1]
  "continuity": 0.0,                    // [0,1]; high if open edit/failing test/unresolved tool error/uncheckpointed plan/unaccepted direction
  "continuity_flags": ["active_edit", "failing_test", "..."],
  "host_capability_tier": "hook-rich"   // pass-through
}
```

## 3. Decision (output of `decide.py`)

```json
{
  "action": "NOOP | ZERO_LLM_PRUNE | SAVE_STATE | PREPARE_FOR_COMPACT | FORCED_COMPACT | FORK_OR_RESET | ASK_USER",
  "reason": "one-line human explanation citing the decision-table row",
  "require_snapshot": true,             // if true, caller MUST run state_packet.py before acting
  "thresholds_used": { "...": "..." },  // echo the resolved thresholds for the decision log
  "host_note": "what the host can actually enforce vs only advise"
}
```

Hard rule in `decide.py`: emit `FORCED_COMPACT` ONLY when
`host_capability_tier == "hook-rich"`. For `advise-persist`/`persist-only`,
any forced/hard-cap path degrades to `PREPARE_FOR_COMPACT` +
`require_snapshot:true`. No universal auto-compaction. Mid-task guard
(continuity_flags non-empty) blocks compaction actions unless headroom is at
hard-cap floor -- then `SAVE_STATE` is forced first (`require_snapshot:true`).

## 4. Thresholds config (`scripts/thresholds.json`, read by `decide.py`)

Keys + v1 defaults (all trace-tunable, logged per decision):
`healthy_headroom_min=0.40`, `soft_headroom_low=0.20`,
`forced_headroom_floor=0.175`, `hard_cap_floor=0.125`,
`thrash_cooldown_turns=6`, `min_recovery_ratio=0.20`,
`zero_llm_success_ratio=0.60`, `topic_shift_confirmation_turns=2`,
`large_output_quarantine_tokens=5000`, `error_input_purge_turns=4`.
(Bands given as single values use the midpoint of the design ranges.)

## 5. State packet (`state_packet.py` writes `TASK_STATE.md` + meta)

Markdown body = the sec7 operational schema (Goal / Accepted constraints /
branch/worktree/session / touched files/symbols / decisions / failing
tests/commands/repro / open risks / exact next action / files to reload /
transcript dump pointer). Trailer meta line (machine-readable):

```json
{"ts":"ISO8601","source_turn":42,"host":"claude-code","host_version":"x","session_id":"...","confidence":0.0,"transcript_dump":"<abs path>"}
```

Redaction pass (risk R13) runs before write: mask `sk-`, `ghp_`,
`AKIA`, `xox[baprs]-`, JWT, `-----BEGIN * KEY-----`, emails.

## 6. Decision log (`decision_log.py`, append-only JSONL)

One line per decision:

```json
{"ts":"ISO8601","session_id":"...","host":"...","host_capability_tier":"...","headroom_frac":0.0,"relevance":0.0,"relevance_confidence":0.0,"burden_tokens":0,"continuity":0.0,"continuity_flags":[],"action":"...","require_snapshot":false,"recovered_tokens":null,"post_action_user_correction":null,"thresholds":{}}
```

`recovered_tokens` / `post_action_user_correction` are filled on a follow-up
update line keyed by the same `ts` when observable (Q6 metrics depend on this).

## 7. Pruner pointers (`prune_zero_llm.py` output)

Non-destructive. Returns:

```json
{
  "recovered_tokens": 31000,
  "actions": [
    {"kind":"dedup|supersede|error_purge|quarantine","ref":"<event id>","restore_pointer":"<abs path or hash>","tokens":1234}
  ],
  "quarantine_dir": "<abs path>"
}
```

Never hard-delete. Every removed item has a `restore_pointer` (disk path +
sha256). Caller replaces in-context blob with `[stored at <path>, N tokens, sha=...]`.

## CLI convention (all scripts)

`python3 <script>.py < input.json > output.json` ; non-zero exit on schema
violation with a one-line stderr reason. Pure functions importable for unit
tests. No network. No model calls anywhere in v1.
