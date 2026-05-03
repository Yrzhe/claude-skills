# Factor & Dimensionality Methods

For the Exploratory-Factor path. When the question is "what's driving Y?" or "what dimensions exist underneath these variables?"

The composite path runs in order. Stop early if a step gives a clean answer.

---

## Step 4a: Correlation matrix (always start here)

`scripts/correlation_matrix.py <path> --target COL`

Returns:
- Pearson r + Spearman ρ for every (X_i, target) pair
- FDR-adjusted p-values (Benjamini-Hochberg)
- Pairwise X_i × X_j matrix to spot multicollinearity
- Heatmap PNG

**Read first**: which X_i has the strongest stable relationship with target? Are top correlates also correlated with each other (multicollinearity warning)?

**Stop here if**: 1-3 clean strong correlates emerge AND they aren't multicollinear. The user may not need PCA.

---

## Step 4b: Ensemble feature importance

`scripts/feature_importance.py <path> --target COL`

Combines three independent methods (a single method is brittle):

| Method | What it measures | Strength |
|---|---|---|
| **LASSO regression coefficients** | Which features survive L1 penalty | Picks parsimonious feature set; handles multicollinearity by dropping correlates |
| **Random Forest permutation importance** | Performance drop when feature is shuffled | Captures non-linear + interaction effects |
| **Mutual information** | Statistical dependence (non-parametric) | No model assumption; catches non-monotonic |

Bootstrap each method (n=200) for stability. **Report only features that appear in top-k of ≥2 methods**. Single-method top features are unreliable.

Output: ranked list with stability score (0-1) per feature.

---

## Step 4c: PCA / EFA / CFA — only when warranted

These three are different. Pick the right one.

### PCA (Principal Component Analysis)

**When**: ≥10 candidate inputs, you want orthogonal axes that maximize variance, the goal is data compression / visualization.

**Not for**: testing a theory of latent factors. PCA gives you whatever components maximize variance; it does not estimate latent constructs.

`scripts/pca_quick.py <path>`

Output: variance explained per component, scree plot, loadings, suggested cut at 80% cumulative variance OR scree elbow (whichever is more interpretable).

**Quality bar**:
- Standardized inputs (z-score)
- Components explain ≥70% cumulative variance to be useful
- Each retained component must be interpretable in <5 words ("engagement composite", "depth-of-read composite") — if not, may be noise
- n_samples ≥ 5×n_variables

### EFA (Exploratory Factor Analysis)

**When**: you suspect latent factors exist, want to estimate them, and accept that observed variables = factor loadings + unique variance + error.

**Differs from PCA**: estimates communalities (shared variance) rather than total variance; uses iterative methods; supports rotation (varimax / promax) for interpretability.

**Tools**: `factor_analyzer` Python package. The `senior-data-analyst` skill v0.1 does not include a packaged script — write inline if needed:

```python
from factor_analyzer import FactorAnalyzer
fa = FactorAnalyzer(n_factors=k, rotation='varimax')
fa.fit(X_standardized)
# fa.loadings_, fa.get_communalities(), fa.get_factor_variance()
```

Choose `k` via Kaiser criterion (eigenvalue > 1), parallel analysis, or scree elbow. Run all three; pick the consensus.

**Quality bar**:
- KMO statistic > 0.6 (sampling adequacy)
- Bartlett's test of sphericity significant
- Each factor has ≥3 strong loadings (>0.4) for stable interpretation
- Rotated solution is more interpretable than unrotated (it should be)

### CFA (Confirmatory Factor Analysis)

**When**: you have a *prior* theory about which variables load on which factors and want to test it.

Strictly hypothesis-driven. Out of scope for v0.1 of this skill — flag and recommend the user use a dedicated SEM tool (lavaan in R, semopy in Python).

---

## Step 4d: Synthesize top-k drivers

Combine evidence from 4a, 4b, 4c:

1. List candidates that show up as a top correlate in 4a AND a top feature in 4b
2. If PCA in 4c reveals these candidates load on the same component, treat them as a single composite driver
3. Final output: 3-7 drivers ranked by composite evidence (correlation strength + multi-method importance + factor loading)

**Discount aggressively**:
- If a "driver" appears in only one method, downgrade
- If a "driver" appears strongly but the variable is itself derived from the target (leakage), drop
- If a "driver" appears strongly but n_samples is small (<100), widen the CI considerably

---

## Common amateur failures (handled in pro-checklist.md)

- Confusing factor importance with causal effect — these are associations
- Reporting top correlation without checking it's stable across resamples
- Running PCA on too few variables (<10) or unstandardized data
- Skipping the multi-method triangulation; relying on a single ranking
- Interpreting PCA components as latent factors (they aren't — that's EFA)
