---
name: social-sandbox
description: Run a what-if social experiment — inject a policy, event, or information shock and observe how a simulated population responds. Use for hypothesis generation (not ground truth) on questions like "what if minimum wage doubled", "how would users react if we added feature X", "which demographics push back first". Triggers on 社会实验, 沙盒模拟, what-if, 如果 X 发生了会怎样, 反事实模拟, counterfactual experiment.
---

# Social Sandbox

Thin scenario wrapper for counterfactual social simulation. Differs from `product-feedback` (scores products) and `vote-predict` (categorical votes) — this produces **open-ended qualitative narratives** from the panel, then clusters them.

## Recipe

```python
import sys
sys.path.insert(0, str(__import__('pathlib').Path.home() / '.claude/skills/persona-sim'))
from lib import sampler
from lib.sim_engine import SYSTEM_PROMPT, _persona_card
from lib.llm_router import generate
from concurrent.futures import ThreadPoolExecutor

# 1. Sample diverse panel (wider demographic spread than product-feedback)
panel = sampler.sample_personas(n=50, source="nemotron_usa", mode="stream")

# 2. Design the scenario — use past tense as if it already happened
scenario = """
Congress has just passed a law raising the federal minimum wage to $22/hour
nationwide, effective in 6 months. You've seen the news today.
"""

# 3. Ask each persona: immediate reaction + 6-month expectation + what they plan to do
def probe(persona):
    task = (f"{scenario}\n\n"
            "Respond as yourself, in 3 sentences:\n"
            "(1) Your immediate emotional reaction.\n"
            "(2) What you expect to happen in your life over 6 months.\n"
            "(3) What (if anything) you plan to do in response.")
    return generate(system=SYSTEM_PROMPT, persona_card=_persona_card(persona),
                    task=task, tier="default", max_tokens=400)

with ThreadPoolExecutor(max_workers=8) as ex:
    narratives = list(ex.map(probe, panel))

# 4. Cluster the narratives (use Sonnet for this, not Haiku)
# Pass the 50 narratives + panel demographics to Sonnet:
# "Identify 3-5 distinct reaction archetypes. For each: label, % of panel, key demographic correlates,
#  sample quote."
```

## What this skill is for

- **Hypothesis generation** before designing a real survey
- **Finding dimensions of disagreement** you hadn't thought of
- **Surfacing minority voices** that demographic-only polling would miss
- **Stress-testing messaging** against diverse interpretations

## What this skill is NOT for

- Predicting actual policy outcomes (LLM personas don't model emergence, network effects, or real economic constraints)
- Replacing real qualitative research (LLM can't replicate lived-experience nuance)
- High-stakes decisions — treat outputs as "interesting starting points" not evidence

## Output structure

Always produce:

1. **3-5 archetypes** with % of panel and 1-2 sample quotes each
2. **Dimensional axes** of disagreement (e.g., "rural vs urban", "service workers vs knowledge workers")
3. **Surprising/outlier reactions** — these are often the most valuable signal
4. **Calibration warning** from `bias_audit` — note that LLM personas under-represent certain human biases

## Cost note

n=50 × 1 open-ended call at Haiku + 1 Sonnet clustering call ≈ $0.50-1 per sandbox run.

## See also

- `persona-sim/references/methodology.md` — Park 2024 narrative-first finding is especially relevant here
- `persona-sim/lib/aggregator.py` — useful for quantitative follow-ups on archetype proportions
