#!/usr/bin/env python3
"""Host hook bridge for adaptive-compaction.

JSON stdin -> JSON stdout. No network. No model calls.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import decide
import decision_log
import prune_zero_llm
import score_signals
import state_packet


class HookBridgeError(ValueError):
    pass


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def runtime_dir(payload: dict[str, Any]) -> Path:
    raw = (
        payload.get("adaptive_compaction_dir")
        or os.environ.get("ADAPTIVE_COMPACTION_DIR")
        or ".adaptive-compaction"
    )
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        cwd = payload.get("cwd") or payload.get("workspace") or os.getcwd()
        path = (Path(str(cwd)) / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def normalize_tool_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    events = payload.get("tool_events") or payload.get("toolEvents") or []
    if not isinstance(events, list):
        return []
    out = []
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        copied = dict(event)
        copied.setdefault("id", f"hook-event-{idx}")
        copied.setdefault("type", copied.get("tool") or copied.get("name") or "tool")
        copied.setdefault("target", copied.get("path") or copied.get("command") or copied.get("name") or "unknown")
        copied.setdefault("content_hash", copied.get("hash") or copied.get("sha256") or copied["id"])
        copied.setdefault("tokens", copied.get("token_count") or copied.get("tokenCount") or 0)
        copied.setdefault("errored", bool(copied.get("error") or copied.get("errored", False)))
        copied.setdefault("turn", copied.get("turn") or copied.get("turn_index") or idx)
        out.append(copied)
    return out


def normalize_recent_turns(payload: dict[str, Any]) -> list[dict[str, Any]]:
    turns = payload.get("recent_turns") or payload.get("recentTurns") or []
    if not isinstance(turns, list):
        return []
    out = []
    for turn in turns:
        if isinstance(turn, dict):
            out.append(
                {
                    "role": str(turn.get("role", "assistant")),
                    "summary": str(turn.get("summary") or turn.get("content") or ""),
                    "tokens": int(turn.get("tokens") or turn.get("token_count") or 0),
                }
            )
    return out


def host_for(mode: str, payload: dict[str, Any]) -> str:
    if payload.get("host"):
        return str(payload["host"])
    if mode.startswith("codex"):
        return "codex"
    if mode.startswith("claude"):
        return "claude-code"
    return "unknown"


def user_prompt_for(payload: dict[str, Any]) -> str:
    prompt = (
        payload.get("user_prompt")
        or payload.get("prompt")
        or payload.get("message")
        or payload.get("transcript")
        or payload.get("hook_input")
        or ""
    )
    return str(prompt)


def telemetry(mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    host = host_for(mode, payload)
    tokens_used = int(payload.get("tokens_used") or payload.get("input_tokens") or payload.get("context_tokens") or 0)
    effective_window = int(
        payload.get("effective_window")
        or payload.get("context_window")
        or os.environ.get("ADAPTIVE_COMPACTION_EFFECTIVE_WINDOW", "200000")
    )
    reserved_output = int(
        payload.get("reserved_output")
        or os.environ.get("ADAPTIVE_COMPACTION_RESERVED_OUTPUT", "20000")
    )
    return {
        "host": host,
        "host_capability_tier": payload.get("host_capability_tier") or score_signals.HOST_TIERS.get(host, "persist-only"),
        "tokens_used": tokens_used,
        "effective_window": effective_window,
        "reserved_output": reserved_output,
        "user_prompt": user_prompt_for(payload),
        "objective": payload.get("objective") or payload.get("goal"),
        "accepted_constraints": list_of_strings(payload.get("accepted_constraints") or payload.get("constraints")),
        "hot_files": list_of_strings(payload.get("hot_files") or payload.get("files")),
        "touched_symbols": list_of_strings(payload.get("touched_symbols") or payload.get("symbols")),
        "plan_items": list_of_strings(payload.get("plan_items") or payload.get("todos")),
        "recent_turns": normalize_recent_turns(payload),
        "tool_events": normalize_tool_events(payload),
        "turns_since_last_compaction": int(payload.get("turns_since_last_compaction") or 9999),
        "explicit_new_task_marker": bool(payload.get("explicit_new_task_marker", False)),
    }


def packet_input(payload: dict[str, Any], telem: dict[str, Any], rt_dir: Path) -> dict[str, Any]:
    transcript_dump = payload.get("transcript_dump")
    if not transcript_dump:
        dump = rt_dir / "transcript-dump.json"
        dump.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        transcript_dump = str(dump.resolve())
    return {
        "output_path": str((rt_dir / "TASK_STATE.md").resolve()),
        "host": telem["host"],
        "host_version": payload.get("host_version", "unknown"),
        "session_id": payload.get("session_id", payload.get("sessionId", "unknown")),
        "source_turn": payload.get("turn", payload.get("turn_index", 0)),
        "confidence": 0.7,
        "transcript_dump": transcript_dump,
        "goal": telem.get("objective") or payload.get("goal") or "Not recorded.",
        "accepted_constraints": telem["accepted_constraints"],
        "branch": payload.get("branch", "unknown"),
        "worktree": payload.get("cwd") or payload.get("workspace") or os.getcwd(),
        "touched_files": telem["hot_files"],
        "touched_symbols": telem["touched_symbols"],
        "decisions": list_of_strings(payload.get("decisions")),
        "failing_tests": list_of_strings(payload.get("failing_tests") or payload.get("failing_commands")),
        "open_risks": list_of_strings(payload.get("open_risks") or payload.get("risks")),
        "next_action": payload.get("next_action", "Reload TASK_STATE.md and continue from the recorded next action."),
        "files_to_reload": list_of_strings(payload.get("files_to_reload") or telem["hot_files"]),
    }


def log_decision(payload: dict[str, Any], rt_dir: Path, telem: dict[str, Any], signals: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "log_path": str((rt_dir / "decision_log.jsonl").resolve()),
        "session_id": payload.get("session_id", payload.get("sessionId", "unknown")),
        "host": telem["host"],
        "host_capability_tier": signals["host_capability_tier"],
        "headroom_frac": signals["headroom_frac"],
        "relevance": signals["relevance"],
        "relevance_confidence": signals["relevance_confidence"],
        "burden_tokens": signals["burden_tokens"],
        "continuity": signals["continuity"],
        "continuity_flags": signals["continuity_flags"],
        "action": decision["action"],
        "require_snapshot": decision["require_snapshot"],
        "thresholds": decision["thresholds_used"],
    }
    return decision_log.append_log(entry)


def maybe_prune(telem: dict[str, Any], rt_dir: Path, decision_obj: dict[str, Any]) -> dict[str, Any] | None:
    if decision_obj["action"] != "ZERO_LLM_PRUNE":
        return None
    prune_input = dict(telem)
    prune_input["quarantine_dir"] = str((rt_dir / "quarantine").resolve())
    prune_input["thresholds"] = decision_obj["thresholds_used"]
    return prune_zero_llm.plan_prune(prune_input)


ACT_NOW_ACTIONS = {"FORCED_COMPACT", "FORK_OR_RESET", "ASK_USER"}
ATTENTION_ACTIONS = {"SAVE_STATE", "PREPARE_FOR_COMPACT", "ZERO_LLM_PRUNE"}


def user_facing_suggestion(action: str, task_state_path: str | None, reason: str) -> str:
    state_ref = task_state_path or "(state was not snapshotted)"
    if action == "FORCED_COMPACT":
        return (
            f"Context window is at the forced band — recommend running `/compact` now. "
            f"I've already saved current state to {state_ref}, so nothing is lost when you compact."
        )
    if action == "FORK_OR_RESET":
        return (
            f"This looks like a topic shift unrelated to the prior task. Recommend forking a fresh "
            f"session for the new work instead of compacting here (the prior task's state is saved "
            f"at {state_ref})."
        )
    if action == "ASK_USER":
        return (
            f"Policy hit an ambiguous case ({reason}) — need a quick confirmation before continuing."
        )
    return ""


def additional_context(decision_obj: dict[str, Any], task_state_path: str | None, prune_result: dict[str, Any] | None) -> str:
    action = decision_obj["action"]
    reason = decision_obj["reason"]
    lines = [
        "Adaptive compaction policy decision:",
        f"- action: {action}",
        f"- reason: {reason}",
        f"- host note: {decision_obj['host_note']}",
    ]
    if task_state_path:
        lines.append(f"- task state: {task_state_path}")
    if prune_result:
        lines.append(f"- zero-LLM recovered tokens: {prune_result['recovered_tokens']}")
        lines.append(f"- quarantine dir: {prune_result['quarantine_dir']}")

    if action in ACT_NOW_ACTIONS:
        suggestion = user_facing_suggestion(action, task_state_path, reason)
        lines.append("")
        lines.append(
            "AGENT DIRECTIVE (act-now): Before responding to the user's next message, "
            "surface this to them in plain language in their language, then continue "
            "with their actual request. Suggested wording (translate / adapt to the "
            "user's language and tone):"
        )
        lines.append("")
        lines.append(f"  > {suggestion}")
        lines.append("")
        lines.append("Do not silently swallow this signal — this is the only channel by which the policy can ask the user to act.")
    elif action in ATTENTION_ACTIONS:
        lines.append("")
        lines.append(
            "AGENT NOTE: The policy took a non-trivial action this turn "
            "(snapshot / prune / prepare). Mention to the user briefly if relevant; "
            "otherwise continue with their request."
        )
    return "\n".join(lines)


def hook_response(mode: str, decision_obj: dict[str, Any], context: str, task_state_path: str | None) -> dict[str, Any]:
    response = {
        "adaptive_compaction": {
            "mode": mode,
            "action": decision_obj["action"],
            "require_snapshot": decision_obj["require_snapshot"],
            "task_state_path": task_state_path,
        },
        "additionalContext": context,
        "hookSpecificOutput": {
            "additionalContext": context,
        },
    }
    if mode == "claude-user-prompt-submit":
        response["hookSpecificOutput"]["hookEventName"] = "UserPromptSubmit"
    elif mode == "claude-session-start":
        response["hookSpecificOutput"]["hookEventName"] = "SessionStart"
    elif mode == "claude-pre-compact":
        response["hookSpecificOutput"]["hookEventName"] = "PreCompact"
    return response


def last_log_decision(rt_dir: Path) -> dict[str, Any] | None:
    log_path = rt_dir / "decision_log.jsonl"
    if not log_path.exists():
        return None
    try:
        with log_path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            if size == 0:
                return None
            handle.seek(max(0, size - 8192))
            tail = handle.read().decode("utf-8", errors="ignore")
        lines = [ln for ln in tail.splitlines() if ln.strip()]
        if not lines:
            return None
        return json.loads(lines[-1])
    except (OSError, ValueError):
        return None


def precompact_override(payload: dict[str, Any], telem: dict[str, Any], rt_dir: Path) -> dict[str, Any] | None:
    """v1.1: Claude Code's PreCompact event does NOT pass token counts.
    Fresh scoring would see headroom_frac ~= 1.0 and emit NOOP, which would
    incorrectly block every native compaction. When telemetry is missing,
    base the gate on the most recent UserPromptSubmit decision (the live
    signal); if even that is unavailable, default to allow+snapshot rather
    than second-guess the harness."""
    if telem["tokens_used"] > 0:
        return None
    last = last_log_decision(rt_dir)
    if last and last.get("action"):
        return {
            "action": str(last["action"]),
            "reason": f"PreCompact telemetry missing; using last live decision from decision_log ({last['action']}).",
            "require_snapshot": True,
            "thresholds_used": last.get("thresholds", {}),
            "host_note": "v1.1 PreCompact override: replayed last UserPromptSubmit decision.",
        }
    return {
        "action": "FORCED_COMPACT",
        "reason": "PreCompact telemetry missing and no prior decision log; default allow+snapshot (harness triggered this event).",
        "require_snapshot": True,
        "thresholds_used": {},
        "host_note": "v1.1 PreCompact safe-fallback: allow+snapshot.",
    }


def synthetic_signals(telem: dict[str, Any]) -> dict[str, Any]:
    return {
        "headroom_frac": 0.0,
        "relevance": 0.0,
        "relevance_confidence": 0.0,
        "burden_tokens": 0,
        "continuity": 0.0,
        "continuity_flags": [],
        "host_capability_tier": telem["host_capability_tier"],
        "turns_since_last_compaction": telem["turns_since_last_compaction"],
    }


def run(mode: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any], str]:
    rt_dir = runtime_dir(payload)
    telem = telemetry(mode, payload)

    override = precompact_override(payload, telem, rt_dir) if mode == "claude-pre-compact" else None
    if override is not None:
        decision_obj = override
        signals = synthetic_signals(telem)
    else:
        signals = score_signals.score(telem)
        signals["turns_since_last_compaction"] = telem["turns_since_last_compaction"]
        decision_obj = decide.decide(signals)

    task_state_path = None
    if decision_obj["require_snapshot"] or mode in {"claude-pre-compact", "codex-pre-compact-advice"}:
        packet = state_packet.write_packet(packet_input(payload, telem, rt_dir))
        task_state_path = packet["task_state_path"]

    prune_result = maybe_prune(telem, rt_dir, decision_obj)
    log_decision(payload, rt_dir, telem, signals, decision_obj)
    context = additional_context(decision_obj, task_state_path, prune_result)
    response = hook_response(mode, decision_obj, context, task_state_path)

    if mode == "claude-pre-compact":
        allow_actions = {"FORCED_COMPACT", "PREPARE_FOR_COMPACT"}
        manual = str(payload.get("trigger", payload.get("matcher", ""))).lower() == "manual"
        if manual and task_state_path:
            return 0, response, ""
        if decision_obj["action"] in allow_actions and task_state_path:
            return 0, response, ""
        return 2, response, "Adaptive compaction blocked native compaction before the policy allowed it. See decision log and TASK_STATE."

    return 0, response, ""


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise HookBridgeError("usage: hook_bridge.py <mode>")
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise HookBridgeError("schema violation: input must be a JSON object")
        code, response, stderr_message = run(sys.argv[1], payload)
        print(json.dumps(response, indent=2, sort_keys=True))
        if stderr_message:
            print(stderr_message, file=sys.stderr)
        return code
    except (json.JSONDecodeError, HookBridgeError, score_signals.ContractError, decide.ContractError, state_packet.ContractError, decision_log.ContractError, prune_zero_llm.ContractError, OSError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
