"""Tests for shot.py — screenshot capture + pool event emission."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog import config, shot  # noqa: E402


@pytest.fixture
def init_pool(tmp_path, monkeypatch):
    """Initialize a fresh pool root + device for the test."""
    monkeypatch.setenv("AGENTLOG_POOL", str(tmp_path))
    # Pool dir skeleton (init usually creates these)
    for sub in ("pool", "artifacts", "state"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    config.cursors_dir().mkdir(parents=True, exist_ok=True)
    config.devices_dir().mkdir(parents=True, exist_ok=True)
    config.init_device(force=True)
    return tmp_path


def _fake_capture_ok(out_path: Path, content: bytes = b"\x89PNG\r\n\x1a\nfake") -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(content)


def test_shot_url_mode_emits_event(init_pool, monkeypatch):
    """Headless URL capture → event lands in the pool with a screenshot artifact."""

    def fake_capture_url(url, out, *, width, height, timeout=30):
        _fake_capture_ok(out)
        return (True, None)

    monkeypatch.setattr(shot, "_capture_url", fake_capture_url)

    result = shot.take_shot(target="https://example.com", note="smoke")
    assert result.ok
    assert result.path is not None and result.path.exists()
    assert result.sha256 is not None and result.sha256.startswith("sha256:")
    assert result.bytes is not None and result.bytes > 0
    assert result.event_id is not None

    # Pool should have exactly one jsonl with our event
    pool_dir = init_pool / "pool"
    jsonl_files = list(pool_dir.rglob("*.jsonl"))
    assert len(jsonl_files) == 1, "expected one shard after one shot"
    line = jsonl_files[0].read_text(encoding="utf-8").splitlines()[0]
    import json
    event = json.loads(line)
    assert event["action"]["type"] == "checkpoint"
    assert event["action"]["label"] == "shot"
    assert event["source_type"] == "manual"
    assert event["artifact_refs"][0]["kind"] == "screenshot"
    assert event["artifact_refs"][0]["sha256"].startswith("sha256:")


def test_shot_unrecognized_target_errors(init_pool, monkeypatch):
    result = shot.take_shot(target="not a url and not localhost")
    assert not result.ok
    assert "unrecognized target" in (result.error or "")


def test_shot_url_capture_failure_no_event(init_pool, monkeypatch):
    """If capture fails, no event should be emitted."""

    def failing_capture(url, out, *, width, height, timeout=30):
        return (False, "fake failure")

    monkeypatch.setattr(shot, "_capture_url", failing_capture)
    result = shot.take_shot(target="https://example.com")
    assert not result.ok
    assert result.error == "fake failure"

    # No event should have been written
    pool_dir = init_pool / "pool"
    assert list(pool_dir.rglob("*.jsonl")) == []


def test_shot_localhost_normalized(init_pool, monkeypatch):
    """`localhost:3000` should be treated as a URL, not interactive."""

    captured_url = {}

    def fake_capture_url(url, out, *, width, height, timeout=30):
        captured_url["url"] = url
        _fake_capture_ok(out)
        return (True, None)

    monkeypatch.setattr(shot, "_capture_url", fake_capture_url)
    result = shot.take_shot(target="localhost:3000")
    assert result.ok
    assert captured_url["url"] == "http://localhost:3000"
