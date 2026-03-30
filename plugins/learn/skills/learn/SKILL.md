---
name: learn
description: /learn - Extract Reusable Patterns. After completing a complex task (5+ tool calls with cross-scenario reuse potential), suggest "/learn" to the user. When invoked, analyze the current task's approach and distill it into a reusable skill or improve an existing one. Also use when user says "save this as a skill", "remember this approach", or "this is reusable".
version: 1.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Learn — Skill Auto-Extraction

Distill the current task's approach into a reusable skill, or improve an existing one.

## When to Suggest

After completing a task, evaluate TWO conditions:
1. **Complexity**: 5+ tool calls used
2. **Reuse potential**: The approach applies to other projects/scenarios, not just this one

If both met, suggest: "This approach might be reusable — want to `/learn` it?"
Never auto-execute. Only suggest.

## Extraction Flow

### 1. Recall

Check if this knowledge already exists:
- Search existing skills for similar functionality
- If a memory system (supermemory, MEMORY.md, etc.) is available, search it too

### 2. Review

Scan the current conversation for the most recently completed task. Identify:
- Core workflow steps
- Key decisions and why they were made
- Non-obvious tricks or gotchas discovered
- Tools/libraries used and how

If `/learn "description"` was provided, focus on that specific aspect.

### 3. Dedup

Search ALL existing skills for similar functionality:
```bash
ls ~/.claude/skills/
grep -r "<relevant keywords>" ~/.claude/skills/*/SKILL.md
```

Three outcomes:
- **Similar skill exists**: Suggest `/skill-improve <skill-name>` instead. Do NOT create a duplicate.
- **Similar learned skill exists**: Suggest updating that skill instead of creating new.
- **No match**: Proceed to create new skill.

### 4. Assess Scope

Determine where this knowledge belongs:
- **Cross-project reusable workflow** → Create skill (continue to step 5)
- **Project-specific pattern** → Suggest saving to local project memory instead, stop here
- **Single factual insight** → Suggest saving to memory system instead, stop here

### 5. Generate

Create skill following skill-creator conventions:

**File**: `~/.claude/skills/<skill-name>/SKILL.md`

Naming: use `learned-` prefix for auto-extracted skills (e.g., `learned-pdf-merge`).

Structure:
```markdown
---
name: learned-<name>
description: <what it does and when to trigger — be specific>
---

# <Title>

<Concise steps. Only include what Claude doesn't already know.>
```

Rules:
- Under 200 lines — context window is shared
- Imperative form ("Run X", not "You should run X")
- No README, CHANGELOG, or extra docs
- Only add `scripts/`, `references/`, `assets/` if genuinely needed

### 6. Confirm

Show the generated SKILL.md content to the user. Write to disk only after confirmation.

### 7. Log

Create or update the extraction log:

**File**: `~/.claude/skills/learn/learned/<skill-name>.md`

```markdown
---
skill: learned-<name>
created: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source: conversation
---

## Creation Record
- **Date**: <YYYY-MM-DD>
- **Task**: <what triggered the extraction>
- **Reason**: <why this is reusable>
```

Also update `~/.claude/skills/learn/learned/README.md` index with a one-line entry.

### 8. Memory Sync (Optional)

If a memory system is available (supermemory, MEMORY.md, etc.) and the extraction revealed cross-project universal insights (API quirks, tool gotchas, non-obvious behaviors), save a concise one-line version.

Do NOT duplicate the full skill content into memory. Only save atomic insights that stand alone.
