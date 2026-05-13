# Cursor adapter

Reads Cursor IDE chat history from per-workspace SQLite stores and emits
one EventV0 per chat bubble.

## Storage layout

Cursor (as of 2025–2026) keeps each workspace's state in:

```
~/Library/Application Support/Cursor/User/workspaceStorage/
└── <workspace_hash>/
    ├── workspace.json     ← {"folder": "file:///path/to/project"}
    └── state.vscdb        ← SQLite, ItemTable(key, value)
```

The chat data lives at key
`workbench.panel.aichat.view.aichat.chatdata` in `ItemTable`, as a
UTF-8 JSON blob with shape:

```json
{
  "tabs": [
    {
      "tabId": "...",
      "chatTitle": "...",
      "bubbles": [
        {"type": "user", "text": "..."},
        {"type": "ai",   "text": "..."}
      ]
    }
  ]
}
```

## Override storage root

For tests or non-default Cursor installs:

```bash
export CURSOR_STORAGE_ROOT=/path/to/workspaceStorage
```

Or in code:

```python
CursorAdapter(pool, storage_root=Path("/custom/path"))
```

## Cursor state across polls

The adapter cursor (stored in `~/.agent-seeds/state/cursors/cursor.json`)
tracks per-workspace per-tab high-water marks:

```json
{
  "workspaces": {
    "<workspace_hash>": {
      "tabs": {"<tab_id>": <next_bubble_idx>},
      "last_seen_total": <total_bubbles_at_last_poll>
    }
  }
}
```

`pollOnce` skips bubbles before the high-water mark and emits each new
bubble. Idempotent: re-running after no new activity emits 0 events.

## Action type mapping

| Bubble type | Action | Notes |
|---|---|---|
| `user` | `user_request` | Always |
| `ai` (non-last) | `agent_response` | Mid-conversation response |
| `ai` (last bubble) | `session_completed` | Triggers pool flush |

## Schema-drift handling

The adapter degrades gracefully on each level:

| Condition | Behavior |
|---|---|
| `state.vscdb` missing | Skip workspace, no log |
| SQLite open error | `logger.warning`, skip workspace |
| `ItemTable` query error | `logger.warning`, skip workspace |
| chatdata value not UTF-8 | `logger.warning`, skip workspace |
| chatdata not valid JSON | `logger.warning`, skip workspace |
| `tabs` key missing | `logger.warning`, skip workspace |
| Individual tab/bubble malformed | Silently skip the bubble |

Crashes never propagate to the rest of the poll cycle.

## Future-proofing

If Cursor changes its chat storage key, update `CHATDATA_KEY` in
`src/agentlog/adapters/cursor.py`. Consider adding fallback key probes
if multiple Cursor versions coexist.

## Privacy

Chat content (user prompts + assistant replies) is captured verbatim
into events. Treat the pool repo as private. The adapter sets
`event.privacy = {"level": "private", "redacted": False}` — downstream
consumers can filter on this if needed.
