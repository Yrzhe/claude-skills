agentlog-adapter-design

# agentlog adapter design v0

## Scope

Adapter layer owns Activity schema, source adapters, notable/noise filtering, and `pool.append(activity)` emission. It does not own `pool.jsonl` storage, GitHub sync, CLI commands, or recap prompts.

## Unified Activity schema

All adapters emit one object before calling `pool.append(activity)`.

| field | type | required | meaning |
| --- | --- | --- | --- |
| `schema_version` | string | yes | initial value `agentlog.activity.v0` |
| `activity_id` | string | yes | deterministic id, usually `${source_type}:${source_event_id}` |
| `source_type` | enum string | yes | `claude_code` / `codex` / `maestri` / `browser_use` |
| `source_event_id` | string | yes | stable source-local id for dedupe and cursor recovery |
| `actor` | object | yes | `{ id: string, display_name: string, kind: "human" | "agent" | "system" }` |
| `project` | object | yes | `{ id?: string, name: string, path?: string }` |
| `timestamp` | ISO-8601 string | yes | source event time; ingest fallback marked in `payload.timestamp_source` |
| `action_type` | enum string | yes | normalized category listed below |
| `summary` | string | yes | one-line summary, max 240 chars |
| `payload` | object | yes | source-specific structured details, trimmed |
| `artifact_refs` | array | yes | zero or more external refs; empty array allowed |
| `session` | object | no | `{ id: string, title?: string, cwd?: string }` |
| `parent_activity_id` | string | no | relation to earlier activity when known |
| `tags` | string[] | no | adapter tags, e.g. `code`, `note`, `browser`, `error` |

`artifact_refs[]`:

| field | type | required | meaning |
| --- | --- | --- | --- |
| `kind` | enum string | yes | `file`, `url`, `note`, `screenshot`, `terminal`, `repo`, `diff`, `unknown` |
| `uri` | string | yes | path, URL, note name, or source URI |
| `title` | string | no | display label |
| `mime_type` | string | no | known content type |
| `metadata` | object | no | line numbers, byte ranges, git commit, tool id |

`action_type` enum:

- `session_started`
- `session_completed`
- `user_request`
- `agent_response`
- `tool_call`
- `tool_result`
- `file_changed`
- `command_run`
- `note_created`
- `note_updated`
- `message_sent`
- `browser_step`
- `error`
- `checkpoint`

## Notable activity rules

Emit when:

- user gives a new task or changes scope
- agent completes a task, creates a report/design, or declares a blocker
- file, note, browser session, screenshot, command, or external message is created/changed/sent
- command/tool result affects progress: tests, build, git, deploy, package install, API call, Maestri operation, browser action
- error blocks progress or changes the plan
- session starts/completes with enough context to anchor later events

Suppress:

- token streaming chunks and partial assistant deltas
- hidden reasoning, planner-only state, UI heartbeat, cursor movement
- repeated identical progress lines without final result
- shell prompts, blank output, ANSI/control noise
- filesystem reads with no decision value unless used as deliverable evidence
- assistant acknowledgements with no new action/result
- duplicates already emitted by `source_event_id`

Size limits:

- `summary`: 240 chars
- `payload.text_excerpt`: 2,000 chars
- command stdout/stderr excerpt: last 4,000 chars plus `{ truncated: true }`
- file/note content goes in `artifact_refs`; payload only stores excerpt

## SourceAdapter interface

```ts
type AdapterCursor = Record<string, unknown>;

type SourceAdapter = {
  sourceType: Activity["source_type"];
  loadCursor(): Promise<AdapterCursor>;
  discover(cursor: AdapterCursor): Promise<SourceEvent[]>;
  normalize(event: SourceEvent): Promise<Activity | null>;
  append(activity: Activity): Promise<void>; // pool.append(activity)
  saveCursor(cursor: AdapterCursor): Promise<void>;
  pollOnce(): Promise<{ emitted: number; skipped: number; cursor: AdapterCursor }>;
};
```

Cursor files live at `~/.agent-seeds/adapter-state/{source_type}.json`. Cursor writes are atomic. Cursor advances only after successful `pool.append(activity)`. Every adapter uses deterministic `activity_id` plus a recent seen-id set; pool may dedupe again but adapter does not depend on it.

## ClaudeCodeAdapter

### Source

