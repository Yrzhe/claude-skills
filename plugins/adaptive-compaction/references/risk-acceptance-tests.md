# Risk Acceptance Tests

Use this checklist to verify the implementation and docs against the 20-row risk register. A release candidate should not pass unless every applicable item is checked or explicitly waived with a reason.

- [ ] **R1 Overstated portability:** Public docs include a host capability matrix and label each behavior as enforce, advise, or persist-only.
- [ ] **R2 Codex server compaction opacity:** Codex hard/forced paths require TASK_STATE and transcript pointer before native compaction is trusted.
- [ ] **R3 Prompt-cache invalidation:** Stable instructions remain before rewritten state; decision logs capture thresholds and cooldowns for cache analysis.
- [ ] **R4 Compaction thrash:** Repeated LLM compaction is blocked within cooldown unless hard cap; low-recovery compaction escalates to fork/reset or state save.
- [ ] **R5 Mid-task compaction:** Active edit, failing test, unresolved tool error, or uncheckpointed plan blocks compaction unless hard cap is reached.
- [ ] **R6 Topic shift with healthy headroom:** Low relevance plus healthy headroom recommends fork/reset, not in-place compact.
- [ ] **R7 Relevance false negatives:** Low-confidence relevance cannot by itself trigger destructive action; ask/save-state is used when continuity is high.
- [ ] **R8 Relevance false positives:** Lexical overlap alone is insufficient; objective/file/symbol/plan evidence is required for high relevance.
- [ ] **R9 Burden heuristic deletes useful evidence:** Every pruned event has a restore pointer with disk path and sha256; no hard deletion.
- [ ] **R10 LLM summary before cheap pruning:** Dedup, supersede, error purge, and quarantine run before any summary recommendation.
- [ ] **R11 State packet too prose-heavy:** TASK_STATE contains operational fields: goal, constraints, branch/worktree/session, files/symbols, decisions, failing tests, risks, next action, reload files, transcript pointer.
- [ ] **R12 TASK_STATE drift:** State packet meta includes timestamp, source turn, host, host version, session id, confidence, and transcript pointer.
- [ ] **R13 Transcript dump privacy/size:** State packet writer redacts OpenAI keys, GitHub tokens, AWS access keys, Slack tokens, JWTs, private keys, and emails before writing.
- [ ] **R14 MCP availability mistaken for reliability:** Forced paths have a local file fallback; the v1 docs do not require MCP to be available.
- [ ] **R15 Hook timing mismatch:** Host notes distinguish hook-rich, advise-persist, and persist-only behavior; unknown hosts downgrade conservatively.
- [ ] **R16 User over-trusts automated decisions:** Destructive actions are visible in the decision output with reason, `require_snapshot`, and host limitation note.
- [ ] **R17 Eval overfits synthetic traces:** Eval protocol requires real traces for main claims and labels synthetic traces as fixtures only.
- [ ] **R18 Host version drift:** Decision/state metadata captures host and host version; unknown host/tier downgrades to persist-only.
- [ ] **R19 Recovery artifact exists but is not used:** Post-compact flow has a recall probe or explicit reload instruction for TASK_STATE and files-to-reload.
- [ ] **R20 Token reduction over task success:** Eval pass gates prioritize user-correction and task-success deltas over recovered tokens.
