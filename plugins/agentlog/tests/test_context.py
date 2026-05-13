from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.context import (  # noqa: E402
    AGENT_CONTEXT_DIR,
    AGENTS_MD,
    CLAUDE_MD,
    DECISIONS_FILE,
    NEXT_STEPS_FILE,
    STATE_FILE,
    STATE_BLOCK_END,
    STATE_BLOCK_START,
    append_decision,
    init_project,
    read_state,
    sync_state,
)


def test_init_project_creates_skeleton(tmp_path: Path) -> None:
    result = init_project(tmp_path)

    assert (tmp_path / AGENTS_MD).exists()
    assert (tmp_path / CLAUDE_MD).exists()
    assert (tmp_path / AGENT_CONTEXT_DIR / STATE_FILE).exists()
    assert (tmp_path / AGENT_CONTEXT_DIR / DECISIONS_FILE).exists()
    assert (tmp_path / AGENT_CONTEXT_DIR / NEXT_STEPS_FILE).exists()
    assert result["created"]
    assert STATE_BLOCK_START in (tmp_path / AGENTS_MD).read_text()
    assert STATE_BLOCK_END in (tmp_path / CLAUDE_MD).read_text()


def test_init_project_idempotent(tmp_path: Path) -> None:
    init_project(tmp_path)
    (tmp_path / AGENTS_MD).write_text(
        "# My Custom Header\n\nKeep me.\n\n"
        f"{STATE_BLOCK_START}\nold state\n{STATE_BLOCK_END}\n"
    )

    second = init_project(tmp_path)
    text = (tmp_path / AGENTS_MD).read_text()

    assert "# My Custom Header" in text
    assert "Keep me." in text
    assert not second["created"]


def test_sync_state_updates_both_markdowns(tmp_path: Path) -> None:
    init_project(tmp_path)
    state_md = "## Status\n\n- API: shipped\n- UI: in progress\n"
    next_steps_md = "- [ ] write tests\n- [ ] deploy\n"

    sync_state(tmp_path, state_md=state_md, next_steps_md=next_steps_md)

    agents_text = (tmp_path / AGENTS_MD).read_text()
    claude_text = (tmp_path / CLAUDE_MD).read_text()

    assert "API: shipped" in agents_text
    assert "API: shipped" in claude_text
    assert (tmp_path / AGENT_CONTEXT_DIR / STATE_FILE).read_text() == state_md
    assert (tmp_path / AGENT_CONTEXT_DIR / NEXT_STEPS_FILE).read_text() == next_steps_md


def test_sync_state_preserves_user_text_outside_block(tmp_path: Path) -> None:
    init_project(tmp_path)
    custom = (
        "# My Project\n\n## Setup\n\n"
        "Run `npm install`.\n\n"
        f"{STATE_BLOCK_START}\nold state\n{STATE_BLOCK_END}\n\n"
        "## Coding Style\n\nUse tabs.\n"
    )
    (tmp_path / AGENTS_MD).write_text(custom)
    (tmp_path / CLAUDE_MD).write_text(custom)

    sync_state(tmp_path, state_md="new state body\n", next_steps_md="- [ ] x\n")

    text = (tmp_path / AGENTS_MD).read_text()
    assert "# My Project" in text
    assert "Run `npm install`" in text
    assert "Use tabs." in text
    assert "new state body" in text
    assert "old state" not in text


def test_sync_state_idempotent_no_drift(tmp_path: Path) -> None:
    init_project(tmp_path)
    sync_state(tmp_path, state_md="same\n", next_steps_md="- [ ] same\n")
    snapshot_a = (tmp_path / AGENTS_MD).read_text()

    sync_state(tmp_path, state_md="same\n", next_steps_md="- [ ] same\n")
    snapshot_b = (tmp_path / AGENTS_MD).read_text()

    assert snapshot_a == snapshot_b


def test_append_decision_appends_only_never_overwrites(tmp_path: Path) -> None:
    init_project(tmp_path)
    append_decision(
        tmp_path,
        title="use AGENTS.md double-write",
        rationale="covers Cursor + Codex without duplication",
        alternatives=["single docs/agent-context.md include"],
        source_event_id="cursor:abc:tab-a:3",
    )
    append_decision(
        tmp_path,
        title="LLM distill with Haiku",
        rationale="cheap and structured output",
        alternatives=["template-only", "hybrid"],
        source_event_id="manual:plan:2026-05-13",
    )

    text = (tmp_path / AGENT_CONTEXT_DIR / DECISIONS_FILE).read_text()
    assert "use AGENTS.md double-write" in text
    assert "LLM distill with Haiku" in text
    assert text.index("AGENTS.md double-write") < text.index("LLM distill")


def test_read_state_round_trip(tmp_path: Path) -> None:
    init_project(tmp_path)
    sync_state(tmp_path, state_md="## Live state\n", next_steps_md="- [ ] later\n")

    state = read_state(tmp_path)
    assert state["state"] == "## Live state\n"
    assert state["next_steps"] == "- [ ] later\n"
