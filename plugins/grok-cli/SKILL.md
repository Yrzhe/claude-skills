---
name: grok-cli
description: Load when the user or an agent wants to use Grok/xAI locally with their own SuperGrok / X Premium account instead of a paid xAI API key — chat with Grok, generate images or videos with Grok Imagine, or search X/Twitter posts via Grok. Triggers on "用 Grok 聊天/问 Grok", "Grok 生成图片/视频", "grok imagine", "搜一下推特/X 上怎么说", "grok-cli ...", "log in to Grok with my X Premium", "Grok image/video generation", "search tweets with Grok". Uses browser OAuth (no API key needed); image/video generation is paid. Do NOT load for non-Grok LLMs or for the paid xAI API key SDK workflow.
---

# grok-cli

Use this skill when the user or an agent needs a local CLI wrapper around Grok/xAI with:

- Browser-based xAI / SuperGrok OAuth login using Authorization Code + PKCE.
- Optional `XAI_API_KEY` fallback.
- xAI `/v1/responses` chat calls.
- Grok Imagine image generation (sync) and video generation (async poll).
- X/Twitter search through xAI's server-side `x_search` Responses tool.
- Persistent local session history in SQLite.
- Multi-session switching, export, and summarization.

## Safety and credential rules

Never ask the user to paste their xAI password. Use `grok-cli login` to open the xAI authorization URL in a browser. Do not scrape browser cookies, automate `grok.com`, or capture interactive login credentials. OAuth tokens are stored locally under `~/.grok-cli/auth.json` with owner-only file permissions when supported by the OS.

Prefer OAuth for SuperGrok users. API keys are supported only as fallback through `XAI_API_KEY` or `grok-cli key set`.

Do not print access tokens, refresh tokens, API keys, or ID tokens. `grok-cli status` sanitizes credential output.

Image and video generation are **paid** xAI operations (≈ $0.02 / image,
≈ $0.40 / 8s video — video is ~20x an image). The CLI refuses paid generation
in non-interactive mode unless `--yes` is passed; never auto-pass `--yes` for an
agent without the user's intent. No credentials are bundled in this package —
each user logs in with their own SuperGrok / X Premium account via
`grok-cli login`.

## Installation

From the skill folder:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Smoke test without network:

```bash
grok-cli --help
grok-cli status
```

## Login

Local machine with browser:

```bash
grok-cli login
```

Remote SSH/container session:

```bash
# On your local machine, in a separate terminal:
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# On the remote host:
grok-cli login --no-browser
# Open the printed URL locally.
```

Alternative API key fallback:

```bash
export XAI_API_KEY="..."
# or store locally:
grok-cli key set
```

## Main commands

```bash
# Single-turn chat, saved to current/default session
grok-cli ask "What is the meaning of life?"

# Interactive chat
grok-cli chat -s research

# Image generation (Grok Imagine, sync) — paid, needs --yes
grok-cli image "a neon cyberpunk fox, sticker art" --yes -o fox.jpg -n 2

# Video generation (Grok Imagine, async poll) — paid ~20x an image, needs --yes
grok-cli video "a paper plane gliding over a city at sunset" --yes -o plane.mp4
grok-cli video --fetch <request_id> --json     # check an existing job

# X Search via Grok server-side x_search
grok-cli search "What are people on X saying about the latest xAI algorithm update?" --save

# Limit search to handles
grok-cli search "Grok image feature reactions" --allowed xai elonmusk --from 2026-05-01

# Enable image/video understanding for matching posts
grok-cli search "Show visual reactions to Grok features" --images --videos

# Sessions
grok-cli session new ai-market --use
grok-cli session list
grok-cli session use thesis
grok-cli session export ai-market -o ai-market.md

# Summarize long session for future compact context
grok-cli summarize -s ai-market
```

## Agent invocation contract

For Codex or another agent, call the CLI rather than importing internals unless you need a custom integration.

Preferred machine-readable calls:

```bash
grok-cli ask "<prompt>" --session "<session>" --json

grok-cli search "<query>" --allowed xai --from 2026-05-01 --json --save

grok-cli status
```

JSON responses include the response id, model, answer, citations, inline citations, status, and usage where available.

## Data layout

Default local state:

```text
~/.grok-cli/
  auth.json          # OAuth/API-key credential state, sanitized by status output
  config.json        # base_url, default_model, search_model, current_session
  sessions.sqlite3   # sessions, messages, citations, summaries
```

Set `GROK_CLI_HOME=/path/to/state` to isolate state for tests or a specific agent workspace.

## Implementation notes for agents

- `grok-cli login` uses the xAI OIDC discovery document and Authorization Code + PKCE.
- OAuth defaults are based on the public Hermes Agent implementation for `xai-oauth`.
- X Search is implemented by sending `tools: [{"type":"x_search"}]` to `/v1/responses`, matching Hermes' documented behavior.
- xAI's public Responses API documents `/v1/responses`, response ids, retrieval, deletion, and server-side response storage. This skill defaults to `store:false` for data-sovereignty reasons.
- If `x_search` returns a provider/model error, switch `search_model` to `grok-4.20-reasoning` or another model with x_search entitlement.

## Troubleshooting

- `No xAI credentials available`: run `grok-cli login`, set `XAI_API_KEY`, or use `grok-cli key set`.
- Login callback cannot connect on a remote host: forward local port 56121 to the remote host before opening the URL.
- `state_mismatch`: rerun login; do not reuse old authorization URLs.
- `invalid_grant` or refresh failure: run `grok-cli login` again.
- `x_search` not enabled for this model/account: verify that your SuperGrok account has access and try `grok-cli config set search_model grok-4.20-reasoning`.

## Source basis

This package is based on public behavior documented by Hermes Agent and xAI docs, not on private credentials or browser-cookie scraping. See `docs/sources.md` for references.
