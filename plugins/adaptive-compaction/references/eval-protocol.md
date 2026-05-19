# Q6 Evaluation Protocol

This protocol is the gate for moving adaptive-compaction beyond the v1 file-based policy layer. The main result must come from real traces, not synthetic prompts.

## Primary Metrics

| Metric | Definition | Pass Direction |
|---|---|---|
| Forced-compaction rate | Forced/native compactions per 100 user turns or task-hours. | Down or no worse while task success is stable. |
| Thrash rate | Sessions with repeated compactions inside cooldown, or compactions recovering less than the configured minimum. | Down or near zero. |
| Post-compact recall | Field-level score for goal, constraints, branch/worktree, touched files, decisions, failing tests, open risks, next action, reload files. | Up; no wrong goal/constraint/next-action fields. |
| User-correction rate | User turns that restate lost context or correct forgotten assumptions after compaction. | Not worse than baseline. |
| Cache-hit delta | Prompt-cache hit rate and cached-token share versus baseline. | Not materially worse unless explicitly accepted. |
| Task-success delta | Completion quality versus baseline: tests pass, artifact created, review accepted, or user accepts result. | Non-negative overall; never negative for coding tasks. |

## Secondary Metrics

- Zero-LLM recovery ratio: tokens recovered by dedup, supersede, error purge, and quarantine divided by reclaimable burden.
- LLM-summary frequency: LLM compactions per session/task.
- Snapshot coverage: forced/native compactions preceded by TASK_STATE plus transcript pointer.
- Recovery use rate: post-compact sessions that reload or reference the state artifact.
- Decision precision: compact/fork/noop recommendations judged correct by human review.
- Relevance false-negative rate: continuing-task turns wrongly treated as topic shift.
- Relevance false-positive rate: real topic shifts wrongly treated as continuing task.
- Latency delta: added p50/p95 wall-clock time per user turn.
- Storage overhead: bytes written for state packets, transcript dumps, and quarantined outputs.

## Real-Trace Corpus Generation

1. Collect real sessions from Claude Code, Codex, and MCP-only or persist-only workflows.
2. Include coding implementation, bug triage, code review, research synthesis, document authoring, and long-running skill construction.
3. Include naturally high-pressure sessions that reached compaction or near-compaction, plus matched ordinary sessions.
4. Use local-only traces by default.
5. Redact secrets, credentials, private tokens, emails, and sensitive file contents before evaluator access.
6. Preserve structural metadata: turn order, tool type, token estimates, file path shape, exit codes, compaction events, and user correction turns.
7. Split by session: 60% tuning, 20% validation, 20% held-out test. Do not split turns from one session across sets.
8. Balance host classes so Claude-only evidence is not presented as cross-agent evidence.

## Minimum Corpus Before Non-Pilot Claims

- At least 100 real sessions.
- At least 30 sessions per major host class before comparing host-specific behavior.
- At least 20 naturally compacted or high-pressure sessions before claiming compaction benefit.
- Anything smaller must be labeled pilot data.

## Trace Schema

Each trace should contain:

```json
{
  "trace_id": "...",
  "host": "claude-code|codex|mcp-only|api|unknown",
  "host_version": "...",
  "model": "...",
  "task_type": "...",
  "repo_or_workspace_type": "...",
  "turns": [],
  "tool_events": [],
  "token_estimates": {},
  "native_compaction_events": [],
  "manual_compaction_events": [],
  "state_artifacts_written": [],
  "quarantined_outputs": [],
  "final_outcome": "...",
  "user_correction_turns": [],
  "cache_usage": {}
}
```

## Replay Modes

| Mode | Intervention |
|---|---|
| Baseline replay | Native host behavior or recorded original behavior. |
| Policy-shadow replay | Policy observes and logs decisions, but does not intervene. |
| Policy-assisted replay | Policy writes TASK_STATE, prunes/quarantines, and recommends actions. |
| Policy-enforced replay | Only for hook-rich hosts; policy may block/prepare compaction where supported. |

## Human Labels

Label each trace for:

- Task boundary moments.
- Mid-task protected intervals.
- Topic shifts.
- Open edit/test/debug loops.
- User corrections due to forgotten context.
- Whether compact/fork/noop would have been correct at each decision point.

## Recall Probe

After every native/manual/simulated compaction, score whether the active state contains:

- Current goal.
- Accepted constraints.
- Current branch/worktree/session.
- Hot files and touched symbols.
- Decisions already made.
- Failing tests/commands/exact repro.
- Open risks/questions.
- Exact next action.
- Files to reload first.

Score each as `present`, `partial`, `missing`, or `wrong`. A `wrong` goal, constraint, or next action is high severity.

## Required Ablations

- No policy vs full policy.
- Zero-LLM pruning only vs LLM summary enabled.
- Headroom-only trigger vs four-signal trigger.
- Lexical relevance only vs lexical plus file/symbol/objective overlap.
- Compact-on-topic-shift vs fork/reset-on-topic-shift.
- Stable-prefix state placement vs rewritten-prefix state placement.

## Pass Gates

The policy can advance only if:

- User-correction rate does not increase versus baseline.
- Task-success delta is non-negative overall and not negative for coding tasks.
- Thrash rate decreases or remains near zero.
- Snapshot coverage for forced/native compactions is above 95% where interception is possible.
- Cache-hit delta is not materially worse, or the cost is explicitly accepted.
- Relevance false negatives do not trigger destructive action in protected mid-task intervals.

## Reporting Requirements

Every eval report must include host capability matrix, corpus composition, redaction policy, threshold config, per-host results, false-positive/false-negative examples, cost/latency deltas, cache-hit deltas where available, user-correction examples, and explicit remaining unknowns.