- `source_type`: `claude_code`
- mode: pull
- read path: `~/.claude/projects/*/*.jsonl`
- session id: JSONL basename without `.jsonl`
- project path: derive from Claude escaped project directory name, e.g. `-Users-renzheyu-...`

### Cursor

Cursor file: `~/.agent-seeds/adapter-state/claude_code.json`

```json
{
  "files": {
    "/Users/renzheyu/.claude/projects/<project>/<session>.jsonl": {
      "inode": 123,
      "mtime_ns": 123456789,
      "size": 98765,
      "offset": 98765,
      "line_index": 120,
      "last_event_id": "<uuid-or-line-index>"
    }
  }
}
```

Strategy:

- scan glob every poll
- known file: seek from `offset`
- new file: parse from 0
- if size shrinks or inode changes: rescan from 0 with activity-id dedupe
- source event id: source `uuid`/`message.id` when present, else `${file_path}:${line_index}`

### Mapping

Emit:

- user message -> `user_request`
- substantial/final assistant message -> `agent_response`
- Bash/Edit/Write/MultiEdit/Notebook/Read tool use when notable -> `tool_call`
- non-empty/error/file-mutating tool result -> `tool_result`
- explicit stop/session summary -> `session_completed`
- seed recap/hook event if present -> `checkpoint`

Noise filter:

- suppress assistant messages below 20 chars unless error/blocker/completion
- suppress Read/Grep/LS unless error or cited in final deliverable
- suppress token/accounting events
- collapse consecutive Bash stdout chunks into one result
- ignore `/tests/eval-` fixture sessions unless `--include-eval`

Push frequency:

- active poll: every 30 seconds
- immediate flush on session completion/Stop hook integration
- backfill: batches of 500 activities

## CodexAdapter

### Source

