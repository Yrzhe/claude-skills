# Reporting Protocol

How to compose the final report in Step 7 (DELIVERY). Hand off to `data-storytelling` for the narrative arc; this file specifies the structural contract.

---

## Standard report shape

Every analysis report has 8 blocks in this order:

```
1.  QUESTION         (1 line, plain language)
2.  ANSWER           (1-3 lines, the headline finding)
3.  EVIDENCE         (numbers with effect sizes + CIs, 3-7 bullets)
4.  INTERPRETATION   (Track A — business-grounded)
5.  ANALOGY          (Track B — cross-domain, with 4-test self-audit OR explicit skip)
6.  LIMITS           (what this does NOT conclude)
6.5 ANALYST LOG      (every method tried, kept or discarded, with reason)
7.  NEXT             (next experiment or next data to collect)
```

Length target: 400-800 words for a tight report; up to 1500 for complex multi-method analyses. Anything longer probably has padding.

---

## Block 1: QUESTION

One sentence, no jargon. Pulled from the Step 1 INTAKE brief, restated in business language.

> "What variables in our 6 months of post-level Twitter analytics best explain new follows per tweet?"

NOT:
> "We performed a multivariate analysis of follower acquisition predictors using a panel dataset from..."

---

## Block 2: ANSWER

The headline. 1-3 lines. State the direction, magnitude, and confidence in plain language.

> "Bookmarks per impression and reply count are the two strongest stable predictors of new follows per tweet, together explaining ~22% of the variation. Likes alone are a weak predictor."

A reader who only reads the answer should still get the bottom line.

---

## Block 3: EVIDENCE

3-7 bullets with the numbers. Always include effect size + CI; never bare point estimates. Always include n.

```
- Bookmarks/impression vs new follows: Spearman ρ=0.42 (95% CI 0.34–0.49), n=487, p<0.001
- Reply count vs new follows: ρ=0.35 (95% CI 0.27–0.43), n=487, p<0.001
- Likes vs new follows: ρ=0.18 (95% CI 0.09–0.27), n=487, p<0.001
- Multivariate model R²=0.22 on 5-fold CV (95% CI 0.17–0.27)
- Top component from PCA on engagement metrics: "depth-of-engagement" (loadings: bookmarks 0.66, replies 0.58, detail-expands 0.42), explains 47% variance
```

If a number lacks a CI, the reader cannot judge how much to trust it.

---

## Block 4: INTERPRETATION (Track A)

Run the protocol from `interpret-business-track.md`. End block with the compact template:

```
Question: <restated user question, 1 line>
Answer: <plain-language finding with business units, 1-2 sentences>
What changes: <decision implication, 1 sentence>
What this does NOT say: <2-3 named limits — but save the heavy limits for Block 6>
```

---

## Block 5: ANALOGY (Track B)

Run the protocol from `interpret-analogy-track.md`. Show the work.

Format:
```
Cross-domain analogy: <name of the structural pattern, e.g. "preferential attachment in network growth">

Structural mapping:
- <business object> ↔ <analogy object>
- <business object> ↔ <analogy object>
- <business relation> ↔ <analogy relation>

New hypothesis it generates: <one testable prediction>

Boundary: <where the analogy breaks down for this case>
```

If no analogy passes all 4 acceptance tests:
```
Cross-domain analogy: SKIPPED. <one sentence reason — typically "the pattern is too local to the business mechanism to generalize" or similar>
```

Skipping with a reason is professional. Forced bad analogies are the opposite.

---

## Block 6: LIMITS

The honest section. 3-5 bullets covering:

- **Causal scope** — observational vs experimental; what can and can't be claimed about causation
- **Sample scope** — period covered; whether results generalize to outside that period
- **Variable scope** — what was NOT measured and may matter
- **Method scope** — known limitations of the chosen methods (e.g., correlation only catches monotonic, R² is in-sample, etc.)
- **Population scope** — who this applies to (e.g., "tweets with ≥100 imp"; smaller-reach posts excluded)

A reader who ships a decision based on the analysis should be able to anticipate stakeholder pushback by reading Block 6.

---

## Block 6.5: ANALYST LOG (required for any analysis with multiple methods)

To prevent post-hoc p-hacking and undisclosed cherry-picking, list every method, test, model, or feature set tried — including the ones discarded. One bullet per attempt:

```
- [method tried] → [result] → [kept / discarded, why]
```

Examples:
- Pearson + Spearman on all 14 features → top 3 strong; FDR-adjusted q<0.05 for 3 → kept all 3
- Linear regression with all 14 → R²=0.18, residuals heteroscedastic → discarded; switched to RandomForest
- LASSO with α from CV → 5 features survive; same 3 in top — kept as cross-method evidence
- PCA → first 2 PCs explain 38% only — discarded as a top-level finding; kept the loadings for context

If you ran exactly one method end-to-end (no model selection, no feature search, no test fishing), state that: `Analyst log: single pre-registered method, no alternatives tried.`

A reader who suspects p-hacking should be able to read this block and either confirm or reject the suspicion.

---

## Block 7: NEXT

End every report with a forward step. One of:

- **Next experiment** — what test would falsify or strengthen this conclusion
- **Next data** — what data, if collected, would reduce a key uncertainty
- **Next decision** — given this, what specific decision is now ready to make

> "Next: run a 2-week experiment posting half the tweets in the morning UTC window and half in the evening, measure follow lift. The current analysis is observational; an experiment would establish whether time-of-day causes the lift or merely covaries with it."

---

## Hand-off to data-storytelling

For executive-facing or external-facing deliverables, after the structured report is complete, invoke `data-storytelling` with the report contents. It handles narrative arc (Hook → Context → Rising → Climax → Resolution → CTA) and visualization.

For internal / technical readers, the structured 7-block report is usually sufficient on its own.

---

## Output format options

| Audience | Format |
|---|---|
| Internal slack / chat | Markdown, all 7 blocks tight |
| Internal Notion page | Markdown + embedded charts via attached URLs |
| Executive deck | Hand off to `data-storytelling` → ppt/pdf |
| Engineering ticket | Markdown + raw data file paths + script invocations to reproduce |
| External (blog / Twitter) | Hand off to copywriting skill; use the analogy in Block 5 as the hook |

---

## Reproducibility footer (required)

End the report with:

```
---
Reproduced by:
- profile: <command + output file path>
- analysis: <commands + output file paths>
- analyst: senior-data-analyst v0.1
- date: <YYYY-MM-DD>
```

A reader 6 months later should be able to re-run the analysis from the footer.
