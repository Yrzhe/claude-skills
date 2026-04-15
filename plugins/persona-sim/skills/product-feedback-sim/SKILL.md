---
name: product-feedback-sim
description: Get structured feedback on a product, copy, pricing, or feature from a simulated panel of target users. Use when the user wants to rank A/B candidates, find persuadable-middle users, or compute a semantic gradient before shipping. Triggers on 产品反馈模拟, A/B 排序, SGO 梯度, persuadable middle, 50 个虚拟用户打分, 看看目标用户怎么想.
---

# Product Feedback Sim

Thin scenario wrapper around `persona-sim`. Runs SGO on a product/copy candidate against a target user panel.

## Recipe

```python
import sys
sys.path.insert(0, str(__import__('pathlib').Path.home() / '.claude/skills/persona-sim'))
from lib import sampler, sim_engine

# 1. Define target audience
panel = sampler.sample_personas(
    n=30,                                              # 30-50 is cost-effective
    filters={"occupation_isco": "software", "age": (25, 50)},  # substring match on occupation
    source="nemotron_usa",
    mode="stream",
)

# 2. Single-version feedback (fast)
base = sim_engine.panel_score(
    panel,
    target="<your product/copy/feature description>",
    goal="<what you want to maximize, e.g. paid conversions>",
)
# → aggregate.histogram / median / iqr / disagreement_flag / by_age / by_gender

# 3. A/B (or N-way) gradient ranking — uses anchored counterfactuals on persuadable middle
ranked = sim_engine.sgo(
    panel,
    target="<original version>",
    candidates=["variant A", "variant B", "variant C"],
    goal="<same goal>",
)
# → ranking: [{"candidate", "avg_score_lift", "n_probed"}, ...]  sorted descending
```

## Decision rules

- **Use `panel_score` only** when you want to understand a single version (no alternatives yet).
- **Use `sgo` ONLY when there's a persuadable middle** (score 4-7). If base median is ≤3 or ≥8, SGO has no signal — iterate on the base version first.
- **n=30 minimum** for stable distribution; n=50-100 if you need tight CIs.
- **Always expose `disagreement_flag`** to the user — high-variance results are signal, not noise.
- **Always prepend the disclaimer** from `result["warning"]` when showing output.

## Target selection guidance

If the user says "我的产品用户是 X"：

| User type | Filter expression |
|---|---|
| 软件开发者 | `{"occupation_isco": "software"}` |
| 企业决策者 | `{"occupation_isco": "manager", "age": (35, 60)}` |
| Gen Z | `{"age": (18, 27)}` |
| 大城市高收入 | `{"region": ["NY","CA","MA","WA"], "age": (28, 50)}` |
| 老年人医疗产品 | `{"age": (65, 100), "adults_only": False}`（覆盖默认的成人限制无需） |

Ambiguous user type → use no occupation filter, let distribution surface the signal.

## Cost note

Haiku 4.5 via Colorist at ~$0.003/call. A 30-person panel + 3-candidate SGO = 30 + (persuadable × 3) ≈ 50-100 calls ≈ $0.15-0.30 per full run.

## See also

- `~/.claude/skills/persona-sim/SKILL.md` for the underlying API and rules
- `vote-predict` for policy/voting, `social-sandbox` for social experiments
