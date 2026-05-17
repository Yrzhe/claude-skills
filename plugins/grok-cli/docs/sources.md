# Sources and basis

This package was built from public docs and public open-source behavior.

## Hermes Agent docs

Hermes documents that X Search is backed by xAI's built-in `x_search` tool on the Responses API at `https://api.x.ai/v1/responses`, and that the tool returns synthesized results with citations to originating posts.

Hermes documents two credential paths for X Search:

- SuperGrok OAuth through browser login.
- `XAI_API_KEY`.

It also documents parameters such as `allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`, `enable_image_understanding`, and `enable_video_understanding`.

## Hermes Agent source

The public Hermes source contains the xAI OAuth provider constants:

- Provider ID: `xai-oauth`
- OAuth issuer/discovery URL around `auth.x.ai`
- Public OAuth client id
- Scope: `openid profile email offline_access grok-cli:access api:access`
- Loopback callback: `127.0.0.1:56121/callback`

The public Hermes source also contains an `x_search_tool.py` implementation that:

- Resolves OAuth or API-key credentials.
- Sends `POST {base_url}/responses`.
- Uses `tools: [{"type":"x_search"}]`.
- Parses top-level citations and inline `url_citation` annotations.

## xAI docs

xAI's public REST docs describe `/v1/responses`, response IDs, response retrieval/deletion, `store`, and examples for `https://api.x.ai/v1/responses`.

## Grok Imagine generation (verified empirically 2026-05-17)

Generation behavior was confirmed by a live entitlement test on a real
SuperGrok / X Premium OAuth session (not from private docs):

- `GET /v1/models` on this entitlement lists `grok-imagine-image`,
  `grok-imagine-image-quality`, `grok-imagine-video`.
- Image: `POST /v1/images/generations` `{model, prompt, n}` → synchronous,
  returns `{data:[{url,mime_type}], usage:{cost_in_usd_ticks}}`.
- Video: `POST /v1/videos/generations` `{model, prompt}` → `{request_id}`;
  poll `GET /v1/videos/{request_id}` → `{status, progress}`, and on
  completion `{status:"done", video:{url,duration,respect_moderation}, usage}`.
- `cost_in_usd_ticks` observed: image ≈ 2e8, 8s video ≈ 4e9
  (≈ 1e10 ticks per USD → image ≈ $0.02, video ≈ $0.40).
- The `images/generations` endpoint rejects the video model with a clear
  "use /v1/videos/generations" error, confirming the endpoint split.

## Important mismatch

xAI public docs may not list `x_search` as a generally available tool in every public API surface. Hermes documents it as available through the xAI/Grok OAuth and eligible models. Treat `x_search` and Grok Imagine generation as account/model/entitlement-dependent.
