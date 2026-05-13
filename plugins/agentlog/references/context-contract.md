# Context file contract (Layer 2)

agentlog's Layer 1 (event pool) captures raw activity. Layer 2 is a
distilled, human-readable snapshot of project state that every AI coding
agent reads on entry. This file specifies the contract.

## File layout

```
<project>/
├── AGENTS.md                       ← Cursor + Codex default entrypoint
├── CLAUDE.md                       ← Claude Code default entrypoint
└── docs/agent-context/
    ├── state.md                    ← current snapshot (overwrite)
    ├── decisions.md                ← design tradeoffs + rationale (append-only)
    └── next-steps.md               ← open work (overwrite)
```

## Double-write rule

AGENTS.md and CLAUDE.md hold a managed block delimited by markers:

```markdown
<!-- agentlog:state-start -->
## Current state
<state.md body>

## Next steps
<next-steps.md body>
<!-- agentlog:state-end -->
```

`agentlog context sync` only edits text **between** these markers.
Everything outside (user's own setup notes, coding-style preferences,
secrets warnings, etc.) is preserved verbatim. Both files always carry
the same block content — that's the "double-write" invariant.

## File semantics

| File | Mode | Why |
|---|---|---|
| `state.md` | overwrite | current snapshot; old states recoverable via git diff |
| `decisions.md` | append-only | rationale history must never be lost |
| `next-steps.md` | overwrite | TODO list; completed items move into git history |

`brief.py` enforces `append-only` for decisions by checking the existing
file content before writing each entry. Duplicate titles within the same
date are skipped.

## Decision entry format

```markdown
## YYYY-MM-DD — <short title>

**Why**: <one or two sentences of rationale>

**Alternatives considered**:
- <option A>
- <option B>

_source: <event_id or brief:<project_name>>_
```

## When agents should read this

- **First time entering a project**: read AGENTS.md / CLAUDE.md to get
  the state block, then `docs/agent-context/decisions.md` for the why.
- **Before suggesting a design**: read decisions.md to avoid repeating
  rejected alternatives.
- **After a working session**: run `agentlog brief --project <name>` to
  refresh state + next-steps and append any new decisions surfaced.

## When NOT to use the context layer

- **Single conversation**: just use the conversation itself, don't bother.
- **No git history**: state.md overwrite mode relies on git tracking for
  audit; if the project isn't tracked, decisions still work but state
  drift is invisible.
- **External docs already canonical**: if the project has a thorough
  `README.md` or `ARCHITECTURE.md`, AGENTS.md should reference those
  rather than re-distilling.
