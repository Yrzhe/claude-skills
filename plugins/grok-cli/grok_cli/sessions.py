"""SQLite-backed session and context storage."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config, load_config, save_config
from .constants import DEFAULT_XAI_MODEL
from .paths import db_path, ensure_app_home


@dataclass
class Session:
    id: str
    name: str
    model: str
    system_prompt: str | None
    mode: str
    current_response_id: str | None
    created_at: int
    updated_at: int


class SessionStore:
    def __init__(self, path: Path | None = None) -> None:
        ensure_app_home()
        self.path = path or db_path()
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (
                  id TEXT PRIMARY KEY,
                  name TEXT UNIQUE NOT NULL,
                  model TEXT NOT NULL,
                  system_prompt TEXT,
                  mode TEXT DEFAULT 'chat',
                  current_response_id TEXT,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                  id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  provider_response_id TEXT,
                  raw_response_json TEXT,
                  created_at INTEGER NOT NULL,
                  FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS citations (
                  id TEXT PRIMARY KEY,
                  message_id TEXT NOT NULL,
                  title TEXT,
                  url TEXT,
                  start_index INTEGER,
                  end_index INTEGER,
                  raw_json TEXT,
                  FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS session_summaries (
                  id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  summary TEXT NOT NULL,
                  covered_until_message_id TEXT,
                  created_at INTEGER NOT NULL,
                  FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session_created ON messages(session_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_citations_message ON citations(message_id);
                """
            )
            conn.commit()
        self.ensure_session("default")

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    def ensure_session(self, name: str, *, model: str | None = None, system_prompt: str | None = None) -> Session:
        if not name.strip():
            raise ValueError("session name is required")
        existing = self.get_session(name)
        if existing:
            return existing
        now = self._now()
        sid = self._new_id("ses")
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sessions (id, name, model, system_prompt, mode, current_response_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sid, name.strip(), model or DEFAULT_XAI_MODEL, system_prompt, "chat", None, now, now),
            )
            conn.commit()
        return self.get_session(name)  # type: ignore[return-value]

    def get_session(self, name_or_id: str) -> Session | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE name = ? OR id = ? LIMIT 1",
                (name_or_id, name_or_id),
            ).fetchone()
        if not row:
            return None
        return Session(**dict(row))

    def current_session(self, cfg: Config | None = None) -> Session:
        cfg = cfg or load_config()
        return self.ensure_session(cfg.current_session, model=cfg.default_model)

    def use_session(self, name: str) -> Session:
        session = self.ensure_session(name)
        cfg = load_config()
        cfg.current_session = session.name
        save_config(cfg)
        return session

    def list_sessions(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*, COUNT(m.id) AS message_count
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_session(self, name_or_id: str) -> bool:
        session = self.get_session(name_or_id)
        if not session:
            return False
        with self.connect() as conn:
            conn.execute("DELETE FROM citations WHERE message_id IN (SELECT id FROM messages WHERE session_id = ?)", (session.id,))
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session.id,))
            conn.execute("DELETE FROM session_summaries WHERE session_id = ?", (session.id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session.id,))
            conn.commit()
        cfg = load_config()
        if cfg.current_session == session.name:
            cfg.current_session = "default"
            save_config(cfg)
        self.ensure_session("default")
        return True

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        provider_response_id: str | None = None,
        raw_response: dict[str, Any] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> str:
        mid = self._new_id("msg")
        now = self._now()
        raw_text = json.dumps(raw_response, ensure_ascii=False) if raw_response is not None else None
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content, provider_response_id, raw_response_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (mid, session_id, role, content, provider_response_id, raw_text, now),
            )
            for citation in citations or []:
                conn.execute(
                    "INSERT INTO citations (id, message_id, title, url, start_index, end_index, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        self._new_id("cit"),
                        mid,
                        citation.get("title"),
                        citation.get("url"),
                        citation.get("start_index"),
                        citation.get("end_index"),
                        json.dumps(citation, ensure_ascii=False),
                    ),
                )
            conn.execute("UPDATE sessions SET updated_at = ?, current_response_id = COALESCE(?, current_response_id) WHERE id = ?", (now, provider_response_id, session_id))
            conn.commit()
        return mid

    def recent_messages(self, session_id: str, limit: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def all_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
        return [dict(row) for row in rows]

    def latest_summary(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM session_summaries WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                (session_id,),
            ).fetchone()
        return dict(row) if row else None

    def add_summary(self, session_id: str, summary: str, covered_until_message_id: str | None = None) -> str:
        sid = self._new_id("sum")
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO session_summaries (id, session_id, summary, covered_until_message_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (sid, session_id, summary, covered_until_message_id, self._now()),
            )
            conn.commit()
        return sid

    def build_input(self, session: Session, user_content: str, *, max_messages: int) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        if session.system_prompt:
            items.append({"role": "system", "content": session.system_prompt})
        summary = self.latest_summary(session.id)
        if summary:
            items.append({"role": "system", "content": "Session summary so far:\n" + summary["summary"]})
        for msg in self.recent_messages(session.id, max_messages):
            if msg["role"] in {"user", "assistant", "system"}:
                items.append({"role": msg["role"], "content": msg["content"]})
        items.append({"role": "user", "content": user_content})
        return items

    def export_session_markdown(self, name_or_id: str) -> str:
        session = self.get_session(name_or_id)
        if not session:
            raise ValueError(f"Session not found: {name_or_id}")
        lines = [f"# grok-cli session: {session.name}", ""]
        if session.system_prompt:
            lines += ["## System prompt", "", session.system_prompt, ""]
        summary = self.latest_summary(session.id)
        if summary:
            lines += ["## Latest summary", "", summary["summary"], ""]
        lines.append("## Messages")
        lines.append("")
        for msg in self.all_messages(session.id):
            lines.append(f"### {msg['role']} — {msg['created_at']}")
            lines.append("")
            lines.append(msg["content"])
            lines.append("")
        return "\n".join(lines)
