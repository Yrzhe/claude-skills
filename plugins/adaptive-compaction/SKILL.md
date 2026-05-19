---
name: adaptive-compaction
description: >-
  Adaptive add-on policy and recovery layer that decides WHEN to compact,
  prune, snapshot, or fork -- replacing fixed-percent auto-compaction across
  Claude Code, Codex, and MCP agents. Trigger on auto-compact timing or
  damage: "when should I compact", "is it safe to compact now or start a fresh
  session", "auto-compact fires too early/mid-task", "switching to an
  unrelated task but the window still has space", "context rot", "answers get
  worse the longer the session runs", "the agent forgot the plan or my
  decisions after it summarized", "add a layer on top that manages context
  without changing the agent", raising autoCompactWindow to give the policy
  room, or installing/tuning a cross-tool compaction policy or PreCompact hook
  -- even when "compaction" is never said but the problem is context-window
  pressure or post-summarization memory loss. Do NOT use to summarize a
  conversation, build RAG, write a summarization prompt (decides WHEN not
  HOW), or answer max-context-length trivia.
allowed-tools: Read, Bash, Write, Edit
---

<!-- Suggested allowed-tools: Read, Bash, Write, Edit. Suggested model: strong everyday coding model; upgrade for architecture review, not routine hook/script operation. -->

# Adaptive Compaction

Use this skill to install, inspect, or operate the adaptive compaction policy and recovery layer for coding agents. Keep the layer add-on only: decide when to preserve, prune, compact, fork, or ask; never rewrite the host agent core.

## Operating Rules

Follow these rules before taking action:

1. Preserve state before any risky compaction path.
2. Run zero-LLM pruning before any LLM summary recommendation.
3. Treat relevance as advisory. Never use low relevance alone for destructive action.
4. Prefer fork/reset on topic shift when headroom is healthy.
5. Enforce `FORCED_COMPACT` only on hook-rich hosts. Degrade Codex and MCP-only hosts to advise/persist.
6. Keep stable instructions before volatile state to avoid prompt-cache churn.
7. Log every decision with thresholds and host capability tier.
8. Use portable paths such as `<skill-dir>/scripts/decide.py`; do not hardcode install paths.

## Load References Conditionally

Do not read every reference by default. Load only the rows needed for the current request.

| Task | Read |
|---|---|
| Check JSON contracts or script I/O | `<skill-dir>/references/contract.md` |
| Explain or tune the four-signal decision table | `<skill-dir>/references/decision-policy.md` |
| Make or review host portability claims | `<skill-dir>/references/capability-matrix.md` |
| Validate release safety or risk coverage | `<skill-dir>/references/risk-acceptance-tests.md` |
| Plan trace evaluation or v1 to v2 gates | `<skill-dir>/references/eval-protocol.md` |
| Install Claude Code hooks | `<skill-dir>/assets/hooks/claude-code/settings.json` and the three shell scripts in that folder |
| Install Codex hooks/config | `<skill-dir>/assets/hooks/codex/hooks.json` and `<skill-dir>/assets/hooks/codex/config.toml` |
| Run deterministic fixture checks | `<skill-dir>/scripts/fixtures/*.json` |

## Workflow

### 1. Classify Host Capability

Classify the host before choosing behavior:

| Host | Tier | Behavior |
|---|---|---|
| Claude Code with lifecycle hooks | `hook-rich` | Allow snapshot-first `FORCED_COMPACT` through PreCompact block/allow. |
| Codex CLI | `advise-persist` | Save state, log advice, shape prompts/config; do not claim opaque server control. |
| Codex server compaction | `advise-persist` | Snapshot before and verify after when observable. |
| MCP-only host | `persist-only` | Save/search/state only; no native compaction claim. |
| Unknown host | `persist-only` | Downgrade conservatively and ask before destructive action. |

Load `<skill-dir>/references/capability-matrix.md` when the host behavior is disputed or user-facing.

### 2. Score Signals

Prepare host telemetry matching `<skill-dir>/references/contract.md`, then run:

```bash
python3 <skill-dir>/scripts/score_signals.py < telemetry.json > signals.json
```

Use the scorer output as the only input to the decision table. Do not add model calls in v1.

### 3. Decide Action

Run:

