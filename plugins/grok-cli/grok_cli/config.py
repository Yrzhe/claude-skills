"""Configuration loading and saving."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from .constants import (
    DEFAULT_CONTEXT_MESSAGES,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_XAI_BASE_URL,
    DEFAULT_XAI_IMAGE_MODEL,
    DEFAULT_XAI_MODEL,
    DEFAULT_XAI_SEARCH_MODEL,
    DEFAULT_XAI_VIDEO_MODEL,
    LEGACY_SEARCH_MODELS,
)
from .paths import config_path, write_private_text


@dataclass
class Config:
    base_url: str = DEFAULT_XAI_BASE_URL
    default_model: str = DEFAULT_XAI_MODEL
    search_model: str = DEFAULT_XAI_SEARCH_MODEL
    image_model: str = DEFAULT_XAI_IMAGE_MODEL
    video_model: str = DEFAULT_XAI_VIDEO_MODEL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    retries: int = DEFAULT_RETRIES
    max_context_messages: int = DEFAULT_CONTEXT_MESSAGES
    current_session: str = "default"
    prefer_oauth: bool = True
    server_store: bool = False


def load_config() -> Config:
    path = config_path()
    if not path.exists():
        cfg = Config()
        save_config(cfg)
        return cfg
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return Config()
    if not isinstance(data, dict):
        return Config()
    valid: dict[str, Any] = {}
    for field in Config.__dataclass_fields__.values():
        if field.name in data:
            valid[field.name] = data[field.name]
    cfg = Config(**valid)
    cfg.timeout_seconds = max(30, int(cfg.timeout_seconds))
    cfg.retries = max(0, int(cfg.retries))
    cfg.max_context_messages = max(1, int(cfg.max_context_messages))
    cfg.base_url = cfg.base_url.rstrip("/")
    # Migrate an invalid legacy search model id written by older versions.
    if cfg.search_model in LEGACY_SEARCH_MODELS:
        cfg.search_model = DEFAULT_XAI_SEARCH_MODEL
        save_config(cfg)
    return cfg


def save_config(cfg: Config) -> None:
    write_private_text(config_path(), json.dumps(asdict(cfg), indent=2, ensure_ascii=False) + "\n")


def set_config_value(key: str, value: str) -> Config:
    cfg = load_config()
    if not hasattr(cfg, key):
        raise KeyError(f"Unknown config key: {key}")
    old_value = getattr(cfg, key)
    if isinstance(old_value, bool):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            cast_value = True
        elif normalized in {"0", "false", "no", "off"}:
            cast_value = False
        else:
            raise ValueError(f"Expected boolean value for {key}")
    elif isinstance(old_value, int):
        cast_value = int(value)
    else:
        cast_value = value
    setattr(cfg, key, cast_value)
    save_config(cfg)
    return cfg
