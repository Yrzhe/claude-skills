# grok-cli architecture

## Goal

Provide a local, agent-callable command-line wrapper around xAI/Grok that supports browser OAuth login, API key fallback, X Search, persistent context, and multiple sessions.

## Components

### AuthManager

File: `grok_cli/auth.py`

Responsibilities:

- Fetch xAI OIDC discovery metadata.
- Generate OAuth PKCE verifier/challenge/state.
- Start a local loopback callback server.
- Open or print the authorization URL.
- Exchange authorization code for tokens.
- Refresh access tokens before expiry.
- Fall back to `XAI_API_KEY` or a stored API key.
- Sanitize credential status output.

### XaiClient

File: `grok_cli/client.py`

Responsibilities:

- Resolve bearer credentials via `AuthManager`.
- Call xAI `/v1/responses`.
- Retry transient failures.
- Refresh OAuth token reactively on 401.
- Extract answer text and citations.
- Provide `x_search()` wrapper around `tools: [{"type":"x_search"}]`.
- `generate_image()` — synchronous `POST /images/generations`.
- `generate_video()` / `get_video()` / `wait_video()` — async video job
  submit + poll loop. `download_url()` streams generated assets to disk.

### SessionStore

File: `grok_cli/sessions.py`

Responsibilities:

- Maintain SQLite database.
- Store sessions, messages, citations, and summaries.
- Build compact model input from system prompt, latest summary, recent messages, and current user prompt.
- Export sessions to Markdown.

### CLI

File: `grok_cli/cli.py`

Agent-facing commands:

- `login`, `logout`, `status`, `refresh`
- `key set`
- `ask`, `chat`, `search`, `image`, `video`, `models`, `summarize`
- `session new/use/list/delete/export/show`
- `config get/set`

## Default storage

```text
~/.grok-cli/
  auth.json
  config.json
  sessions.sqlite3
```

Override with:

```bash
export GROK_CLI_HOME=/absolute/path
```

## Response storage policy

The tool defaults to local-first persistence and sends `store:false` to xAI unless `--server-store` is explicitly used. This avoids relying on xAI server-side retention for multi-session memory.