```bash
python3 <skill-dir>/scripts/decide.py < signals.json > decision.json
```

Accept only these actions:

- `NOOP`
- `ZERO_LLM_PRUNE`
- `SAVE_STATE`
- `PREPARE_FOR_COMPACT`
- `FORCED_COMPACT`
- `FORK_OR_RESET`
- `ASK_USER`

If `FORCED_COMPACT` appears outside `hook-rich`, treat it as a bug. The decider should downgrade it to `PREPARE_FOR_COMPACT`.

### 4. Act on the Decision

Use this table:

| Decision | Action |
|---|---|
| `NOOP` | Continue without compaction. |
| `ZERO_LLM_PRUNE` | Run `<skill-dir>/scripts/prune_zero_llm.py`; replace in-context blobs only with restore pointers. |
| `SAVE_STATE` | Run `<skill-dir>/scripts/state_packet.py`; write `TASK_STATE.md` plus transcript pointer. |
| `PREPARE_FOR_COMPACT` | Run `state_packet.py`, then advise the host/native compactor. |
| `FORCED_COMPACT` | Allow only in Claude Code PreCompact after `state_packet.py` succeeds. |
| `FORK_OR_RESET` | Recommend a fresh task/session and preserve old state if useful. |
| `ASK_USER` | Ask before destructive action. |

For pruning:

```bash
python3 <skill-dir>/scripts/prune_zero_llm.py < telemetry.json > prune.json
```

For state:

```bash
python3 <skill-dir>/scripts/state_packet.py < state-input.json > state-result.json
```

### 5. Log the Decision

Always append a JSONL decision entry:

```bash
python3 <skill-dir>/scripts/decision_log.py < log-input.json > log-result.json
```

Include the selected action, headroom, relevance, burden, continuity flags, host tier, thresholds, and snapshot requirement.

## Hook Assets

### Claude Code

Use `<skill-dir>/assets/hooks/claude-code/` for hook-rich enforcement:

- `pre-compact.sh` calls `<skill-dir>/scripts/hook_bridge.py claude-pre-compact`.
- `session-start.sh` calls `<skill-dir>/scripts/hook_bridge.py claude-session-start`.
- `user-prompt-submit.sh` calls `<skill-dir>/scripts/hook_bridge.py claude-user-prompt-submit`.
- `settings.json` shows the hook configuration snippet.

The PreCompact path is the only v1 host-scoped native `FORCED_COMPACT` path. It snapshots first, then allows or blocks compaction according to the decision table.

Set `ADAPTIVE_COMPACTION_SKILL_DIR=<skill-dir>` if the shell scripts are copied outside the skill folder. Set `ADAPTIVE_COMPACTION_DIR` to choose the runtime directory for `TASK_STATE.md`, transcript dumps, decision logs, and quarantine files.

### Codex

Use `<skill-dir>/assets/hooks/codex/` for advise/persist integration:

- `hooks.json` routes session, prompt, and stop events into `<skill-dir>/scripts/hook_bridge.py`.
- `config.toml` contains a compact prompt snippet that asks native compaction to preserve the state packet shape.

Never claim Codex server compaction content is controlled or auditable. Snapshot externally and log advice.

### Hook Bridge

Use `<skill-dir>/scripts/hook_bridge.py` only as a host adapter. It normalizes hook JSON, imports the scorer/decider/pruner/state/log scripts, writes runtime artifacts, and emits hook-friendly JSON. Keep policy in the scripts and references, not in host assets.

## How the Decision Is Made (so you can reason about it)

Runtime autonomy does NOT come from the agent deciding anything per turn. The
host harness fires hooks deterministically; each hook runs zero-token Python
(`score_signals.py` -> `decide.py`). There is no per-turn LLM call in v1. The
skill `description` only matters when a human asks to install/tune/explain the
policy -- it is NOT the runtime trigger. These are two separate planes; keep
them separate when explaining to the user.

The four signals and how each is judged (all deterministic, see
`<skill-dir>/references/decision-policy.md` for exact formulas):

- **Headroom** = free context fraction from token counts. Pure arithmetic.
- **Relevance** = lexical + structural overlap of the new prompt vs the
  current objective / hot files / touched symbols / plan. No model call;
  advisory only -- never the sole cause of a destructive action.
