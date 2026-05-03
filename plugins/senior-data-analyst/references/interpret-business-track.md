# Business-Grounded Interpretation Track

Translate the numerical result back into the business language and the original decision. This is the *non*-clever track — straightforward but easy to skip in favor of the cooler analogy.

Both interpretation tracks (this one + analogy) are required. Numbers without business interpretation are not analysis; they are a math homework dump.

---

## What this track produces

A 3-5 sentence block answering, in the user's own vocabulary:

1. **What does this number mean for the business question?**
2. **What changes in our decision because of this answer vs. the opposite answer?**
3. **What does this not say?** (the limit on the inference)

If you can't answer (1) without using stats jargon, you haven't translated yet — keep working.

---

## Workflow

### Step 1: Restate the user's original question

In one sentence, no jargon. Pull from the Step 1 INTAKE brief.

If the question was "what factors drive 涨粉," do not write "we performed a multivariate analysis"; write "What variables in our data best explain new follows per tweet?"

### Step 2: Translate every numerical finding back to business units

| Statistical finding | Business translation |
|---|---|
| `Pearson r = 0.42` between Bookmarks and New follows, p < 0.001, n=506 | "Tweets that get bookmarked more tend to get more new follows. The pattern is moderate-strength and unlikely to be coincidence." |
| `Cohen's d = 0.3` for tweets posted in H16-18 UTC vs H02-05 UTC | "Tweets in the evening UTC window get a small but real lift in engagement compared to night-window tweets — about a third of a standard deviation." |
| `R² = 0.18` for the multivariate regression | "Our model explains about 18% of the variation in new follows. Most of what drives follows is not in this dataset." |
| `Top PCA component = 'engagement composite' (loadings: Likes 0.6, Bookmarks 0.55, Replies 0.45)` | "There's one underlying 'engagement' dimension that combines likes, bookmarks, and replies — they tend to move together." |

The discipline: **never report a number without its business meaning in the same sentence**.

### Step 3: Use dbs-deconstruct when concepts are blurry

If the finding involves a concept that has fuzzy meaning ("engagement," "quality content," "viral," "loyal user"), call `dbs-deconstruct` to pin it down before claiming the analysis says anything about that concept.

Example: a finding says "tweets with higher engagement get more new follows." But what is "engagement"? Likes? Likes + bookmarks? PV? — different definitions yield different policy implications. Use dbs-deconstruct to pin the operational definition. Then re-state the finding using only the pinned definition.

### Step 4: Use dbs-diagnosis when the analysis touches business-model questions

If the analysis is about a business-model decision (pricing, positioning, channel choice, who-to-serve), call `dbs-diagnosis`. Statistical findings tell you *what's true in the data*; dbs-diagnosis tells you *what would be true about the business model regardless of this data*. Both matter; statistics alone is naive.

Example: analysis finds "high-bookmark tweets correlate with new follows." dbs-diagnosis layer asks: *but is bookmark-driven growth aligned with our business model?* Maybe bookmarks bring lurkers who never buy. The number is right; the implication needs a business-model lens.

### Step 5: Write the "what changes in our decision" sentence

This is the bottleneck of analysis quality. The point of running the numbers is to inform a decision. State what the user should do differently because of the finding vs. the opposite finding.

Format:
> "If this finding holds, the next move is X. If it had gone the other way, we'd have considered Y. Either way, the action becomes more concrete."

If you cannot write this sentence, the question may have been mis-framed in Step 1 INTAKE. Loop back.

### Step 6: Write the "what this does NOT say" sentence

Every analysis has limits. State them:

- "This is observational; we cannot conclude that bookmarks *cause* follows."
- "Sample is the last 6 months; if the algorithm changed in that window, results may not generalize."
- "We dropped tweets with <100 impressions; conclusions don't apply to low-reach posts."
- "Effect size is modest (R²=0.18); most variance in follows is unexplained — there's a lot we're not measuring."

A senior analyst names these proactively. A junior analyst gets caught when a stakeholder asks.

---

## Common amateur failures (avoid)

- **Statistical jargon survives into the business interpretation.** "We rejected H0 at α=0.05" is not a business finding.
- **Effect direction without effect size.** "Bookmarks predict follows" — by how much? r=0.05 is uninteresting; r=0.5 is huge.
- **Ignoring the decision frame.** A correct number that doesn't change anyone's decision is decoration.
- **Pretending the analysis says more than it does.** "This proves bookmarks cause follows" — observational data cannot prove causation.
- **Skipping the limits sentence.** Stakeholders will find the limits later; better to surface them now and stay credible.

---

## Compact output template

When all 6 workflow steps are done, the business-grounded interpretation should fit in this template:

```
Question: <restated user question, 1 line>

Answer: <plain-language finding with business units, 1-2 sentences>

What changes: <decision implication, 1 sentence>

What this does NOT say: <2-3 named limits>
```

Hand off to Step 7 (DELIVERY) — this template plus the analogy track output plus the evidence section becomes the final report.
