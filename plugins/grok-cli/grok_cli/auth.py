"""xAI OAuth and API-key credential management for grok-cli.

This module implements a browser-based OAuth 2.0 Authorization Code + PKCE flow
against xAI's public OIDC discovery document. It intentionally avoids browser
cookie scraping and webpage automation.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import requests

from .constants import (
    DEFAULT_LOGIN_TIMEOUT_SECONDS,
    DEFAULT_XAI_BASE_URL,
    PROVIDER_API_KEY,
    PROVIDER_OAUTH,
    XAI_ACCESS_TOKEN_REFRESH_SKEW_SECONDS,
    XAI_OAUTH_CLIENT_ID,
    XAI_OAUTH_DISCOVERY_URL,
    XAI_OAUTH_REDIRECT_HOST,
    XAI_OAUTH_REDIRECT_PATH,
    XAI_OAUTH_REDIRECT_PORT,
    XAI_OAUTH_SCOPE,
)
from .paths import auth_path, write_private_text


class AuthError(RuntimeError):
    pass


@dataclass
class Bearer:
    token: str
    provider: str
    base_url: str = DEFAULT_XAI_BASE_URL


class _CallbackState:
    def __init__(self, expected_state: str) -> None:
        self.expected_state = expected_state
        self.code: str | None = None
        self.error: str | None = None
        self.description: str | None = None
        self.received_state: str | None = None
        self.event = threading.Event()


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    callback_state: _CallbackState

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - stdlib name
        return

    def do_GET(self) -> None:  # noqa: N802 - stdlib name
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != XAI_OAUTH_REDIRECT_PATH:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        params = urllib.parse.parse_qs(parsed.query)
        state = params.get("state", [""])[0]
        self.callback_state.received_state = state

        if state != self.callback_state.expected_state:
            self.callback_state.error = "state_mismatch"
            self.callback_state.description = "OAuth state mismatch; possible CSRF or stale login URL."
        elif "error" in params:
            self.callback_state.error = params.get("error", ["oauth_error"])[0]
            self.callback_state.description = params.get("error_description", [""])[0]
        else:
            self.callback_state.code = params.get("code", [""])[0] or None
            if not self.callback_state.code:
                self.callback_state.error = "missing_code"
                self.callback_state.description = "OAuth callback did not include an authorization code."

        self.callback_state.event.set()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        body = """
