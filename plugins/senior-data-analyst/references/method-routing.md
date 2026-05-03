# Method Routing

How to convert a fuzzy business question + a DataProfile into one or more concrete analysis paths.

This is the most failure-prone step in any analysis. Two amateur traps:

1. **Default to regression** — every analyst's reflex; often the wrong choice
2. **Pick one method when the question needs two** — exploratory questions almost always need a descriptive pass before any inferential / predictive work

Treat this routing as a structured judgment, not a lookup table. Use the table below as a starting point, then justify the final pick in writing during Step 4 PLAN-CONFIRM.

---

## Negative-first exclusion filter (run BEFORE picking a path)

Exclusion gates beat positive matching. Walk these checks first; they prevent the most common drift (default-to-regression, predictive-without-target, inferential-on-too-small-n):

| If... | Then this path is **excluded**, regardless of how the question sounds |
|---|---|
| The question is "what does X look like" with no comparison and no target | NOT Inferential, NOT Predictive — must be Descriptive (or Exploratory if many vars) |
| No target variable can be named after Step 1 INTAKE | NOT Inferential, NOT Predictive — must be Descriptive or Exploratory-Factor |
| n_rows < 50 | NOT Predictive (insufficient for held-out validation); flag in PLAN-CONFIRM |
| n_rows < 5 × n_features (in candidate inputs) | NOT Predictive without aggressive feature reduction; flag explicitly |
| User said "cause" / "导致" / "因为" but data is observational | Path can be Inferential, but PLAN-CONFIRM **must** include a written causation caveat; never claim causation in the report |
| User wants "what factors / drivers" + has ≥10 candidate inputs | Default to Exploratory-Factor, NOT a single regression |
| The whole dataset is one group (no comparison group, no time slice) | NOT Inferential — there's nothing to test against |

If any exclusion fires, name it explicitly in the PLAN-CONFIRM block so the human can see the constraint.

---

## The 4 paths

### Path 1: Descriptive

**When**: question is about *what is* — distribution, central tendency, trend over time, breakdown by segment, anomalies. No causal claim, no prediction.

Trigger phrases:
- "What does X look like?"
- "What's the trend?"
- "How is X distributed?"
- "What changed?"
- "Show me the breakdown by Y"

**Hands off to**: `data-analysis` skill (pandas EDA + basic plots). Use `xlsx` if output needs to be a spreadsheet.

**Output shape**: summary stats + 1-3 charts + flagged anomalies.

**Common amateur failure**: stopping here when the question actually needed inferential or factor analysis underneath.

---

### Path 2: Inferential

**When**: question involves a *comparison* or a *claim about a population*. Hypothesis test territory.

Trigger phrases:
- "Is X different from Y?"
- "Did the change make a difference?"
- "Is there a relationship between X and Y?"
- "Does X cause / predict Y?" (causation needs more than inference, but the test is the start)
- "AB test / experiment results"

**Sub-route by data shape** (read `statistical-analysis/SKILL.md` — it has the canonical test-selection guide):

| Compare | Data type | Default test |
|---|---|---|
| 2 means | numeric, independent | independent t-test (Welch's by default) |
| 2 means | numeric, paired | paired t-test |
| 3+ means | numeric | one-way ANOVA + post-hoc (Tukey/Dunn) |
| 2+ proportions | categorical | chi-square or Fisher exact |
| Relationship | 2 numeric | Pearson (parametric) / Spearman (non-parametric) |
| Predict | numeric outcome | linear / multiple regression |
| Predict | binary outcome | logistic regression |
| Multi-way comparison | factorial | factorial ANOVA / mixed model |

**Hands off to**: `statistical-analysis` skill. It handles assumption checks (normality, homoscedasticity), effect size (Cohen's d, η², odds ratio), confidence intervals, and APA reporting.

**Common amateur failures** (handled in `pro-checklist.md`):
- p-hacking by trying many tests until something is significant
- ignoring multiple-comparison correction
- reporting p < 0.05 without effect size
- using parametric test when assumptions violated

---

### Path 3: Predictive

**When**: question is about *building a model that generalizes to new data*. Held-out test set is mandatory.

Trigger phrases:
- "Predict X given Y, Z"
- "Classify into A/B/C"
- "Forecast next month / quarter"
- "Score the probability of churn / conversion"
- "Recommend / rank"

**Read** `references/ml-methods.md` for the method picker (classification / regression / clustering / time-series + cross-validation protocol).

**Output shape**: trained model + held-out performance metrics + feature importance + calibration check.

**Common amateur failures**:
- Data leakage (target info in features, future info in past features)
- Train/test split contamination
- Optimizing on test set (use proper train/val/test or CV)
- Reporting accuracy on imbalanced data instead of F1 / AUC / PR-AUC

---

### Path 4: Exploratory-Factor

**When**: question is about *what's driving Y* or *what dimensions exist underneath* — but you don't have a clean predictive setup, or the goal is understanding rather than prediction.

Trigger phrases:
- "What factors drive X?"
- "What are the underlying dimensions?"
- "Which variables matter most?"
- "Reduce these 30 columns to a few axes"
- "涨粉因子 / 转化因子 / 影响 X 的变量"

**This is a composite path**. Run the steps in order, stopping early if a step gives a clean answer:

```
Step 4a:  Correlation matrix (Pearson + Spearman) with FDR-adjusted p-values
          → scripts/correlation_matrix.py <path> --target COL
          → If 1-3 clear strong correlates emerge, you may be done.

Step 4b:  Ensemble feature importance (LASSO + RandomForest + Mutual Info)
          → scripts/feature_importance.py <path> --target COL
          → Bootstrap (n=200) for stability. Report top-k with stability scores.

Step 4c:  PCA / EFA (if ≥10 candidate inputs and they're correlated)
          → scripts/pca_quick.py <path>
          → Read references/factor-methods.md for choice between PCA / EFA / CFA
          → 80% variance + scree elbow + interpretable loadings = useful

Step 4d:  Top-k driver ranking with confidence
          → Combine evidence from 4a/4b/4c. Discount any "driver" that
            shows up in only one method.
```

Read `references/factor-methods.md` for the full protocol.

**Common amateur failures**:
- Reporting top-1 correlation without checking it's stable across samples
- Confusing factor importance with causal effect
- Running PCA on a tiny correlated set (use it when ≥10 inputs)
- Skipping the multi-method triangulation (any single method is brittle)

---

## How to combine paths

Real questions often need multiple paths in sequence. Examples:

| Business question | Path sequence |
|---|---|
| "Did the new feature increase retention?" | Descriptive (look at retention trend) → Inferential (test pre/post or treat/control) |
| "What drives 涨粉?" | Descriptive (variable distributions, corr matrix) → Exploratory-Factor (Step 4a/4b/4c) → optional Predictive (build a model to validate) |
| "Should we ship this?" | Inferential (test the difference) → Decision-aid (Bayesian update + EV) — this last hop hands off to `decision-aid` skill |
| "Segment users into actionable groups" | Descriptive → Predictive (clustering) → Inferential (test segment differences are significant) |

When in doubt, list the user's question on the left and write the sequence on the right in plain prose during Step 4 PLAN-CONFIRM. Make the user agree to the sequence before executing.

---

## A note on causation

Inference and prediction are not causation. If the user's underlying question is causal ("does X cause Y") and the data is observational, the analysis can at best describe association, not causation. Say this explicitly in the limits section. Causal analysis (DiD, IV, RDD, propensity scoring, DAG-based identification) is out of scope for this skill v0.1 — flag it as a future extension.
