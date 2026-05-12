from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentlog.adapters.maestri import MaestriAdapter  # noqa: E402
from agentlog.schema import validate  # noqa: E402


@dataclass
class AppendResult:
    ok: bool
    event_id: str
    shard_path: Path
    duplicate: bool
    error: str | None = None


class MockPool:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, event: dict, flush: bool = False) -> AppendResult:
        validate(event)
        self.events.append(event)
        return AppendResult(ok=True, event_id=event["id"], shard_path=Path("/tmp/mock"), duplicate=False)


def install_fake_maestri(monkeypatch, *, notes: dict[str, str], agents: dict[str, str]) -> None:
    listing = """You:
  - name: "Junction", role: "Adapter Architect"

Connected agents:
  - name: "Claude Code", role: "总管"
  - name: "Cistern", role: "Pool Architect"

Connected notes (use `maestri note read/write/edit`):
  - name: "agentlog-spec-v0"
  - name: "agentlog-adapter-design"

Connected portals:
  - name: "agentlog-docs"
"""

    def fake_run(command, check, capture_output, text, timeout):
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == 20
        args = list(command)
        subcommand = args[1:]
        if subcommand == ["list"]:
            return subprocess.CompletedProcess(args, 0, stdout=listing, stderr="")
        if subcommand[:1] == ["check"]:
            name = subcommand[1]
            return subprocess.CompletedProcess(args, 0, stdout=agents[name], stderr="")
        if subcommand[:2] == ["note", "read"]:
            name = subcommand[2]
            return subprocess.CompletedProcess(args, 0, stdout=notes[name], stderr="")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(subprocess, "run", fake_run)


def make_adapter(tmp_path: Path, pool: MockPool) -> MaestriAdapter:
    return MaestriAdapter(pool, cursor_path=tmp_path / "maestri-cursor.json", device_id="test-device")


def test_first_poll_emits_two_peer_agents_and_two_notes(tmp_path: Path, monkeypatch) -> None:
    """The local agent ("You:" section, here "Junction") is skipped — only
    connected peers + connected notes are emitted."""
    notes = {
        "agentlog-spec-v0": "[2 lines total]\n1\tagentlog spec\n2\tphase one\n",
        "agentlog-adapter-design": "[2 lines total]\n1\tagentlog adapter\n2\tv0 design\n",
    }
    agents = {
        "Claude Code": "waiting for architects\n",
        "Cistern": "pool design done\n",
    }
    install_fake_maestri(monkeypatch, notes=notes, agents=agents)
    pool = MockPool()

    result = make_adapter(tmp_path, pool).pollOnce()

    assert result["emitted"] == 4
    assert [event["action"]["type"] for event in pool.events] == [
        "session_started",
        "session_started",
        "note_created",
        "note_created",
    ]
    assert [event["summary"] for event in pool.events[:2]] == [
        "Maestri agent connected: Claude Code",
        "Maestri agent connected: Cistern",
    ]
    for event in pool.events:
        validate(event)


def test_second_poll_without_change_emits_zero(tmp_path: Path, monkeypatch) -> None:
    notes = {
        "agentlog-spec-v0": "[1 line total]\n1\tagentlog spec\n",
        "agentlog-adapter-design": "[1 line total]\n1\tagentlog adapter\n",
    }
    agents = {
        "Claude Code": "waiting for architects\n",
        "Cistern": "pool design done\n",
    }
    install_fake_maestri(monkeypatch, notes=notes, agents=agents)
    pool = MockPool()
    adapter = make_adapter(tmp_path, pool)

    first = adapter.pollOnce()
    second = adapter.pollOnce()

    assert first["emitted"] == 4
    assert second["emitted"] == 0
    assert len(pool.events) == 4


def test_note_content_change_emits_one_note_updated(tmp_path: Path, monkeypatch) -> None:
    notes = {
        "agentlog-spec-v0": "[1 line total]\n1\tagentlog spec\n",
        "agentlog-adapter-design": "[1 line total]\n1\tagentlog adapter\n",
    }
    agents = {
        "Junction": "working on adapter\n",
        "Claude Code": "waiting for architects\n",
        "Cistern": "pool design done\n",
    }
    install_fake_maestri(monkeypatch, notes=notes, agents=agents)
    pool = MockPool()
    adapter = make_adapter(tmp_path, pool)

    adapter.pollOnce()
    pool.events.clear()
    notes["agentlog-adapter-design"] = "[2 lines total]\n1\tagentlog adapter\n2\tupdated section\n"
    result = adapter.pollOnce()

    assert result["emitted"] == 1
    event = pool.events[0]
    validate(event)
    assert event["action"]["type"] == "note_updated"
    assert event["summary"] == "Maestri note updated: agentlog-adapter-design"
    assert event["artifact_refs"] == [
        {
            "kind": "note",
            "uri": "agentlog-adapter-design",
            "storage": "external",
            "metadata": {"source": "maestri"},
        }
    ]