<!doctype html>
<html><head><title>grok-cli login</title></head>
<body style="font-family: system-ui, sans-serif; margin: 2rem;">
<h1>grok-cli login received</h1>
<p>You can close this browser tab and return to your terminal.</p>
</body></html>
""".strip()
        self.wfile.write(body.encode("utf-8"))


class AuthManager:
    def __init__(self) -> None:
        self.path = auth_path()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "providers": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"version": 1, "providers": {}}
        if not isinstance(data, dict):
            return {"version": 1, "providers": {}}
        data.setdefault("version", 1)
        data.setdefault("providers", {})
        return data

    def _save(self, data: dict[str, Any]) -> None:
        data["updated_at"] = int(time.time())
        write_private_text(self.path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def discovery(self) -> dict[str, Any]:
        try:
            r = requests.get(XAI_OAUTH_DISCOVERY_URL, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            raise AuthError(f"Failed to fetch xAI OIDC discovery document: {exc}") from exc
        if not isinstance(data, dict):
            raise AuthError("xAI OIDC discovery document was not a JSON object")
        for key in ("authorization_endpoint", "token_endpoint"):
            if not data.get(key):
                raise AuthError(f"xAI OIDC discovery document missing {key}")
        return data

    @staticmethod
    def _pkce_verifier() -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(48)).decode("ascii").rstrip("=")

    @staticmethod
    def _pkce_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    @staticmethod
    def _redirect_uri(port: int = XAI_OAUTH_REDIRECT_PORT) -> str:
        return f"http://{XAI_OAUTH_REDIRECT_HOST}:{port}{XAI_OAUTH_REDIRECT_PATH}"

    def login(
        self,
        *,
        no_browser: bool = False,
        port: int = XAI_OAUTH_REDIRECT_PORT,
        timeout_seconds: int = DEFAULT_LOGIN_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        discovery = self.discovery()
        authorization_endpoint = str(discovery["authorization_endpoint"])
        token_endpoint = str(discovery["token_endpoint"])

        state = secrets.token_urlsafe(32)
        verifier = self._pkce_verifier()
        challenge = self._pkce_challenge(verifier)
        redirect_uri = self._redirect_uri(port)

        callback_state = _CallbackState(expected_state=state)
        handler_cls = type("OAuthCallbackHandler", (_OAuthCallbackHandler,), {})
        handler_cls.callback_state = callback_state
        try:
            server = HTTPServer((XAI_OAUTH_REDIRECT_HOST, port), handler_cls)
        except OSError as exc:
            raise AuthError(
                f"Could not bind OAuth callback server at {redirect_uri}. "
                f"Try --port with a free local port. Error: {exc}"
            ) from exc

        def serve_once() -> None:
            server.timeout = max(1, timeout_seconds)
            while not callback_state.event.is_set():
                server.handle_request()

        thread = threading.Thread(target=serve_once, daemon=True)
        thread.start()

        query = {
            "client_id": XAI_OAUTH_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": XAI_OAUTH_SCOPE,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        url = f"{authorization_endpoint}?{urllib.parse.urlencode(query)}"

        print("Open this URL to log in with your xAI / SuperGrok account:\n")
        print(url)
        print()
        if not no_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass

        if not callback_state.event.wait(timeout_seconds):
            raise AuthError(
                f"Authorization timed out after {timeout_seconds} seconds. "
                "Run login again. For remote hosts, forward the callback port."
            )
        if callback_state.error:
            raise AuthError(f"OAuth callback failed: {callback_state.error} {callback_state.description or ''}")
        if not callback_state.code:
            raise AuthError("OAuth callback did not return a code")

        token_data = self._exchange_code(
            token_endpoint=token_endpoint,
            code=callback_state.code,
            redirect_uri=redirect_uri,
            verifier=verifier,
        )
        state_payload = self._normalize_token_state(token_data, token_endpoint=token_endpoint)
        auth_store = self._load()
        auth_store.setdefault("providers", {})[PROVIDER_OAUTH] = state_payload
        auth_store["active_provider"] = PROVIDER_OAUTH
        self._save(auth_store)
        return state_payload

    def _exchange_code(self, *, token_endpoint: str, code: str, redirect_uri: str, verifier: str) -> dict[str, Any]:
        body = {
            "grant_type": "authorization_code",
            "client_id": XAI_OAUTH_CLIENT_ID,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        }
        r = requests.post(token_endpoint, data=body, timeout=60)
        try:
            r.raise_for_status()
        except requests.HTTPError as exc:
            raise AuthError(f"Token exchange failed: {self._safe_error(r)}") from exc
        data = r.json()
        if not isinstance(data, dict) or not data.get("access_token"):
            raise AuthError("Token exchange response did not include access_token")
        return data

    def _refresh(self, state: dict[str, Any]) -> dict[str, Any]:
        refresh_token = state.get("refresh_token")
        token_endpoint = state.get("token_endpoint")
        if not refresh_token:
            raise AuthError("OAuth refresh_token is missing; run `grok-cli login` again")
        if not token_endpoint:
            token_endpoint = self.discovery()["token_endpoint"]
        body = {
            "grant_type": "refresh_token",
            "client_id": XAI_OAUTH_CLIENT_ID,
            "refresh_token": refresh_token,
        }
        r = requests.post(str(token_endpoint), data=body, timeout=60)
        try:
            r.raise_for_status()
        except requests.HTTPError as exc:
            raise AuthError(f"Token refresh failed: {self._safe_error(r)}") from exc
        data = r.json()
        if not isinstance(data, dict) or not data.get("access_token"):
            raise AuthError("Token refresh response did not include access_token")
        if not data.get("refresh_token"):
            data["refresh_token"] = refresh_token
        return self._normalize_token_state(data, token_endpoint=str(token_endpoint))

    @staticmethod
    def _normalize_token_state(token_data: dict[str, Any], *, token_endpoint: str) -> dict[str, Any]:
        now = int(time.time())
        expires_in = int(token_data.get("expires_in") or 3600)
        return {
            "provider": PROVIDER_OAUTH,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "id_token": token_data.get("id_token"),
            "token_type": token_data.get("token_type", "Bearer"),
            "scope": token_data.get("scope", XAI_OAUTH_SCOPE),
            "expires_at": now + expires_in,
            "token_endpoint": token_endpoint,
            "base_url": DEFAULT_XAI_BASE_URL,
            "updated_at": now,
        }

    @staticmethod
    def _safe_error(response: requests.Response) -> str:
        try:
            payload = response.json()
            return json.dumps(payload, ensure_ascii=False)[:1000]
        except Exception:
            return response.text[:1000]

    def get_oauth_state(self) -> dict[str, Any] | None:
        data = self._load()
        state = data.get("providers", {}).get(PROVIDER_OAUTH)
        return dict(state) if isinstance(state, dict) else None

    def get_oauth_bearer(self, *, refresh: bool = True) -> Bearer | None:
        data = self._load()
        state = data.get("providers", {}).get(PROVIDER_OAUTH)
        if not isinstance(state, dict) or not state.get("access_token"):
            return None
        expires_at = int(state.get("expires_at") or 0)
        if refresh and expires_at <= int(time.time()) + XAI_ACCESS_TOKEN_REFRESH_SKEW_SECONDS:
            new_state = self._refresh(state)
            data.setdefault("providers", {})[PROVIDER_OAUTH] = new_state
            data["active_provider"] = PROVIDER_OAUTH
            self._save(data)
            state = new_state
        return Bearer(
            token=str(state["access_token"]),
            provider=PROVIDER_OAUTH,
            base_url=str(state.get("base_url") or DEFAULT_XAI_BASE_URL).rstrip("/"),
        )

    def set_api_key(self, api_key: str) -> None:
        api_key = api_key.strip()
        if not api_key:
            raise AuthError("API key is empty")
        data = self._load()
        data.setdefault("providers", {})[PROVIDER_API_KEY] = {
            "provider": PROVIDER_API_KEY,
            "api_key": api_key,
            "base_url": DEFAULT_XAI_BASE_URL,
            "updated_at": int(time.time()),
        }
        if not data.get("active_provider"):
            data["active_provider"] = PROVIDER_API_KEY
        self._save(data)

    def get_api_key_bearer(self) -> Bearer | None:
        env_key = os.environ.get("XAI_API_KEY", "").strip()
        if env_key:
            return Bearer(token=env_key, provider="xai-env-api-key", base_url=os.environ.get("XAI_BASE_URL", DEFAULT_XAI_BASE_URL).rstrip("/"))
        data = self._load()
        state = data.get("providers", {}).get(PROVIDER_API_KEY)
        if isinstance(state, dict) and state.get("api_key"):
            return Bearer(
                token=str(state["api_key"]),
                provider=PROVIDER_API_KEY,
                base_url=str(state.get("base_url") or DEFAULT_XAI_BASE_URL).rstrip("/"),
            )
        return None

    def get_bearer(self, *, prefer_oauth: bool = True) -> Bearer:
        if prefer_oauth:
            oauth = self.get_oauth_bearer(refresh=True)
            if oauth:
                return oauth
            api = self.get_api_key_bearer()
            if api:
                return api
        else:
            api = self.get_api_key_bearer()
            if api:
                return api
            oauth = self.get_oauth_bearer(refresh=True)
            if oauth:
                return oauth
        raise AuthError("No xAI credentials available. Run `grok-cli login` or set XAI_API_KEY.")

    def refresh_now(self) -> dict[str, Any]:
        data = self._load()
        state = data.get("providers", {}).get(PROVIDER_OAUTH)
        if not isinstance(state, dict):
            raise AuthError("No OAuth state found; run `grok-cli login` first")
        new_state = self._refresh(state)
        data.setdefault("providers", {})[PROVIDER_OAUTH] = new_state
        data["active_provider"] = PROVIDER_OAUTH
        self._save(data)
        return new_state

    def logout(self, provider: str | None = None) -> None:
        data = self._load()
        providers = data.setdefault("providers", {})
        if provider:
            providers.pop(provider, None)
        else:
            providers.clear()
        if provider is None or data.get("active_provider") == provider:
            data["active_provider"] = None
        self._save(data)

    def status(self) -> dict[str, Any]:
        data = self._load()
        providers = data.get("providers", {}) if isinstance(data.get("providers"), dict) else {}
        out: dict[str, Any] = {
            "auth_file": str(self.path),
            "active_provider": data.get("active_provider"),
            "providers": {},
            "env_xai_api_key": bool(os.environ.get("XAI_API_KEY")),
        }
        for provider, state in providers.items():
            if not isinstance(state, dict):
                continue
            sanitized = {k: v for k, v in state.items() if k not in {"access_token", "refresh_token", "id_token", "api_key"}}
            if "expires_at" in sanitized:
                sanitized["expires_in_seconds"] = int(sanitized["expires_at"]) - int(time.time())
            out["providers"][provider] = sanitized
        return out
