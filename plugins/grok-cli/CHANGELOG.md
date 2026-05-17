# Changelog

All notable changes to `grok-cli` are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] - 2026-05-17

### Added
- `grok-cli image "<prompt>"` — synchronous image generation via Grok Imagine
  (`POST /v1/images/generations`, model `grok-imagine-image`). Flags:
  `--model`, `-n/--count` (1–10), `-o/--output`, `--no-download`, `--yes`,
  `--json`. Downloads results locally; prints approximate USD cost.
- `grok-cli video "<prompt>"` — asynchronous video generation via Grok Imagine
  (`POST /v1/videos/generations` → `GET /v1/videos/{request_id}`, model
  `grok-imagine-video`). Flags: `--fetch <request_id>`, `--model`, `-o/--output`,
  `--no-wait`, `--no-download`, `--poll-interval`, `--poll-timeout`, `--yes`,
  `--json`. Polls to completion, downloads the mp4.
- Paid-action guard `_confirm_paid`: image/video generation cost real money;
  requires `--yes` (or interactive confirmation). Non-interactive callers
  (agents) MUST pass `--yes` — refuses otherwise to prevent silent spend.
- `client.generate_image / generate_video / get_video / wait_video` and a
  streaming `download_url` helper.
- `usd_from_ticks` — approximate USD from xAI `cost_in_usd_ticks`
  (~1e10 ticks ≈ $1; verified: image ≈ $0.02, 8s video ≈ $0.40).
- Config fields `image_model`, `video_model`.
- Offline tests for subcommands, cost conversion, mime→ext, config migration.

### Fixed
- **`search_model` default was an invalid model id.** `grok-4.20-reasoning`
  does not exist on the X Premium / SuperGrok OAuth entitlement; the real id is
  `grok-4.20-0309-reasoning`. Default corrected and existing on-disk configs
  carrying the legacy value are auto-migrated on load.

### Verified (2026-05-17, real X Premium OAuth session)
- `grok-cli models` lists `grok-imagine-image`, `grok-imagine-image-quality`,
  `grok-imagine-video` as available on this entitlement.
- Image generation: synchronous, returns `data:[{url,mime_type}]`. Verified
  end-to-end (1408x768 JPEG downloaded).
- Video generation: async; `POST` returns `{request_id}`, status at
  `GET /v1/videos/{request_id}` (`{status, progress}` → on done
  `{video:{url,duration}, usage}`). Verified end-to-end (8s mp4).

### Notes for the public-share build
- No credentials are embedded anywhere in the package. Auth is per-user OAuth
  (`grok-cli login`), tokens live only in each user's `~/.grok-cli/auth.json`.
  The shareable zip is credential-free by construction; recipients run
  `grok-cli login` against their own SuperGrok / X Premium account.

## [0.1.0]

### Added
- Initial: OAuth PKCE login, API-key fallback, `/v1/responses` chat
  (`ask`/`chat`), `x_search`, SQLite sessions, `summarize`.
