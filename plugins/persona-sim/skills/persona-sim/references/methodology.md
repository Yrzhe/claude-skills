# Persona Simulation Methodology (Condensed)

Read this before any change to prompts, aggregation, or SGO logic.

## Core findings

1. **Narrative > demographic stub** (Park et al. 2024, arxiv 2411.10109). 2-hour interview transcripts → agent replicates human GSS answers at 85% of human test-retest reliability. Demographic stubs amplify stereotypes — Nemotron's long-form `professional_persona` etc. are the correct backbone.

2. **Known failure modes**:
   - Left-leaning bias (Santurkar 2303.17548) — RLHF models drift toward US Dem/highly-educated. Census-ground the panel; don't let LLM invent personas.
   - Mode collapse (Anthropic 2306.16388) — cross-country personas still produce convergent answers. Mitigate: temp 0.9-1.0, force distractors, Worst-of-N.
   - Persona leakage — long dialogues revert to assistant voice. Mitigate: re-inject system every N turns; `<persona>` XML tags.
   - Sycophancy — silicon sampling (Argyle 2209.06899): reframe the question multiple ways and pool.
   - Missing real survey biases — Tjuatja 2311.04076: LLMs don't show acquiescence/anchoring like real respondents. Bisbee 2024: mode concentration, long tail missing. **Disclaimer is mandatory**.

3. **SGO algorithm** (Eric Xu, github.com/xuy/sgo):
   - Panel 30–80 (default ~47).
   - Each persona scores 1-10 with reasoning + concerns.
   - **Only persuadable middle (4-7) gets counterfactual probes** — 1-3 never buy, 8+ already sold.
   - Gradient = vector-Jacobian: `∇_j = Σ v_i · (score_new - score_orig)`, weighted by goal-relevance v_i.
   - Output: ranked Δ, not absolute predictions.

4. **Aggregation rules**:
   - Never output a single mean.
   - Always histogram + IQR + segment breakdown (gender, age, region).
   - Flag multi-modal (dip test / local maxima).
   - High variance is signal — social disagreement is a finding.
   - Post-stratify with real census weights (PUMS / 七普) via IPF if panel is not census-sampled.

## Key papers

- Park et al. 2024, *Generative Agent Simulations of 1,000 People*, arxiv 2411.10109
- Santurkar et al. 2023, *Whose Opinions Do LLMs Reflect?*, arxiv 2303.17548
- Anthropic 2023, *Towards Measuring the Representation of Subjective Global Opinions*, arxiv 2306.16388
- Argyle et al. 2022, *Out of One, Many*, arxiv 2209.06899
- Tjuatja et al. 2023, *Do LLMs Exhibit Human-like Response Biases?*, arxiv 2311.04076
- Hewitt et al. 2024, *Predicting Social Science Experiments*, arxiv 2407.07337
- Liu et al. 2025, *CoBRA: Controlling Cognitive Biases*, arxiv 2509.13588
- Anthropic 2025, *Values in the Wild*, arxiv 2504.15236

## Architecture invariants

1. Census-grounded persona pool — not LLM-generated personas.
2. Narrative-rich prompt (inject Nemotron persona fields; don't synthesize traits).
3. Built-in bias audit layer (framing/order/authority probes).
4. Output distribution + segment breakdown, never single mean.
5. Counterfactual gradient for actionable ranking (not absolute prediction).
6. Disclaimer on every result.
