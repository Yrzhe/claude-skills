"""Smoke test 2: occupation-targeted panel.

Goal: verify that when we target the RIGHT audience (software developers), panel scores
shift into a meaningful range (5-8 instead of 1-3), and SGO's persuadable middle is findable.
"""
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
    # Filter by occupation substring — Nemotron values like "software_engineer", "software_developer", etc.
    # Panel size 30: large enough for distribution signal, small enough to run in ~1 min under Haiku.
    n = 30
    print(f">>> Streaming {n} Nemotron-USA personas filtered by occupation ~ 'software'...")
    panel = sampler.sample_personas(
        n=n,
        filters={"occupation_isco": "software", "age": (22, 55)},
        source="nemotron_usa",
        mode="stream",
        seed=7,
    )
    print(f"    Got {len(panel)} personas.")
    for i, p in enumerate(panel[:5]):
        print(f"    [{i}] age={p.get('age')} {p.get('gender')} {p.get('region')} occ={p.get('occupation_isco')}")
    if len(panel) > 5:
        print(f"    ... and {len(panel)-5} more")

    if len(panel) < 5:
        print("ABORT: not enough matching personas (stream scan cap too tight?).")
        sys.exit(1)

    print(f"\n>>> Scoring via Haiku 4.5 (this will make {len(panel)} API calls)...")
    result = sim_engine.panel_score(panel, target=target, max_workers=6)
    print(f"    n={result['n']}  n_failed={result['n_failed']}")

    print("\n>>> Aggregate (should show scores shifted UP vs generic panel):")
    agg = result["aggregate"]
    print(f"    median={agg['median']}  iqr={agg['iqr']}  entropy={agg['entropy']}")
    print(f"    multi_modal={agg['multi_modal']}  disagreement={agg['disagreement_flag']}")
    print(f"    histogram: {agg['histogram']}")

    scores = [r["score"] for r in result["results"] if r["score"] is not None]
    in_middle = sum(1 for s in scores if 4 <= s <= 7)
    print(f"\n    Persuadable middle (4-7): {in_middle}/{len(scores)} "
          f"— SGO would {'' if in_middle >= 5 else 'NOT '}have enough signal")

    print(f"\n    warning: {result['warning']}")


if __name__ == "__main__":
    main()
