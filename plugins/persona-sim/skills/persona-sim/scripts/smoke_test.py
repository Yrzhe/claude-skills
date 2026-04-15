"""Smoke test: stream 5 Nemotron personas + score 1 target + aggregate. No local downloads."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import sampler, sim_engine


def main():
    target = (
        "Pricing: $29/month vs $49/month for an AI coding copilot with unlimited chat, "
        "repo indexing, and model switching. Which tier would you pick and why?"
    )
    print(">>> Streaming 5 Nemotron-USA personas (no local download)...")
    panel = sampler.sample_personas(n=5, source="nemotron_usa", mode="stream", seed=42)
    print(f"    Got {len(panel)} personas.")
    for i, p in enumerate(panel):
        print(f"    [{i}] age={p.get('age')} gender={p.get('gender')} region={p.get('region')} occ={p.get('occupation_isco')}")
        narr = (p.get("narrative") or "")[:120]
        print(f"        narrative: {narr}...")

    print("\n>>> Scoring target via Colorist gateway → Haiku 4.5...")
    result = sim_engine.panel_score(panel, target=target, max_workers=3)
    print(f"    n={result['n']}  n_failed={result['n_failed']}")
    print(f"    warning: {result['warning']}")

    print("\n>>> Aggregate:")
    print(json.dumps(result["aggregate"], indent=2, ensure_ascii=False))

    print("\n>>> Raw scores + reasons:")
    for r in result["results"]:
        reason = ""
        try:
            obj = json.loads(r["raw"])
            reason = obj.get("reason", "")[:100]
        except Exception:
            reason = r["raw"][:100]
        print(f"    score={r['score']}  reason={reason}")


if __name__ == "__main__":
    main()
