# Cross-Domain Analogy Interpretation Track

This is the differentiator from a junior analyst. After producing the numerical result, you owe the user **one** non-trivial cross-disciplinary analogy that re-frames the finding from outside the business's own vocabulary.

The point is not to sound clever. The point is that a good cross-domain analogy generates new hypotheses you would not have asked from inside the business.

---

## Anti-template-laundering protocol (read BEFORE producing an analogy)

The single most common failure mode is **template laundering**: the agent gets attracted to a template name from `analogy-templates.md`, then back-fills a mapping that looks plausible but isn't actually supported by the data. The output passes all 4 acceptance tests on the surface, while the underlying claim is unfounded.

Two hard rules to prevent this. **Both** must be followed in order, before any template is named:

### Rule 1: Observed structural signature first, template second

Before opening `analogy-templates.md`, write down the **observed structural signature** of the finding *in its own terms*, using only the data:

- Shape of the distribution (linear / log-linear / power-law / sigmoid / step / oscillation)
- Direction and rate of change over time / dose / exposure
- Where saturation, decay, or threshold effects appear (and at what value)
- Whether the relationship is symmetric or asymmetric
- Whether it depends on history (path-dependent) or only on current state
- Whether it scales with size of input or is invariant

Only after this signature is written may you browse templates. If you select a template whose abstract structure does not match the signature you wrote, reject it and try again. **Never** select a template first and then describe the data.

### Rule 2: Every analogy must include a disconfirming test

For every produced analogy, you must write one explicit sentence: *"This analogy is wrong if we observe [specific result]."* The disconfirming result must be something the data could in principle show. If you cannot name a disconfirmer, the analogy is unfalsifiable — skip it.

This rule is what turns the analogy from "high-grade metaphor" into "testable cross-domain explanation." It is also the cheapest single intervention against template laundering, because most laundered analogies cannot survive the disconfirming-sentence step.

---

## The 4 acceptance tests

A produced analogy must pass **all four**. If it fails any one, rewrite or skip — do not ship.

### Test 1: Structural mapping (not surface similarity)

You must be able to write the mapping as a table:

```
Business object       ↔  Analogy object
A → B in business     ↔  C → D in analogy
```

Surface similarity ("they both grow over time") is not enough. You must map at least 2 entities and 1 relation.

**Pass example**: "Tweets that already have likes attract more new likes via algorithmic boost ↔ nodes with high degree attract more new edges via preferential attachment in network growth."
- Map: tweet ↔ node; like ↔ edge; algorithmic boost ↔ proportional probability of attachment
- Relation: existing-attention → future-attention

**Fail example**: "Viral tweets grow like a snowball." (No mapping. Just a vibe.)

### Test 2: Generates a new hypothesis

The analogy must let you make a prediction or design an experiment you would not have proposed without it.

**Pass example**: Preferential attachment predicts a power-law degree distribution. → Hypothesis: tweet engagement should also follow a power-law (not normal). → Test: fit log-log to your engagement counts; does the slope hold?

**Fail example**: "It's like a snowball" — what new hypothesis does this generate? None.

### Test 3: States its boundary

Every analogy breaks somewhere. Name where.

**Pass example**: "Preferential attachment assumes nodes can attract edges symmetrically over time. Twitter timeline decay (tweets become invisible after ~24h) means the mechanism only operates within the first day. After that, no further preferential dynamics. So the power law should hold for first-day engagement but not for cumulative engagement weeks later."

**Fail example**: presenting the analogy as if it explains everything.

### Test 4: Avoids restatement

The analogy must NOT be a paraphrase of the business conclusion in fancier words. It must add a new viewpoint.

**Fail example**: business finding = "engagement falls off after a few hours." Analogy = "this is exponential decay." → This is not an analogy, just a math name. It restates the finding, doesn't add hypotheses.

