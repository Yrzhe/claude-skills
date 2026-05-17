# grok-cli skill

`grok-cli` is a reusable skill package for other agents, especially coding agents such as Codex, that need local access to Grok chat and X Search without requiring a paid xAI API key.

The default path is browser OAuth login with an xAI / SuperGrok account. API key fallback is available but not required for normal use.

## What this includes

- `grok-cli login`: xAI OAuth Authorization Code + PKCE login.
- `grok-cli ask`: one-shot chat through xAI `/v1/responses`.
- `grok-cli chat`: interactive multi-session chat.
- `grok-cli search`: Grok-powered X Search via `x_search` server-side tool.
- `grok-cli image`: Grok Imagine image generation (sync), auto-downloads.
- `grok-cli video`: Grok Imagine video generation (async poll), auto-downloads.
- `grok-cli session ...`: local SQLite session management.
- `grok-cli summarize`: local session summary generation for compact long-context reuse.
- `grok-cli key set`: API key fallback.

## Install

```bash
cd grok-cli
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then:

```bash
grok-cli login
grok-cli ask "Hello Grok"
grok-cli search "What are people on X saying about Grok today?" --json
grok-cli image "a neon cyberpunk fox, sticker art" --yes -o fox.jpg
grok-cli video "a paper plane gliding over a city at sunset" --yes -o plane.mp4
```

Image and video generation cost real money (≈ $0.02 / image, ≈ $0.40 / 8s
video). They require `--yes` (or interactive confirmation); non-interactive
callers must pass `--yes` explicitly.

## Architecture

```text
CLI commands
  -> AuthManager
       -> OAuth PKCE login / token refresh / API key fallback
  -> XaiClient
       -> POST /v1/responses
       -> POST /v1/responses + tools:[{type:x_search}]
  -> SessionStore
       -> SQLite sessions/messages/citations/summaries
```

## Important limitation

This package cannot grant access your xAI account does not already have. It can log you in and send the same style of OAuth bearer request that Hermes documents, but `x_search` availability still depends on the account, subscription, model, and xAI-side entitlement.
