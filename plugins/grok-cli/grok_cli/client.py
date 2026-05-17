"""xAI Responses API client and X Search wrapper."""

from __future__ import annotations

import json
import time
from typing import Any, Iterable

import requests

from .auth import AuthError, AuthManager, Bearer
from .config import Config, load_config
from .constants import (
    VIDEO_DONE_STATUSES,
    VIDEO_POLL_INTERVAL_SECONDS,
    VIDEO_POLL_TIMEOUT_SECONDS,
    XAI_IMAGE_GENERATIONS_PATH,
    XAI_VIDEO_GENERATIONS_PATH,
    XAI_VIDEO_STATUS_PATH,
)

# Approximate: xAI reports usage as `cost_in_usd_ticks`; ~1e10 ticks ≈ 1 USD
# (verified 2026-05-17: image ≈ 2e8 ticks ≈ $0.02, 8s video ≈ 4e9 ≈ $0.40).
USD_TICKS_PER_USD = 10_000_000_000


def usd_from_ticks(ticks: Any) -> float | None:
    try:
        return round(float(ticks) / USD_TICKS_PER_USD, 4)
    except (TypeError, ValueError):
        return None


def download_url(url: str, dest: str, *, timeout: int = 300) -> str:
    """Stream a generated-asset URL to a local file. Returns the path."""
    from pathlib import Path

    if not url:
        raise XaiClientError("no asset url to download")
    p = Path(dest).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(p, "wb") as fh:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    fh.write(chunk)
    return str(p)


class XaiClientError(RuntimeError):
    pass