**Pass example**: business finding = "the same ad creative shows decreasing CTR after the third impression to a user." Analogy = "ecological niche saturation: each repeat impression occupies the same cognitive niche, so marginal information gain → 0; it is not just satiation but specifically *competition for attention from the user's own anti-novelty filter*."
- This adds: the failure mode is information-theoretic, not motivational. → New hypothesis: rotating creative variations should restore CTR even with the same product (a niche-rotation prediction the "users got bored" framing wouldn't generate).

## Three reference cases (do not just imitate; understand the pattern)

### Case A — Tweet engagement power law
- Business observation: a small fraction of tweets earn most of the new follows; once a tweet "hits," subsequent tweets see lifted reach
- ✅ Good analogy: **preferential attachment / cumulative advantage** in network growth
- ❌ Bad: "snowball effect"
- New hypothesis it generates: log-log distribution of new-follows-per-tweet should be linear; intervention to boost early visibility (e.g. self-quote) should have super-linear payoff

### Case B — Early-user retention
- Business observation: new users' first-3-day behavior almost fully determines long-term retention; later interventions barely move the needle
- ✅ Good analogy: **developmental biology critical period** (e.g. song learning in zebra finch); or **early-feedback lock-in** in cybernetics
- ❌ Bad: "first impressions matter"
- New hypothesis: there is a window after which the marginal value of any intervention drops by an order of magnitude; this implies onboarding should be over-resourced (uneconomical-looking) within the window and underresourced after it

### Case C — Ad creative decay
- Business observation: same creative starts at high ROI; CTR and conversion both fall as frequency increases
- ✅ Good analogy: **ecological niche saturation** + **information-theoretic novelty decay** (each repeat impression carries near-zero new bits)
- ❌ Bad: "users got bored"
- New hypothesis: rotating creative variants that occupy *different* attention-niches (humor / data / social-proof) should outperform variants that compete for the *same* niche

## How to produce one (your work loop)

0. **Write the observed structural signature first** (per Rule 1 above) — distribution shape, direction, saturation/decay/threshold, symmetry, path-dependence, scaling
1. **Name the abstract structure** of the finding: power-law? saturation curve? phase transition? feedback loop? optimal-stopping? exploration-exploitation? oscillation? stochastic resonance?
2. Browse `references/analogy-templates.md` for candidate cross-domain instances of *that* structure (not a structure whose name you found attractive)
3. Pick the one with the closest *relational* match (not surface match). If no template matches the signature you wrote in step 0, stop and skip with reason.
4. Write the structural mapping (Test 1)
5. Write the new hypothesis (Test 2)
6. Write the boundary (Test 3)
7. Write the disconfirming test (per Rule 2 above): "This analogy is wrong if we observe ____."
8. Re-read against Test 4 — am I just restating the finding?

If any step 5/6/7/8 fails, **skip the analogy entirely and say so**. A forced bad analogy ("things grow like other things grow") is worse than no analogy.

---

## Required output format (4-test self-audit)

After completing the work loop, output the self-audit explicitly. This is non-negotiable — Track B is incomplete without it.

```
### Cross-domain analogy: [name of structural pattern, e.g. "preferential attachment in network growth"]

Observed structural signature (from data, before template was chosen):
[1-2 sentences]

Structural mapping:
- [business object] ↔ [analogy object]
- [business object] ↔ [analogy object]
- [business relation] ↔ [analogy relation]

New hypothesis it generates:
[one testable prediction]

Boundary:
[where the analogy breaks down]

Disconfirming test:
"This analogy is wrong if we observe ____."

4-test self-audit:
- Test 1 (structural mapping):  ✅/❌ — [1 sentence evidence]
- Test 2 (new hypothesis):      ✅/❌ — [the hypothesis as a testable prediction]
- Test 3 (boundary):            ✅/❌ — [where it breaks]
- Test 4 (not restatement):     ✅/❌ — [what it adds beyond the business conclusion]
```

If any test is ❌, replace the entire block with: `Cross-domain analogy: SKIPPED. [one-sentence reason].`

## When to skip with reason

It is professional to write: *"No cross-domain analogy passes all 4 acceptance tests for this finding. The pattern is too local to the business mechanism (e.g., a one-off platform policy change) to generalize."*

Skipping with reason demonstrates the discipline. Forcing a bad analogy demonstrates the opposite.