- **Burden** = estimated reclaimable tokens: duplicate reads, superseded
  writes, errored-tool inputs, oversized tool outputs.
- **Continuity** = open edit / failing test / unresolved tool error /
  uncheckpointed plan flags. High continuity blocks mid-task compaction.

`decide.py` runs the canonical table in `references/decision-policy.md` over
these four plus the host capability tier, emitting one action.

## Install It Yourself

If you can edit the host config, set this up directly instead of asking the
user to do it by hand:

1. **Wire the hooks.** Add `<skill-dir>/assets/hooks/claude-code/` PreCompact,
   SessionStart, and UserPromptSubmit entries to `settings.json` (snippet in
   that folder). Set `ADAPTIVE_COMPACTION_SKILL_DIR` to the installed skill
   path and `ADAPTIVE_COMPACTION_DIR` to a runtime dir. For Codex, install
   `<skill-dir>/assets/hooks/codex/hooks.json` + `config.toml`.
2. **Give the adaptive policy room (raise the native trigger).** Native
   auto-compaction can fire on its own threshold before this policy's
   preferred action runs. Because this layer is adaptive, push the native
   trigger LATER so the policy decides first:

| Host | Real setting | Action |
|---|---|---|
| Claude Code | `autoCompactWindow` in `settings.json` (token count at which native auto-compact fires; higher = fires later) | Raise it well above the default for the model's window (e.g. for a 1M-context model, raise from `400000` toward `~800000`) so PreCompact + policy decide first. Confirm the model's true window before picking a number. |
| Codex CLI | `model_auto_compact_token_limit` | Set conservatively in `<skill-dir>/assets/hooks/codex/config.toml` so the policy decides first; still snapshot before opaque server compaction. |
| MCP-only | none exposed | Cannot raise or intercept; persist/recover only. State the limit honestly. |

Raising the native trigger is real insurance here (the host exposes it), but
the PreCompact block/allow boundary remains the primary mechanism: snapshot
first, then block if policy says "not yet / fork", or allow with
state-packet-preserving instructions. This IS the v1 host-scoped
`FORCED_COMPACT` seam. Never claim full prevention of native compaction on a
host that exposes no interception seam (MCP-only).

## Script Index

| Script | Purpose |
|---|---|
| `<skill-dir>/scripts/score_signals.py` | Score headroom, relevance, burden, continuity, and host tier from telemetry. |
| `<skill-dir>/scripts/decide.py` | Apply the canonical decision table and host downgrade rules. |
| `<skill-dir>/scripts/prune_zero_llm.py` | Plan reversible dedup, supersede, error-purge, and quarantine actions. |
| `<skill-dir>/scripts/state_packet.py` | Write redacted `TASK_STATE.md` with transcript pointer and meta trailer. |
| `<skill-dir>/scripts/decision_log.py` | Append one JSONL decision record. |
| `<skill-dir>/scripts/hook_bridge.py` | Bridge Claude Code and Codex hook payloads into the script contract. |
| `<skill-dir>/scripts/thresholds.json` | Store trace-tunable v1 threshold defaults. |
| `<skill-dir>/scripts/fixtures/*.json` | Exercise telemetry-level and signal-level policy cases. |

## Fixture Check

Run fixture checks after editing scripts or hook bridge behavior:

```bash
for f in <skill-dir>/scripts/fixtures/case_[abcd]*.json \
         <skill-dir>/scripts/fixtures/case_review_explicit_marker.json; do
  python3 <skill-dir>/scripts/score_signals.py < "$f" \
    | python3 <skill-dir>/scripts/decide.py
done

for f in <skill-dir>/scripts/fixtures/*_signals.json; do
  python3 <skill-dir>/scripts/decide.py < "$f"
done
```

Run at least one hook bridge smoke test:

```bash
python3 <skill-dir>/scripts/hook_bridge.py claude-user-prompt-submit \
  < <skill-dir>/scripts/fixtures/case_c_relevant_space_ok.json
```

## Output Discipline

When reporting results:

- State the host tier and chosen action.
- State whether a snapshot was required and where it was written.
- State whether behavior was enforce, advise/persist, or persist-only.
- Mention any downgrade, especially Codex opaque compaction or MCP-only hosts.
- Keep recovered-token claims secondary to continuity and task-success claims.