- `source_type`: `codex`
- mode: pull
- read paths:
  - primary: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`
  - archive backfill: `~/.codex/archived_sessions/rollout-*.jsonl`
- event types: `session_meta`, `turn_context`, `event_msg`, `response_item`, tool calls, tool outputs

### Cursor

Cursor file: `~/.agent-seeds/adapter-state/codex.json`

```json
{
  "roots": {
    "/Users/renzheyu/.codex/sessions": { "last_scan_at": "2026-05-12T14:00:00Z" },
    "/Users/renzheyu/.codex/archived_sessions": { "last_scan_at": "2026-05-12T14:00:00Z" }
  },
  "files": {
    "/Users/renzheyu/.codex/sessions/2026/05/12/rollout-...jsonl": {
      "inode": 456,
      "mtime_ns": 123456789,
      "size": 54321,
      "offset": 54321,
      "line_index": 88,
      "session_id": "019..."
    }
  }
}
```

Strategy:

- scan today's path every poll
- scan full `~/.codex/sessions` tree every 10 minutes
- scan archive hourly or explicit backfill
- source event id: response item id when present, else `${session_id}:${line_index}:${event_type}`
- session id: `session_meta.payload.id`
- project/cwd: `turn_context` when present, else inferred from payload text or configured fallback

### Mapping

Emit:

- user message response item -> `user_request`
- assistant final text/message -> `agent_response`
- phase/blocker/completion `event_msg` -> `checkpoint`
- shell/tool execution request -> `tool_call`
- shell/tool output/error/exit code -> `command_run` or `tool_result`
- `apply_patch`/file edit result -> `file_changed`
- final assistant close-out -> `session_completed`

Noise filter:

- suppress progress-only `event_msg` unless 30+ seconds since last checkpoint or contains blocker/result
- suppress raw reasoning and hidden fields
- suppress empty tool outputs and uncited successful directory listings
- collapse repeated wait/poll outputs
- do not emit memory citation blocks as standalone activities

Push frequency:

- active poll: every 20 seconds for today's files
- full tree: every 10 minutes
- archive: hourly or explicit backfill
- immediate flush after final assistant response

## MaestriAdapter

### Source

- `source_type`: `maestri`
- mode: pull via CLI
- commands:
  - `maestri list` discovers connected agents/notes
  - `maestri check "<Agent Name>"` reads connected agent terminal output
  - `maestri note read "<Note Name>"` snapshots shared notes
- read path: none assumed; Maestri canvas is accessed through CLI
- OPEN: replace terminal/note scraping if Maestri exposes stable local event API

### Cursor

Cursor file: `~/.agent-seeds/adapter-state/maestri.json`

```json
{
  "agents": {
    "总管": {
      "last_seen_hash": "sha256:...",
      "last_seen_lines": 180,
      "last_checked_at": "2026-05-12T14:00:00Z"
    }
  },
  "notes": {
    "agentlog-spec-v0": {
      "last_seen_hash": "sha256:...",
      "last_seen_lines": 40,
      "last_checked_at": "2026-05-12T14:00:00Z"
    }
  }
}
```

Strategy:

- run `maestri list` each poll
- hash normalized `maestri check` output per agent
- hash normalized note body per note after stripping line numbers
- on hash change, diff from previous tail and emit meaningful new blocks
- source event id: `maestri:agent:${agent_name}:${sha256(new_block)}` or `maestri:note:${note_name}:${sha256(note_body)}`

### Mapping

Emit:

- new connected agent -> `session_started`
- terminal completion/blocker/ask response -> `agent_response` or `checkpoint`
- first-seen note -> `note_created`
- note hash change -> `note_updated`
- visible local `maestri ask` send -> `message_sent`

Noise filter:

- suppress unchanged hashes
- strip note-read line numbers before hashing
- suppress spinners, repeated prompts, shell PS1, blank lines
- suppress check output that only repeats previous tail
- collapse long terminal deltas unless note/file/message artifact appears

Push frequency:

- active canvas poll: every 60 seconds
- delegated agent high-attention poll: every 15 seconds for that agent
- note poll: every 2 minutes; if changed, every 30 seconds for next 5 minutes

## BrowserUseAdapter

### Source

- `source_type`: `browser_use`
- mode: pull via MCP/tool API
- API: `mcp__browser-use__get_session_messages(session_id)`
- read path: none; messages come from browser-use cloud/MCP
- OPEN: exact active-session discovery API; v0 can require configured session ids

### Cursor

Cursor file: `~/.agent-seeds/adapter-state/browser_use.json`

```json
{
  "sessions": {
    "<browser_use_session_id>": {
      "last_seen_message_id": "msg_...",
      "last_seen_index": 42,
      "last_seen_at": "2026-05-12T14:00:00Z",
      "last_url": "https://example.com"
    }
  }
}
```

Strategy:

- session ids come from config until discovery exists
- call `get_session_messages(session_id)` each poll
- process messages after `last_seen_message_id`; fallback to index if ids absent
- source event id: `browser_use:${session_id}:${message_id || index}`
- extract URLs, screenshots, DOM snapshots, downloads into `artifact_refs`

### Mapping

Emit:

- navigation to new URL/domain -> `browser_step`
- form submit, important click, upload/download -> `browser_step`
- screenshot produced -> `browser_step` with screenshot ref
- task completion/failure -> `agent_response` or `error`
- externally visible action attempt/result -> `tool_call` then `tool_result` when available

Noise filter:

- suppress low-level DOM dumps unless error or final extraction result
- suppress repeated page state with same URL and visible-text hash
- suppress mouse movement, scroll-only steps, viewport resize unless tied to extraction/completion
- collapse click/type/navigation sequence under 5 seconds on same target URL
- redact password/token field values; keep field names only

Push frequency:

- active session: every 15 seconds
- idle session: every 2 minutes
- immediate flush on completed/failed message
- backoff to 5 minutes after 3 unchanged polls

## Cross-adapter project attribution

Order:

1. explicit cwd/session/project field
2. path from log root, terminal cwd, or note title context
3. nearest git repository root for cwd
4. configured fallback project name
5. `project.name = "unknown"`, `payload.project_source = "unknown"`

Project id:

- local: `sha256(normalized_project_path || project_name)`
- remote-only BrowserUse: `sha256(session_origin_domain || configured_project_name)`

## Privacy and payload rules

- never store full env dumps
- redact token/password/API key values
- store file paths and note names as refs; do not inline whole files/notes
- store command output excerpts only with exit code and truncation flag
- redact URL query params named `token`, `key`, `secret`, `code`, `password`

## Failure behavior

- parse error on one line/message emits one `error` activity, then continues
- source unavailable is local health state; append only if outage lasts beyond 5 minutes
- cursor save failure stops adapter before more appends
- pool append failure does not advance cursor

## OPEN

- BrowserUse active-session discovery API
- Maestri stable event/source API beyond `list`, `check`, note reads
- final `action_type` enum alignment with Pool Architect schema
- exact max payload size if Pool Architect sets stricter limits
