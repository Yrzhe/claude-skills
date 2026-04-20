# seed — Build-in-Public Activity Recorder

A Claude Code skill that mechanically captures every turn of your coding sessions so you can later synthesize them into tweets, blog posts, or changelogs — without having to remember what you did.

> Built because Building-in-Public requires memory. If you ship 10 things in a day, you forget 8 of them by evening. The `seed` hook logs everything automatically; the `/seed` skill helps you pick the tweet-worthy parts later.

## What's in the box

| Component | What it does |
|-----------|--------------|
| `hooks/capture-session-seed.sh` | Stop hook. Fires after every assistant turn. Dumb, mechanical — no scoring, no LLM calls. |
| `scripts/extract_turn.py` | Parses the Claude Code transcript JSONL, extracts user prompt + tool uses + assistant output for the latest turn, de-dupes by turn-uuid, appends a markdown block. |
| `scripts/shot.py` | Screenshot capture — interactive window pick (`screencapture -w`) OR headless Chrome URL mode. Binds the PNG to the current session so it shows up during `/seed` synthesis. |
| `SKILL.md` | The skill itself. Describes the architecture and tells Claude how to read the session log and propose tweet drafts when you invoke `/seed`. |

## Architecture

```
~/.claude/
├── hooks/capture-session-seed.sh    # Stop hook (you wire this up once)
└── skills/seed/
    ├── SKILL.md
    ├── scripts/
    │   ├── extract_turn.py
    │   └── shot.py
    └── state/
        ├── sessions/{session_id}.md          # raw per-session logs
        └── sessions/{session_id}/shots/      # screenshots
```

The hook is intentionally **dumb**: it extracts the last user prompt + all assistant text/tool_use blocks for that turn and appends a markdown block. De-duped by user-prompt uuid. Zero LLM cost, zero latency.

LLM-level synthesis happens only when you invoke `/seed`.

## Installation

### 1. Install the skill

**Via the marketplace (recommended):**

```bash
/plugin marketplace add yrzhe/claude-skills
/plugin install seed@yrzhe-skills
```

**Manual install:**

```bash
cp -r plugins/seed/skills/seed ~/.claude/skills/seed
chmod +x ~/.claude/skills/seed/scripts/*.py
```

### 2. Install the Stop hook

Copy the hook script into your hooks directory and make it executable:

```bash
mkdir -p ~/.claude/hooks
cp ~/.claude/skills/seed/hooks/capture-session-seed.sh ~/.claude/hooks/capture-session-seed.sh
chmod +x ~/.claude/hooks/capture-session-seed.sh
```

Then register it in `~/.claude/settings.json` under `hooks.Stop`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/capture-session-seed.sh" }
        ]
      }
    ]
  }
}
```

Restart Claude Code. From now on, every turn in every session gets logged to `~/.claude/skills/seed/state/sessions/{session_id}.md`.

### 3. (Optional) For `/seed shot` URL mode

The headless screenshot mode needs Chrome / Chromium / Edge / Arc installed. The script auto-detects from the usual macOS `/Applications` paths.

## Usage

### Let the hook log in the background

Just use Claude Code normally. After each turn, a markdown block gets appended to your session's log file. You don't have to think about it.

### When you want to tweet

```
/seed
```

Claude reads the current session's log, scans for genuinely tweet-worthy moments (specific decisions, non-obvious observations, concrete data points, real problems solved), and presents 2–3 draft tweets tied to actual evidence from the log.

If the session was routine, Claude tells you plainly — no manufactured tweets.

### Grab a screenshot during work

```
/seed shot                          # interactive — cursor turns into camera, click target window
/seed shot https://example.com      # headless Chrome, 1280×800
/seed shot localhost:3000 --note "dashboard after latency fix"
```

The image lands in `state/sessions/{session_id}/shots/` and a `**📸 Shot**` marker gets appended to the session's log, so `/seed` synthesis can reference it when drafting.

### Other commands

- `/seed <one-line description>` — Manual capture (for things that happened outside Claude Code)
- `/seed done` — Archive the current session's log
- `/seed list` — List all session logs

## What the hook does NOT do

- ❌ Score / rank / filter turns — it's mechanical
- ❌ Call any LLM — zero cost, zero latency
- ❌ Upload anywhere — everything stays in `~/.claude/skills/seed/state/`

If you want judgment, that's what `/seed` invocation is for. The hook stays dumb by design.

## Platform

macOS (the `shot.py` interactive mode relies on `screencapture -w`). The hook itself is portable; URL-mode screenshots work anywhere Chrome is installed.

## License

MIT — see repository root.