class XaiClient:
    def __init__(self, auth: AuthManager | None = None, config: Config | None = None) -> None:
        self.auth = auth or AuthManager()
        self.config = config or load_config()

    def _bearer(self) -> Bearer:
        return self.auth.get_bearer(prefer_oauth=self.config.prefer_oauth)

    @staticmethod
    def _error_text(response: requests.Response) -> str:
        try:
            return json.dumps(response.json(), ensure_ascii=False)[:1200]
        except Exception:
            return response.text[:1200]

    def request(self, method: str, path: str, *, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        bearer = self._bearer()
        url = f"{bearer.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {bearer.token}",
            "Content-Type": "application/json",
            "User-Agent": "grok-cli-skill/0.1",
        }
        max_retries = max(0, int(self.config.retries))
        timeout = max(30, int(self.config.timeout_seconds))
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                resp = requests.request(method, url, headers=headers, json=json_body, timeout=timeout)
                if resp.status_code == 401 and bearer.provider == "xai-oauth":
                    # Refresh reactively once and retry immediately.
                    self.auth.refresh_now()
                    bearer = self._bearer()
                    headers["Authorization"] = f"Bearer {bearer.token}"
                    resp = requests.request(method, url, headers=headers, json=json_body, timeout=timeout)
                if resp.status_code >= 500 and attempt < max_retries:
                    time.sleep(min(5.0, 1.5 * (attempt + 1)))
                    continue
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise XaiClientError("xAI response was not a JSON object")
                return data
            except (requests.ReadTimeout, requests.ConnectionError) as exc:
                last_error = exc
                if attempt >= max_retries:
                    break
                time.sleep(min(5.0, 1.5 * (attempt + 1)))
            except requests.HTTPError as exc:
                raise XaiClientError(f"xAI request failed: {self._error_text(exc.response)}") from exc
        raise XaiClientError(f"xAI request failed after retries: {last_error}")

    @staticmethod
    def extract_text(payload: dict[str, Any]) -> str:
        output_text = str(payload.get("output_text") or "").strip()
        if output_text:
            return output_text
        parts: list[str] = []
        for item in payload.get("output", []) or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []) or []:
                if not isinstance(content, dict):
                    continue
                if content.get("type") in {"output_text", "text"}:
                    text = str(content.get("text") or "").strip()
                    if text:
                        parts.append(text)
        return "\n\n".join(parts).strip()

    @staticmethod
    def extract_inline_citations(payload: dict[str, Any]) -> list[dict[str, Any]]:
        citations: list[dict[str, Any]] = []
        for item in payload.get("output", []) or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []) or []:
                if not isinstance(content, dict):
                    continue
                for annotation in content.get("annotations", []) or []:
                    if isinstance(annotation, dict) and annotation.get("type") == "url_citation":
                        citations.append({
                            "url": annotation.get("url", ""),
                            "title": annotation.get("title", ""),
                            "start_index": annotation.get("start_index"),
                            "end_index": annotation.get("end_index"),
                        })
        return citations

    def create_response(
        self,
        *,
        input_items: str | list[dict[str, Any]],
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        store: bool | None = None,
        previous_response_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model or self.config.default_model,
            "input": input_items,
            "store": self.config.server_store if store is None else bool(store),
        }
        if tools is not None:
            payload["tools"] = tools
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        if extra:
            payload.update(extra)
        return self.request("POST", "/responses", json_body=payload)

    def retrieve_response(self, response_id: str) -> dict[str, Any]:
        return self.request("GET", f"/responses/{response_id}")

    def delete_response(self, response_id: str) -> dict[str, Any]:
        return self.request("DELETE", f"/responses/{response_id}")

    def list_models(self) -> dict[str, Any]:
        return self.request("GET", "/models")

    # --- Grok Imagine generation ------------------------------------------

    @staticmethod
    def _usage_summary(payload: dict[str, Any]) -> dict[str, Any]:
        usage = payload.get("usage") or {}
        ticks = usage.get("cost_in_usd_ticks") if isinstance(usage, dict) else None
        return {"raw": usage, "cost_in_usd_ticks": ticks, "cost_usd_approx": usd_from_ticks(ticks)}

    def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        n: int = 1,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Synchronous image generation via POST /images/generations."""
        if not prompt.strip():
            raise XaiClientError("prompt is required")
        n = max(1, min(int(n), 10))
        body: dict[str, Any] = {
            "model": model or self.config.image_model,
            "prompt": prompt.strip(),
            "n": n,
        }
        if extra:
            body.update(extra)
        resp = self.request("POST", XAI_IMAGE_GENERATIONS_PATH, json_body=body)
        images = [
            {"url": d.get("url", ""), "mime_type": d.get("mime_type", "")}
            for d in (resp.get("data") or [])
            if isinstance(d, dict)
        ]
        return {
            "success": bool(images),
            "model": body["model"],
            "prompt": body["prompt"],
            "images": images,
            "usage": self._usage_summary(resp),
            "raw": resp,
        }

    def generate_video(
        self,
        prompt: str,
        *,
        model: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Kick off async video generation. Returns {request_id}."""
        if not prompt.strip():
            raise XaiClientError("prompt is required")
        body: dict[str, Any] = {
            "model": model or self.config.video_model,
            "prompt": prompt.strip(),
        }
        if extra:
            body.update(extra)
        resp = self.request("POST", XAI_VIDEO_GENERATIONS_PATH, json_body=body)
        request_id = str(resp.get("request_id") or "").strip()
        if not request_id:
            raise XaiClientError(f"video generation did not return a request_id: {json.dumps(resp)[:400]}")
        return {"request_id": request_id, "model": body["model"], "prompt": body["prompt"], "raw": resp}

    def get_video(self, request_id: str) -> dict[str, Any]:
        """Poll one video job: GET /videos/{request_id}."""
        rid = str(request_id).strip()
        if not rid:
            raise XaiClientError("request_id is required")
        return self.request("GET", f"{XAI_VIDEO_STATUS_PATH}/{rid}")

    def wait_video(
        self,
        request_id: str,
        *,
        interval: float = VIDEO_POLL_INTERVAL_SECONDS,
        timeout: float = VIDEO_POLL_TIMEOUT_SECONDS,
        on_progress: Any = None,
    ) -> dict[str, Any]:
        """Poll until the job leaves a running state or timeout elapses."""
        rid = str(request_id).strip()
        deadline = time.time() + max(1.0, float(timeout))
        last: dict[str, Any] = {}
        while time.time() < deadline:
            last = self.get_video(rid)
            status = str(last.get("status") or "").lower()
            if callable(on_progress):
                on_progress(status, last.get("progress"))
            if status in VIDEO_DONE_STATUSES:
                video = last.get("video") or {}
                ok = status in {"done", "completed", "succeeded"} and bool(video.get("url"))
                return {
                    "success": ok,
                    "status": status,
                    "request_id": rid,
                    "model": last.get("model"),
                    "video": video,
                    "usage": self._usage_summary(last),
                    "raw": last,
                }
            time.sleep(max(1.0, float(interval)))
        raise XaiClientError(f"video job {rid} did not finish within {timeout:.0f}s (last status: {last.get('status')})")

    def x_search(
        self,
        query: str,
        *,
        allowed_x_handles: Iterable[str] | None = None,
        excluded_x_handles: Iterable[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        enable_image_understanding: bool = False,
        enable_video_understanding: bool = False,
        model: str | None = None,
        store: bool | None = None,
    ) -> dict[str, Any]:
        if not query.strip():
            raise XaiClientError("query is required")
        allowed = [str(h).strip().lstrip("@") for h in (allowed_x_handles or []) if str(h).strip()]
        excluded = [str(h).strip().lstrip("@") for h in (excluded_x_handles or []) if str(h).strip()]
        if len(allowed) > 10 or len(excluded) > 10:
            raise XaiClientError("allowed_x_handles and excluded_x_handles support at most 10 handles")
        if allowed and excluded:
            raise XaiClientError("allowed_x_handles and excluded_x_handles are mutually exclusive")
        tool: dict[str, Any] = {"type": "x_search"}
        if allowed:
            tool["allowed_x_handles"] = allowed
        if excluded:
            tool["excluded_x_handles"] = excluded
        if from_date:
            tool["from_date"] = from_date
        if to_date:
            tool["to_date"] = to_date
        if enable_image_understanding:
            tool["enable_image_understanding"] = True
        if enable_video_understanding:
            tool["enable_video_understanding"] = True

        response = self.create_response(
            model=model or self.config.search_model,
            input_items=[{"role": "user", "content": query.strip()}],
            tools=[tool],
            store=False if store is None else store,
        )
        return {
            "success": True,
            "provider": "xai",
            "tool": "x_search",
            "model": response.get("model") or (model or self.config.search_model),
            "query": query.strip(),
            "answer": self.extract_text(response),
            "citations": list(response.get("citations") or []),
            "inline_citations": self.extract_inline_citations(response),
            "response_id": response.get("id"),
            "raw": response,
        }


def compact_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": payload.get("id"),
        "model": payload.get("model"),
        "status": payload.get("status"),
        "answer": XaiClient.extract_text(payload),
        "citations": payload.get("citations", []),
        "inline_citations": XaiClient.extract_inline_citations(payload),
        "usage": payload.get("usage"),
    }
