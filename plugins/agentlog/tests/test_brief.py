from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog import brief  # noqa: E402
from agentlog.context import AGENT_CONTEXT_DIR, DECISIONS_FILE, NEXT_STEPS_FILE, STATE_FILE  # noqa: E402


def _event(
    *,
    project_name: str = "agentlog",
    action_type: str = "checkpoint",
    summary: str = "did a thing",
    timestamp: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "agentlog.event.v0",
        "id": "00000000-0000-0000-0000-000000000000",
        "source_event_id": f"test:{project_name}:{summary[:10]}",
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "actor": {"id": "x", "name": "X", "kind": "agent"},
        "source_type": "claude_code",
        "source": {"device_id": "dev-a"},
        "project": {"name": project_name},
        "action": {"type": action_type, "status": "completed"},
        "summary": summary,
        "payload": payload or {},
        "artifact_refs": [],
    }


class FakeAnthropicResponse:
    def __init__(self, text: str) -> None:
        self.content = [type("Block", (), {"text": text})()]


class FakeAnthropicClient:
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.last_messages: list[Any] | None = None
        self.last_model: str | None = None
        self.last_system: str | None = None

        class _Messages:
            def __init__(inner_self) -> None:  # noqa: N804
                pass

            def create(
                inner_self,  # noqa: N804
                *,
                model: str,
                max_tokens: int,
                system: str,
                messages: list[Any],
            ) -> FakeAnthropicResponse:
                self.last_model = model
                self.last_system = system
                self.last_messages = messages
                return FakeAnthropicResponse(self._response_text)

        self.messages = _Messages()


def _full_distill_text() -> str:
    return (
        "---STATE---\n"
        "- API server: running on port 8000\n"
        "- DB migrations: up to 0042\n"
        "---DECISIONS---\n"
        "## use Postgres\n\n"
        "Why: we needed strong consistency for the orders table.\n\n"
        "Alternatives considered: SQLite (too small), DynamoDB (no transactions)\n"
        "---NEXT-STEPS---\n"
        "- [ ] add e2e tests (high)\n"
        "- [ ] deploy to staging (medium)\n"
    )


def test_distill_parses_three_sections(tmp_path: Path) -> None:
    client = FakeAnthropicClient(_full_distill_text())
    events = [
        _event(action_type="decision", summary="picked Postgres", payload={"rationale": "consistency"}),
        _event(action_type="checkpoint", summary="API server up on 8000"),
    ]

    result = brief.distill(
        project_name="agentlog",
        events=events,
        anthropic_client=client,
        model="claude-haiku-4-5-20251001",
    )

    assert "API server: running on port 8000" in result["state"]
    assert "use Postgres" in result["decisions"]
    assert "deploy to staging" in result["next_steps"]
    assert client.last_model == "claude-haiku-4-5-20251001"
    sent = client.last_messages[0]["content"]
    assert "agentlog" in sent
    assert "picked Postgres" in sent


def test_run_brief_writes_files_and_appends_decisions(tmp_path: Path) -> None:
    client = FakeAnthropicClient(_full_distill_text())
    events = [_event(action_type="decision", summary="picked Postgres")]

    brief.run_brief(
        project_name="agentlog",
        project_root=tmp_path,
        events=events,
        anthropic_client=client,
    )

    state_path = tmp_path / AGENT_CONTEXT_DIR / STATE_FILE
    next_path = tmp_path / AGENT_CONTEXT_DIR / NEXT_STEPS_FILE
    decisions_path = tmp_path / AGENT_CONTEXT_DIR / DECISIONS_FILE

    assert "API server: running on port 8000" in state_path.read_text()
    assert "deploy to staging" in next_path.read_text()
    assert "use Postgres" in decisions_path.read_text()
    assert "consistency for the orders table" in decisions_path.read_text()


def test_run_brief_appends_decisions_only_once_per_run(tmp_path: Path) -> None:
    client = FakeAnthropicClient(_full_distill_text())
    events = [_event(action_type="decision", summary="picked Postgres")]

    brief.run_brief(
        project_name="agentlog",
        project_root=tmp_path,
        events=events,
        anthropic_client=client,
    )
    brief.run_brief(
        project_name="agentlog",
        project_root=tmp_path,
        events=events,
        anthropic_client=client,
    )

    decisions_text = (tmp_path / AGENT_CONTEXT_DIR / DECISIONS_FILE).read_text()
    assert decisions_text.count("— use Postgres") == 1


def test_distill_fails_fast_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        brief.get_default_client()


def test_select_events_prioritizes_decisions_and_caps(tmp_path: Path) -> None:
    events = (
        [_event(action_type="user_request", summary=f"req {i}") for i in range(50)]
        + [_event(action_type="decision", summary=f"dec {i}") for i in range(3)]
        + [_event(action_type="checkpoint", summary=f"ckpt {i}") for i in range(20)]
    )

    selected = brief.select_events(events, limit=10)
    types = [e["action"]["type"] for e in selected]
    assert types.count("decision") == 3
    assert len(selected) == 10
