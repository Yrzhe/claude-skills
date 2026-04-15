---
name: vote-predict
description: Predict how a target population would vote, respond to a policy, or react to a political message. Use when the user wants a distribution (not a winner-take-all answer) across demographic segments, with calibration disclaimers. Triggers on 投票预测, 民意模拟, policy response, 政策反应, 选举模拟, 民意分布, 某群体怎么看.
---

# Vote Predict

Thin scenario wrapper for opinion/vote simulation. Unlike product-feedback which scores 1-10, vote-predict uses **categorical choices** and **post-stratification** so the distribution maps to population-level prediction.

## Recipe

```python
import sys, json
sys.path.insert(0, str(__import__('pathlib').Path.home() / '.claude/skills/persona-sim'))
from lib import sampler, ipf, aggregator
from lib.sim_engine import SYSTEM_PROMPT, _persona_card
from lib.llm_router import generate

# 1. Sample a large panel (census-matched after IPF)
panel = sampler.sample_personas(n=100, source="nemotron_usa", mode="stream")

# 2. Compute IPF weights to match target population marginals
weights = ipf.ipf_weights(
    panel,
    targets={
        "age": {"<25": 0.12, "25-39": 0.26, "40-59": 0.33, "60+": 0.29},  # US adult
        "gender": {"male": 0.49, "female": 0.51},
    },
    bucketers={"gender": lambda x: x.strip().lower() if isinstance(x, str) else None},
)

# 3. Ask each persona the question
def ask(persona, question, options):
    task = (f"{question}\nChoose ONE of: {options}.\n"
            f'Respond JSON: {{"vote": "<choice>"}}')
    resp = generate(system=SYSTEM_PROMPT, persona_card=_persona_card(persona),
                    task=task, tier="default", max_tokens=100)
    # parse JSON (see eval/run_eval._parse_json_answer)
    ...

# 4. Aggregate with weights
# Option-wise: weighted_share[option] = sum(weights[i] for i where vote[i]==option) / sum(weights)
```

## Core rules

1. **NEVER output a single "winner" percentage as the answer.** Output the full distribution + margin of uncertainty.
2. **Always apply IPF weights** when the base panel doesn't match the target population (almost always for Nemotron).
3. **Report segment breakdowns** (age × vote, education × vote) — even if the topline says 52/48, the story is in the segments.
4. **Attach bias audit warning** from `lib/bias_audit.py` — humans show acquiescence and framing biases that LLM personas do not. Flag the prediction as "LLM-synthetic, not a replacement for real polling".
5. **Flag multi-modal results** — if `aggregator._dip_test_proxy` says multi-modal, the population is split and averaging misleads.

## Calibration priors

Known US baselines from `eval/gss_20q.json` can sanity-check predictions. If your simulated distribution is >0.2 JS-divergence from the reference for a similar question, **the simulation is not trustworthy for this topic**. Run eval first.

## Do NOT use this skill for

- Real election forecasting (use prediction markets + polling aggregators)
- High-stakes policy decisions on single outcome (use this for hypothesis generation only)
- Issues where real-world events have shifted distributions after the Nemotron training cutoff (2024 or earlier)

## See also

- `persona-sim/lib/ipf.py` — post-stratification implementation
- `persona-sim/lib/bias_audit.py` — run before publishing any prediction
- `persona-sim/eval/gss_20q.json` — baseline attitude distributions
