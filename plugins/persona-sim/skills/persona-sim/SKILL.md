---
name: persona-sim
description: Simulate feedback from statistically grounded virtual human populations. Use when the user wants to get product or copy feedback from a panel of diverse personas, predict group opinions or voting behavior, run social-experiment sandboxes, or compute a semantic gradient (SGO) for A/B ranking. Also triggers on mentions of Nemotron-Personas, PersonaHub, synthetic population, generative agents, silicon sample, LLM survey simulation, persuadable middle, SGO, social sandbox, 用虚拟人群测试, 模拟民意, 投票预测模拟.
---

# Persona Sim

Simulate feedback from census-grounded virtual populations. Five layers, each independently replaceable:

```
L5 Scenario adapters (product-feedback-sim / vote-predict / social-sandbox)   thin wrappers
L4 Simulation engine (sim_engine.py — SGO: panel -> score -> persuadable middle -> anchored gradient)
L3 LLM router        (llm_router.py — config-driven; default Haiku 4.5 + prompt cache; Sonnet for gradient)
L2 Persona sampler   (sampler.py    — unified sample_personas(n, filters, source, mode))
L1 Persona store     (~/.claude/data/personas/ + manifest.json)
```

## First-time setup (not optional)

Dependencies and config live **outside the skill** under `~/.claude/data/personas/` so sharing the skill never leaks keys. See `SETUP.md` for the full walk-through. Short version:

```bash
mkdir -p ~/.claude/data/personas
cp ~/.claude/skills/persona-sim/data/config.example.json ~/.claude/data/personas/config.json
cp ~/.claude/skills/persona-sim/data/manifest.json ~/.claude/data/personas/manifest.json
# Edit config.json — set `provider` and fill api_key / base_url for your chosen block

python3 -m venv ~/.claude/data/personas/.venv
~/.claude/data/personas/.venv/bin/pip install -r ~/.claude/skills/persona-sim/requirements.txt
```

Always invoke with the venv interpreter:
```bash
~/.claude/data/personas/.venv/bin/python <script>
```

## When to use

- "Score this copy/feature with 100 virtual target users" → `sim_engine.panel_score()`
- "Find the persuadable middle for this tweet" → `sim_engine.sgo()`
- "Predict the US opinion distribution for this policy" → `panel_score()` + segment breakdown
- "Which of these two pricing variants wins?" → `sgo()` with anchored counterfactual probes

## In-code API

```python
from persona_sim import sampler, sim_engine

# Sample 30 targeted personas (streaming — no local download needed)
panel = sampler.sample_personas(
    n=30,
    filters={"occupation_isco": "software", "age": (22, 55)},  # see filter semantics below
    source="nemotron_usa",
    mode="stream",
)

# Single-version scoring
result = sim_engine.panel_score(panel, target="Copy or product description here")
# -> {"n", "results", "aggregate": {"histogram", "median", "iqr", "entropy",
#    "multi_modal", "disagreement_flag", "by_gender", "by_age", "by_region"},
#    "warning": "Simulation only..."}

# SGO gradient — rank candidates by how much they shift the persuadable middle
ranked = sim_engine.sgo(
    panel,
    target="original version",
    candidates=["variant A", "variant B"],
    goal="maximize paid conversions",
)
# -> {"base", "persuadable_middle", "ranking": [{"candidate", "avg_score_lift", ...}]}
```

## Filter semantics (commonly misused)

`sample_personas(filters={...})` interprets values by Python type:

| Filter value | Match behavior |
|---|---|
| `(low, high)` tuple of numbers | inclusive range (`low <= rv <= high`) |
| `[...]` list | membership (`rv in list`) |
| `"substring"` string | case-insensitive substring in `str(rv)` — great for free-text `occupation_isco` |
| other (int/str literal) | equality |

Missing field on row (`rv is None`) → row rejected.

**Default `adults_only=True`** injects `age=(18, 120)` unless you pass your own `age` filter. Nemotron data includes children with synthetic `professional_persona` fields — always filter them out for work/product panels.

## Six non-obvious rules (READ BEFORE ANY CHANGE)

1. **Narrative > demographic stub.** Park et al. 2024 proved demographic-only prompts amplify stereotypes. `_persona_card` puts Nemotron's long `professional_persona` narrative FIRST; demographics are a footnote.
2. **Never output a single mean.** Output distribution + segment breakdown + `disagreement_flag`. High variance = signal, not noise.
3. **Prompt caching is mandatory for panels.** System + task are identical across N personas; with cache_read at 10% of base, a 50-persona panel costs ~1/10 of naive. Cache breakpoint goes BEFORE the persona card (which varies per row).
4. **SGO uses ANCHORED counterfactuals.** The probe re-injects the persona's original score + reason so the delta is causal (attribution to the change), not two independent scorings. See `_anchored_delta_one` in `sim_engine.py`.
5. **Persuadable middle = score 4–7 only.** 1–3 never buys; 8+ already sold. Don't waste LLM calls on extremes.
6. **Calibration disclaimer is required.** Tjuatja 2311.04076 + Bisbee 2024 proved LLM synthetic samples lack human response biases (acquiescence, anchoring, framing). Every public-facing result must include the `warning` field.

