#!/usr/bin/env python3
"""Analyze decision_log.jsonl to recommend an autoCompactWindow value.

Reads a runtime decision log, summarizes the action distribution + the
headroom band where FORCED_COMPACT actually fires under the live policy,
and recommends where to set the native auto-compact threshold so that
the native trigger and the policy land on the same boundary.

Usage:
  python3 analyze_decision_log.py <path/to/decision_log.jsonl> \\
      [--effective-window 1000000] [--reserved-output 20000]

No network, no model calls.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def read_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def histogram(values: list[float], bins: int = 10, low: float = 0.0, high: float = 1.0) -> list[tuple[float, float, int]]:
    if not values:
        return []
    step = (high - low) / bins
    edges = [low + i * step for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        idx = min(bins - 1, max(0, int((v - low) / step)))
        counts[idx] += 1
    return [(edges[i], edges[i + 1], counts[i]) for i in range(bins)]


def fmt_bar(count: int, width: int = 30, max_count: int = 1) -> str:
    return "#" * max(0, int(width * count / max(1, max_count)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_path", type=Path, help="Path to decision_log.jsonl")
    ap.add_argument("--effective-window", type=int, default=1_000_000,
                    help="Model's true context window in tokens (default 1M)")
    ap.add_argument("--reserved-output", type=int, default=20_000,
                    help="Reserved output tokens (default 20K)")
    args = ap.parse_args()

    entries = read_entries(args.log_path)
    if not entries:
        print(f"No entries in {args.log_path}", file=sys.stderr)
        return 1

    # Filter to fresh UserPromptSubmit decisions (drop PreCompact overrides,
    # which carry synthetic headroom_frac == 0.0).
    fresh = [e for e in entries if isinstance(e.get("headroom_frac"), (int, float)) and e.get("headroom_frac") > 0]

    print(f"Decision log: {args.log_path}")
    print(f"Total entries: {len(entries)} ({len(fresh)} fresh, {len(entries) - len(fresh)} override-replays)")
    print()

    # Action distribution
    actions: dict[str, int] = {}
    for e in entries:
        a = str(e.get("action", "?"))
        actions[a] = actions.get(a, 0) + 1
    print("Action distribution (all entries):")
    total = sum(actions.values()) or 1
    for a in sorted(actions, key=lambda x: -actions[x]):
        pct = 100 * actions[a] / total
        print(f"  {a:22} {actions[a]:5}  {pct:5.1f}%")
    print()

    if not fresh:
        print("No fresh UserPromptSubmit decisions to analyze headroom from.", file=sys.stderr)
        return 0

    # Headroom histogram for FORCED + NOOP
    forced = [float(e["headroom_frac"]) for e in fresh if e["action"] == "FORCED_COMPACT"]
    noop = [float(e["headroom_frac"]) for e in fresh if e["action"] == "NOOP"]

    print(f"Headroom_frac at FORCED_COMPACT ({len(forced)} samples):")
    if forced:
        print(f"  min={min(forced):.3f}  median={statistics.median(forced):.3f}  max={max(forced):.3f}")
        hist = histogram(forced, bins=10)
        peak = max((c for _, _, c in hist), default=1)
        for lo, hi, c in hist:
            if c:
                print(f"  [{lo:.2f}, {hi:.2f})  {c:4}  {fmt_bar(c, max_count=peak)}")
    else:
        print("  (none — policy has not signalled FORCED_COMPACT yet)")
    print()

    print(f"Headroom_frac at NOOP ({len(noop)} samples):")
    if noop:
        print(f"  min={min(noop):.3f}  median={statistics.median(noop):.3f}  max={max(noop):.3f}")
    print()

    # Recommend autoCompactWindow: where most FORCED events cluster.
    # tokens_used at headroom_frac h ≈ effective_window * (1 - h) - reserved_output
    if forced:
        target_h = statistics.median(forced)
        recommended = max(0, int(args.effective_window * (1 - target_h) - args.reserved_output))
        print("Recommendation:")
        print(f"  effective_window  = {args.effective_window:,} tokens")
        print(f"  reserved_output   = {args.reserved_output:,} tokens")
        print(f"  median FORCED at headroom_frac = {target_h:.3f}")
        print(f"  → set autoCompactWindow ≈ {recommended:,} tokens")
        print()
        print("This aligns the native auto-compact trigger with where the live")
        print("policy already wants to compact, so the PreCompact gate has the")
        print("right call to make (allow+snapshot vs block) at every native attempt.")
    else:
        print("Recommendation: insufficient FORCED_COMPACT samples to tune.")
        print("Run the agent for more sessions, then re-run this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
