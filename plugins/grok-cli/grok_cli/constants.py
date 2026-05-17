"""Constants for grok-cli.

The xAI OAuth defaults are derived from the public Hermes Agent implementation and
are intentionally kept in one place so users can override them if xAI changes the
login surface.
"""

from __future__ import annotations

APP_NAME = "grok-cli"
APP_DIR_NAME = ".grok-cli"

DEFAULT_XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_XAI_MODEL = "grok-4.3"
# Verified 2026-05-17 via `grok-cli models` on a SuperGrok/X Premium OAuth
# entitlement: the bare "grok-4.20-reasoning" id does not exist; the real id is
# the dated one below. LEGACY_SEARCH_MODEL is migrated away on config load.
DEFAULT_XAI_SEARCH_MODEL = "grok-4.20-0309-reasoning"
LEGACY_SEARCH_MODELS = ("grok-4.20-reasoning",)

# Grok Imagine generation models (verified available on X Premium OAuth).
DEFAULT_XAI_IMAGE_MODEL = "grok-imagine-image"
DEFAULT_XAI_VIDEO_MODEL = "grok-imagine-video"
# Endpoints (image = sync, video = async request_id + poll).
XAI_IMAGE_GENERATIONS_PATH = "/images/generations"
XAI_VIDEO_GENERATIONS_PATH = "/videos/generations"
XAI_VIDEO_STATUS_PATH = "/videos"  # GET /videos/{request_id}
VIDEO_POLL_INTERVAL_SECONDS = 6
VIDEO_POLL_TIMEOUT_SECONDS = 600
VIDEO_DONE_STATUSES = ("done", "completed", "succeeded", "failed", "error", "canceled")

DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_RETRIES = 2
DEFAULT_CONTEXT_MESSAGES = 20
DEFAULT_LOGIN_TIMEOUT_SECONDS = 180

# Public OAuth client used by Hermes Agent's SuperGrok OAuth flow.
# Not a secret; the CLI uses Authorization Code + PKCE.
XAI_OAUTH_ISSUER = "https://auth.x.ai"
XAI_OAUTH_DISCOVERY_URL = f"{XAI_OAUTH_ISSUER}/.well-known/openid-configuration"
XAI_OAUTH_CLIENT_ID = "b1a00492-073a-47ea-816f-4c329264a828"
XAI_OAUTH_SCOPE = "openid profile email offline_access grok-cli:access api:access"
XAI_OAUTH_REDIRECT_HOST = "127.0.0.1"
XAI_OAUTH_REDIRECT_PORT = 56121
XAI_OAUTH_REDIRECT_PATH = "/callback"
XAI_ACCESS_TOKEN_REFRESH_SKEW_SECONDS = 120

PROVIDER_OAUTH = "xai-oauth"
PROVIDER_API_KEY = "xai-api-key"

AUTH_FILE = "auth.json"
CONFIG_FILE = "config.json"
DB_FILE = "sessions.sqlite3"