## Empirical validation

Smoke-tested on Nemotron-USA + Haiku 4.5:

| Panel | Filter | Median | IQR | Persuadable middle |
|---|---|---|---|---|
| Generic (n=5) | none | 2 | — | 0/5 |
| Software devs (n=30) | `occupation_isco~"software", age (22,55)` | **7** | (7, 8) | **19/30** |

Same product, different panel → median shifts from 2 to 7. Personas play roles faithfully; single dissenter at 3 had concrete reasoning. SGO has enough signal when targeting is correct.

## LLM routing

Active provider set in `~/.claude/data/personas/config.json` → `provider` field. Three shapes supported:

- `anthropic` (native) — Anthropic SDK with `ANTHROPIC_API_KEY`; supports prompt caching
- `anthropic` with `base_url` override — for custom Anthropic-compatible gateways (enterprise proxies, Vertex-routed gateways, etc.)
- `openai` (gateway-compatible) — OpenRouter, vLLM, Together, Groq, etc.

Escalate to `gradient_model` (default Sonnet 4.5) for:
- SGO anchored counterfactual (fine-grained semantic judgment)
- Bias audit probes (framing / order / authority)
- Long-narrative fidelity eval

See `data/config.example.json` for template config blocks.

## Data fetch flow (streaming works without any download)

MVP runs entirely on HF streaming — no local copy needed. Only fetch when you're running many panels and want the speed:

```bash
~/.claude/data/personas/.venv/bin/python -m persona_sim.fetch nemotron_usa
```

`manifest.json` per-dataset `default_mode`:
- `local` → prompts to download on first use
- `stream` → direct HF streaming (default for MVP)
- `ask` → shows license + manual-download URL

`redistribute: false` entries (most Nemotron / PersonaHub / WVS / CGSS) are NEVER bundled when sharing the skill — each user fetches them per license terms.

## Bias audit

`lib/bias_audit.py` tests whether LLM personas reproduce four known human biases:

| Probe | What it measures | Human typical | LLM typical |
|---|---|---|---|
| framing | Tversky-Kahneman gain/loss reframe | +0.25 to +0.50 shift | ~0 (none) |
| acquiescence | agree-bias on symmetric statements | +0.10 to +0.20 excess | ~0 (logical) |
| order | primacy/recency on option list | 0.05-0.15 TV distance | <0.03 |
| authority | "experts say" prefix shift | +0.10 to +0.20 | +0.00 to +0.05 |

Results flagged with calibration warnings. Run before publishing any survey-style prediction.

## Subagent pattern (for n > 200)

```python
Task(subagent_type="general-purpose",
     prompt=f"Run persona_sim.panel_score on ids {ids[0:50]}, target={target!r}. Return distribution only.")
```
Main agent aggregates per-slice distributions to avoid context bloat.

## Known gaps

- Chinese persona data pipeline is scaffolded (`references/chinese_pipeline.md`) but not implemented — see that file for the 3-source recipe (census + WVS + LLM narrative).
- `demo_corr` suite requires persona income field (not in Nemotron); currently skips that dimension.
- ANES demographic correlation reference values are approximations — re-verify against the official codebook before publishing.

## Resources

- `lib/{fetch,sampler,llm_router,sim_engine,aggregator,bias_audit,ipf}.py` — core layers
- `prompts/persona_system.md` — narrative-first system prompt with anti-agreeable guardrails
- `prompts/sgo_gradient.md` — anchored counterfactual template
- `eval/run_eval.py` + `eval/*.json` — 6-suite score card (gss_20q, bfi44, test_retest, diversity, demo_corr, bias_audit)
- `references/methodology.md` — Park 2024, Santurkar, SGO, CoBRA, Tjuatja synthesis
- `references/datasets.md` — dataset inventory + field maps
- `references/chinese_pipeline.md` — scaffold for Chinese persona synthesis
- `scripts/smoke_test.py`, `scripts/smoke_test2.py` — minimal working examples
- `SETUP.md` — venv + config bootstrap
- `requirements.txt` — pinned deps
- `data/manifest.json` — dataset registry (safe to share)
- `data/config.example.json` — sanitized LLM config template

## Eval loop

```bash
cd ~/.claude/skills/persona-sim
~/.claude/data/personas/.venv/bin/python eval/run_eval.py \
    --suite gss_20q,bfi44,test_retest,diversity,demo_corr,bias_audit \
    --n 30
# -> eval/reports/score_card_YYYYMMDD.json
```

Target: overall >= 0.75. If any dimension fails, that dimension is the highest-priority edit target for the next iteration.

## Scenario skills

Three thin scenario wrappers ship alongside the core. They route into `persona-sim`'s API with opinionated defaults for common use cases:

- **`product-feedback-sim`** — SGO ranking for product/copy/pricing candidates
- **`vote-predict`** — categorical opinion prediction with IPF post-stratification
- **`social-sandbox`** — what-if experiments with open-ended narrative clustering

Each has its own `SKILL.md` with a full recipe.
