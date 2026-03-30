---
name: skill-improve
description: Improve existing skills after use. When Claude uses a skill and discovers issues (outdated steps, missing edge cases, unclear instructions, wrong assumptions), suggest "/skill-improve" after the current task completes. Also use when user says "fix this skill", "this skill is wrong", "update skill", or "/skill-improve <skill-name>".
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

# Skill Improve — Post-Use Skill Maintenance

Improve existing skills based on real usage experience. Always finish the current task first.

## Trigger Rules

- **After task completion**: If a skill was used and had issues, suggest: "The `<skill-name>` skill had some gaps — want me to `/skill-improve` it?"
- **Manual**: `/skill-improve <skill-name>` or `/skill-improve` (defaults to most recently used skill in session)
- **NEVER interrupt** the current task to improve a skill. Finish first, improve after.

## Improvement Flow

### 1. Identify Target

Determine which skill to improve:
- If `<skill-name>` provided, use that
- If no argument, use the most recently invoked skill in this session
- If no skill was used, ask the user which skill to improve

### 2. Read Current Skill

Read the target skill's `SKILL.md` and any bundled resources (`scripts/`, `references/`, `assets/`).

### 3. Diagnose Issues

Compare the skill's instructions against actual execution experience. Categorize problems:

| Category | Example |
|----------|---------|
| **Outdated** | Tool/API changed, deprecated method |
| **Missing** | Edge case encountered that skill didn't cover |
| **Redundant** | Steps Claude already knows, wasting context |
| **Unclear** | Ambiguous instruction that caused wrong action |
| **Wrong** | Incorrect assumption or factual error |

### 4. Generate Diff Preview

Show the user exactly what will change:
- Quote the original text
- Show the proposed replacement
- Explain why for each change

Do NOT modify the file until user confirms.

### 5. Apply Changes

After confirmation:
- Edit the SKILL.md (and bundled resources if needed)
- Preserve the skill's name and description structure unless the issue is there
- Keep changes minimal — fix what's broken, don't rewrite what works

### 6. Log the Improvement

Update or create `~/.claude/skills/learn/learned/<skill-name>.md`:

If the file exists, append to the improvement record section:
```markdown
### <YYYY-MM-DD>
- **Problem**: <what was wrong>
- **Fix**: <what was changed>
- **Source**: <task context that revealed the issue>
```

If the file doesn't exist (non-learned skill being improved for the first time), create it:
```markdown
---
skill: <skill-name>
created: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source: improvement
---

## Improvement Record
### <YYYY-MM-DD>
- **Problem**: <what was wrong>
- **Fix**: <what was changed>
- **Source**: <task context that revealed the issue>
```

### 7. Memory Sync (Optional)

If a memory system is available and the fix revealed a universal insight (not just a skill-specific correction), save a concise one-line version to memory.

## Scope Limits

- **Small fixes**: Apply directly (typos, outdated commands, missing steps)
- **Major redesign**: If the skill's entire approach is wrong, suggest using `/learn` to extract a new skill instead of patching
- **Don't bloat**: If adding content would push SKILL.md over 500 lines, suggest splitting into reference files instead
