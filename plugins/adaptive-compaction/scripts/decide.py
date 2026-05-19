#!/usr/bin/env python3
"""Canonical adaptive-compaction decision table.

JSON stdin -> JSON stdout. No network. No model calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


VALID_TIERS = {"hook-rich", "advise-persist", "persist-only"}


class ContractError(ValueError):
    pass


def load_thresholds() -> dict[str, float]:
    path = Path(__file__).with_name("thresholds.json")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ContractError(f"schema violation: {key} must be a number")
    return float(value)


def require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ContractError(f"schema violation: {key} must be a list")
    return value


def host_note(tier: str, action: str) -> str:
    if tier == "hook-rich":
        return "hook-rich host can enforce snapshot-first compaction boundaries; FORCED_COMPACT is allowed only on this tier."
    if tier == "advise-persist":
        return "advise-persist host can persist state and shape prompts, but native/server compaction is opaque; forced paths degrade to PREPARE_FOR_COMPACT."
    return "persist-only host can save/search/state only; no native compaction control is claimed."


def decision(action: str, reason: str, require_snapshot: bool, thresholds: dict[str, Any], tier: str) -> dict[str, Any]:
    if action == "FORCED_COMPACT" and tier != "hook-rich":
        action = "PREPARE_FOR_COMPACT"
        require_snapshot = True
        reason = reason + " Degraded because host tier cannot enforce native compaction."
    return {
        "action": action,
        "reason": reason,
        "require_snapshot": require_snapshot,
        "thresholds_used": thresholds,
        "host_note": host_note(tier, action),
    }


def decide(signals: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    if thresholds is None:
        thresholds = load_thresholds()

    for key in [
        "headroom_frac",
        "relevance",
        "relevance_confidence",
        "low_relevance_streak",
        "burden_tokens",
        "reclaimable_burden_frac",
        "continuity",
    ]:
        require_number(signals, key)
    flags = require_list(signals, "continuity_flags")
    tier = str(signals.get("host_capability_tier", "persist-only"))
    if tier not in VALID_TIERS:
        tier = "persist-only"

    h = float(signals["headroom_frac"])
    r = float(signals["relevance"])
    relevance_confidence = float(signals["relevance_confidence"])
    low_streak = int(signals["low_relevance_streak"])
    burden_frac = float(signals["reclaimable_burden_frac"])
    continuity = float(signals["continuity"])
    has_mid_task_flags = len(flags) > 0

    healthy = h >= thresholds["healthy_headroom_min"]
    soft = thresholds["soft_headroom_low"] <= h < thresholds["healthy_headroom_min"]
    forced = thresholds["hard_cap_floor"] < h <= thresholds["forced_headroom_floor"]
    pressure_gap = thresholds["forced_headroom_floor"] < h < thresholds["soft_headroom_low"]
    hard_cap = h <= thresholds["hard_cap_floor"]
    low_relevance = r < 0.30
    high_relevance = r >= 0.45
    high_burden = burden_frac >= thresholds["min_recovery_ratio"]
    explicit_marker = signals.get("explicit_new_task_marker") is True
    topic_shift = explicit_marker or low_streak >= thresholds["topic_shift_confirmation_turns"]
    low_relevance_low_confidence = low_relevance and relevance_confidence < 0.50
    in_thrash_cooldown = int(signals.get("turns_since_last_compaction", 9999) or 9999) < thresholds["thrash_cooldown_turns"]

    if hard_cap:
        return decision(
            "FORCED_COMPACT",
            "Hard-cap row: snapshot is required, then compact or prepare according to host capability.",
            True,
            thresholds,
            tier,
        )

    if in_thrash_cooldown and (forced or soft):
        if high_burden:
            return decision(
                "ZERO_LLM_PRUNE",
                "Thrash-guard row: recent compaction blocks another LLM compact; run deterministic pruning only.",
                False,
                thresholds,
                tier,
            )
        return decision(
            "SAVE_STATE",
            "Thrash-guard row: recent compaction blocks repeat compaction; refresh state instead.",
            True,
            thresholds,
            tier,
        )

    if has_mid_task_flags and not hard_cap:
        if forced:
            return decision(
                "SAVE_STATE",
                "Mid-task guard row: continuity flags block compaction before hard cap; snapshot active work.",
                True,
                thresholds,
                tier,
            )
        if high_burden:
            return decision(
                "ZERO_LLM_PRUNE",
                "Mid-task guard row: continuity flags block compaction; deterministic pruning is allowed.",
                False,
                thresholds,
                tier,
            )
        if low_relevance:
            return decision(
                "ASK_USER",
                "Healthy/soft low-relevance plus high-continuity row: ask before destructive topic handling.",
                False,
                thresholds,
                tier,
            )
        return decision(
            "NOOP",
            "Mid-task guard row: active continuity and no hard cap; preserve momentum.",
            False,
            thresholds,
            tier,
        )

    if healthy and topic_shift:
        if low_relevance_low_confidence:
            return decision(
                "ASK_USER",
                "Healthy-headroom topic-shift row: low relevance has low confidence, so ask before fork/reset.",
                False,
                thresholds,
                tier,
            )
        return decision(
            "FORK_OR_RESET",
            "Healthy-headroom topic-shift row: fork/reset by default instead of in-place compact.",
            False,
            thresholds,
            tier,
        )

    if healthy:
        if high_relevance and high_burden:
            return decision(
                "ZERO_LLM_PRUNE",
                "Healthy/high-relevance/high-burden row: prune deterministic garbage without compaction.",
                False,
                thresholds,
                tier,
            )
        return decision(
            "NOOP",
            "Healthy-headroom row: do not compact for headroom alone.",
            False,
            thresholds,
            tier,
        )

    if soft:
        if topic_shift:
            if low_relevance_low_confidence:
                return decision(
                    "ASK_USER",
                    "Soft-headroom topic-shift row: low relevance has low confidence, so ask before fork/reset.",
                    False,
                    thresholds,
                    tier,
                )
            return decision(
                "FORK_OR_RESET",
                "Soft-headroom topic-shift row: save old task if needed, then fork/reset.",
                False,
                thresholds,
                tier,
            )
        if high_burden:
            return decision(
                "ZERO_LLM_PRUNE",
                "Soft/high-burden row: zero-LLM pruning before any summary.",
                False,
                thresholds,
                tier,
            )
        return decision(
            "NOOP",
            "Soft/headroom low-burden row: wait; no compaction trigger.",
            False,
            thresholds,
            tier,
        )

    if forced:
        if topic_shift and not high_relevance:
            if low_relevance_low_confidence:
                return decision(
                    "SAVE_STATE",
                    "Forced-zone low-relevance row: low confidence blocks fork/reset automation; save state first.",
                    True,
                    thresholds,
                    tier,
                )
            return decision(
                "FORK_OR_RESET",
                "Forced-zone low-relevance row: SAVE_STATE is required before fork/reset so recovery is explicit.",
                True,
                thresholds,
                tier,
            )
        return decision(
            "FORCED_COMPACT",
            "Forced-zone row: snapshot required before compact/prepare.",
            True,
            thresholds,
            tier,
        )

    if pressure_gap:
        if high_burden:
            return decision(
                "ZERO_LLM_PRUNE",
                "Pre-forced pressure row: prune deterministic burden before summary.",
                False,
                thresholds,
                tier,
            )
        return decision(
            "SAVE_STATE",
            "Pre-forced pressure row: refresh state before entering forced zone.",
            True,
            thresholds,
            tier,
        )

    return decision(
        "NOOP",
        "Fallback row: no canonical trigger fired.",
        False,
        thresholds,
        tier,
    )


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ContractError("schema violation: input must be a JSON object")
        print(json.dumps(decide(data), indent=2, sort_keys=True))
        return 0
    except (json.JSONDecodeError, ContractError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
