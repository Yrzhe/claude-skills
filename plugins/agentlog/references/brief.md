# `agentlog brief` — event pool → distilled context

`brief` is Layer 2 of agentlog. It reads recent events for a project,
asks Haiku 4.5 to distill them into three markdown sections, then writes
those into `docs/agent-context/{state,decisions,next-steps}.md` and
syncs AGENTS.md + CLAUDE.md.

## Usage

```bash
agentlog brief --project agentlog --last 7d
agentlog brief --project agentlog --project-root /Users/me/code/agentlog
```

Defaults: `--last 7d`, project root = current directory.

## Requirements

- `ANTHROPIC_API_KEY` exported in env (fail-fast if missing)
- `anthropic` Python package installed (`pip install anthropic`)
- At least one event in the pool for the given project name

## Event selection

`brief.select_events` picks up to 200 events from the window, prioritizing:

1. `action.type == "decision"` (highest)
2. `action.type == "next_step"`
3. `action.type == "checkpoint"`
4. `action.type == "session_completed"`
5. `action.type == "file_changed"`
6. `action.type == "error"`
7. `action.type == "command_run"`
8. everything else

Within a tier, original ordering is preserved. Final selected events are
re-sorted by timestamp ascending before being sent to the model.

## Prompt contract

System message (constant, in `brief.py`):

```
You distill an AI-coding project's recent activity into 3 markdown sections.
Every claim must be grounded in the events provided — do not invent facts.
Be terse: bullets, not paragraphs. Decisions must answer 'why this and not
the alternatives'. Output exactly three sections separated by '---STATE---',
'---DECISIONS---', '---NEXT-STEPS---' markers.
```

User message format:

```
Project: <name>
Event count: <N>

[<ts>] (<source_type> · <action.type>) <summary>  WHY: <payload.rationale>
... one line per event ...

Now distill into three sections.
```

## Expected response format

```
---STATE---
- bullet ...
- bullet ...

---DECISIONS---
## <short title>

**Why**: ...

**Alternatives considered**: ...

## <another decision>
...

---NEXT-STEPS---
- [ ] item (priority)
- [ ] item (priority)
```

If the model deviates, `_parse_sections` falls back to treating the
whole response as "state" with empty decisions/next-steps. Decision
parsing tolerates `**Why**:`, `Why:`, English or Chinese colons.

## Idempotency

`run_brief` reads the current `decisions.md` before each append. If the
exact title already appears, it skips. This means re-running `brief`
on the same window doesn't duplicate decision entries.

`state.md` and `next-steps.md` are full overwrites — re-running with
the same data produces the same file content (no drift).

## Cost

Haiku 4.5 is ~$0.001 per brief call (~5K input + 1K output tokens for a
typical 50-event window). Safe to run on every working session end.

## Hallucination defense

Three layers:

1. **System prompt** explicitly forbids invention.
2. **User prompt** structure constrains the model to event-derived facts
   (timestamps, source, action type, summary, optional rationale).
3. **Decision dedup** prevents the same hallucinated title from
   accumulating across runs.

If you need to audit: `brief.distill` returns the parsed sections
without writing, and `select_events` is pure → you can inspect both
before any file IO.

## When NOT to run brief

- Project has fewer than 5 events → output is mostly empty boilerplate.
- Activity span is a single conversation → just use the conversation.
- No reliable network → distill will fail; this is a hard requirement.
