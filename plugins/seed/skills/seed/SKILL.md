---
name: seed
description: "Read the current Claude Code session's raw activity log and help the user synthesize it into tweet material. Use when user says /seed, 'save this for twitter', 'this is tweet material', 'capture this', '记一下', '发推', or wants to turn recent work into a tweet."
---

# Session Seed (auto-recorded, on-demand synthesized)

A Stop hook silently records every turn of every Claude Code session into a per-session markdown file. When the user wants to tweet about what they just did, you read that file and help them turn raw activity into a draft.

## Architecture

```
~/.claude/
├── hooks/capture-session-seed.sh    # Stop hook → appends turn record
├── skills/seed/
│   ├── SKILL.md                     # (this file)
│   ├── scripts/
│   │   ├── extract_turn.py          # called by the hook
│   │   └── shot.py                  # /seed shot — screenshot + session binding
│   └── state/
│       ├── sessions/{session_id}.md        # raw turn logs, one per session
│       ├── sessions/{session_id}/shots/    # screenshots bound to that session
│       └── archive/                        # optional: consumed seeds moved here
```

The hook is **mechanical** — it extracts the last user prompt + all assistant text/tool_use blocks for that turn and appends a markdown block. No scoring, no synthesis, no LLM call. De-duped by user-prompt uuid so repeat Stops on the same turn don't double-write.

## When User Invokes

### `/seed` — read-and-synthesize flow

1. Get current session's file:
   - Read `$CLAUDE_SESSION_ID` if exported, otherwise ask the user (the ID is the jsonl filename in `~/.claude/projects/.../<session-id>.jsonl`)
   - Path: `~/.claude/skills/seed/state/sessions/{session_id}.md`
2. Read the full session log. It's a flat list of turns, each with:
   - Timestamp
   - User prompt
   - Tools used (name + short input summary)
   - Full assistant output
3. Synthesize: scan for the genuinely tweet-worthy moments — specific decisions, non-obvious observations, concrete data points, real problems solved. **Skip routine back-and-forth.**
4. Present 2–3 draft tweet angles tied to actual evidence from the log. Each draft must:
   - Reference a real action from the log (tool used, file touched, problem faced)
   - Include specific detail (number, tool name, timing)
   - Lead with reframe or observation, not agreement
   - Sound human: no AI-slop phrases ("The real X isn't Y, it's Z", "Happy to...", "Makes me think...")
   - 200–350 chars for replies; longer is fine for standalone originals
5. Ask which draft the user wants refined.

### `/seed <one-line description>` — manual override

User wants to capture something that ISN'T in the log (e.g., a non-Claude moment). Save a manual entry with their description; generate drafts as above.

### `/seed done` — archive/delete

After user posts, move the session file to `state/archive/{YYYY-MM-DD}_{session_id}.md` (or just delete if the user prefers). Reduces clutter and marks the raw material as consumed.

### `/seed list` — show all current session logs

Print filenames + first turn timestamp + file size. Useful when a user wants to pick material from a past session they remember.

### `/seed shot` — capture a screenshot and bind to current session

Two modes, delegated to `scripts/shot.py`:

```bash
# Interactive: cursor turns into a camera, user clicks the target window
python3 ~/.claude/skills/seed/scripts/shot.py --session-id $SID

# Headless: screenshot a URL
python3 ~/.claude/skills/seed/scripts/shot.py https://example.com --session-id $SID
python3 ~/.claude/skills/seed/scripts/shot.py localhost:3000 --session-id $SID --note "dashboard after latency fix"
```

**Always pass `--session-id` with the CURRENT session's id.** You (the agent) know which session you're in — the transcript path is `~/.claude/projects/.../{session_id}.jsonl`, and `$CLAUDE_SESSION_ID` is often set. Whichever session *triggered* the shot is the one it should bind to. Without `--session-id`, shot.py falls back to "most recently modified session file" — which is wrong when multiple Claude Code windows are running in parallel.

Output goes to `state/sessions/{session_id}/shots/{timestamp}.png` and appends a `**📸 Shot**` marker to the session's `.md` file. During `/seed` synthesis, read those markers and reference the image paths when a tweet draft would benefit from a screenshot.

Uses:
- Interactive mode when the tweet-worthy thing lives in a native app or needs multi-window framing (no Accessibility permission needed — `screencapture -w` does it). macOS only lets one `screencapture -w` own the cursor at a time, so parallel sessions can't collide.
- URL mode for dev servers, public pages, or anything Chrome can render headlessly (`--headless=new` at 1280×800 by default; override with `--width`/`--height`)

When the user says "拍一下 / 截图 / shot this / grab a screenshot" during a work session, run the appropriate mode unprompted.

## Synthesis Guidelines

- **Pure facts in, judgment on request out.** The log is raw. Your job at `/seed` invocation is to add the judgment the hook intentionally skipped.
- **Verify before citing.** If you draft "fixed a naive-datetime bug in notion_check_pending.py", confirm that's what the log actually shows (tool = Edit on that file, not just mentioning it).
- **Prefer one good draft over three generic ones.** If only one angle from the session is actually tweet-worthy, say so.
- **Skip if nothing fits.** If the session was routine (config edits, doc reads, no real discoveries), tell the user plainly — don't manufacture a tweet.

## Format of Raw Session File (hook output)

Example of what the hook writes per turn:

```markdown
## 2026-04-20 22:59:52
<!-- turn-uuid: abc-...-xyz -->
**cwd:** `/path/to/project`

**User:**

扫一下

**Tools:**
- `Bash` — python3 ~/.claude/skills/tweet-monitor/scripts/scan.py ...
- `Read` — /Users/.../notion_check_pending.py

**Assistant output:**

(full markdown body of what Claude said, untruncated)

---
```

The `turn-uuid` marker is how the hook dedupes repeat invocations.

## Tweet Draft Rules (re-applied during synthesis)

- Lead with the result, not the process
- Include a specific detail (time, number, tool name)
- Write as "I" not "we"
- No "The real X isn't Y, it's Z" pattern
- Must sound like a human talking, not AI writing
- Reinforce identity: "AI PM shipping with Claude Code"

## What the Hook Does NOT Do

- It does NOT score / rank / filter turns
- It does NOT summarize — full assistant output is preserved
- It does NOT touch Google Drive (old location is deprecated)
- It does NOT invoke any LLM — zero cost, zero latency

If you want LLM-level filtering, that's what `/seed` invocation is for. The hook stays dumb by design.
