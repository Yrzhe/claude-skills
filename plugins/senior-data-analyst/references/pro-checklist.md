# Anti-Amateur Checklist

What separates senior from junior. Apply the relevant block to whatever method you ran. Treat any failed check as something to fix or disclose, never to silently suppress.

---

## Enforcement rule (apply on every Step 5 method execution)

After running any method in Step 5, paste the relevant checklist block into the output and mark each item ✅ or ❌. **Do not mark ✅ silently — paste the evidence (one short clause).** If any item is ❌, it MUST appear in the LIMITS section of the final report. Do not proceed to Step 6 INTERPRET while any checklist item is unchecked.

This converts the checklist from "soft guidance" into a visible audit trail the human can verify.

---

## Universal (every analysis)

- [ ] **Reported effect size + confidence interval, not just p-value or accuracy** — a tiny p-value with negligible effect is not a finding
- [ ] **Sample size is adequate for the claim** — for inferential, run a power analysis (`statistical-analysis` has it); for predictive, n_samples / n_features ≥ 10 minimum
- [ ] **Limits section names what this analysis cannot conclude** — e.g., "this is observational, no causal claim"
- [ ] **Used the test/method's diagnostic before trusting the result** — Q-Q plot, residual plot, calibration curve, learning curve

## Inferential / hypothesis testing

- [ ] **Pre-registered the hypothesis OR reported every test you ran** — fishing without disclosure is p-hacking
- [ ] **Multiple-comparison correction applied when running many tests** — FDR (Benjamini-Hochberg) by default; Bonferroni when small k and you need conservatism
- [ ] **Assumption checks done** — normality (Shapiro-Wilk / Q-Q), equal variance (Levene), independence (study design); switch to non-parametric (Wilcoxon / Mann-Whitney / Kruskal-Wallis) when violated
- [ ] **Used Welch's t-test by default** for unequal variances (don't default to Student's)
- [ ] **Reported direction + magnitude, not just "p < 0.05"** — "Group A scored 12 points (95% CI 7–17) higher than Group B, t(98)=4.2, p<0.001, d=0.7"
- [ ] **Did not interpret a non-significant result as proof of no effect** — absence of evidence is not evidence of absence; report power and CI width

## Correlation

- [ ] **Used Spearman alongside Pearson** when distributions are skewed or relationship may be monotonic-but-nonlinear
- [ ] **FDR-adjusted p-values** when testing many pairs (correlation matrix)
- [ ] **Did not interpret r as effect size without CI** — r=0.3 with n=20 has CI roughly [-0.2, 0.65]
- [ ] **Did not claim causation from correlation** — write the limits sentence explicitly

## Regression

- [ ] **Checked residuals** for heteroscedasticity (residual-vs-fitted plot), normality (Q-Q on residuals), influential points (Cook's distance)
- [ ] **Checked multicollinearity** when ≥3 predictors — VIF > 5 means trouble
- [ ] **Reported R², adjusted R², and out-of-sample if predictive** — in-sample R² is overstated
- [ ] **Did not extrapolate beyond observed range of X** — model is only valid in the training distribution

## ML / Predictive

- [ ] **Train/test split done before any feature engineering touched test data** — leakage check
- [ ] **No future information in features** when predicting time-ordered outcomes (use time-aware split, not random)
- [ ] **No target leakage** — features that could only be known after the outcome (e.g., "did_renew" feature when predicting churn)
- [ ] **Cross-validation properly stratified** for imbalanced classes
- [ ] **Reported the right metric for the problem**:
  - Imbalanced binary: PR-AUC, F1, balanced accuracy, NOT plain accuracy
  - Calibration matters: Brier score, calibration plot
  - Ranking: NDCG, MAP
  - Regression: RMSE + MAE (different sensitivity to outliers)
- [ ] **Compared to a stupid baseline** — random / majority-class / yesterday's value. Did the model beat it meaningfully?
- [ ] **Used cross-validation, not just one split** — single split is high-variance for n < ~10K
- [ ] **Hyperparameter tuned on val set, not test set**

## Factor analysis / PCA / EFA

- [ ] **n_samples ≥ 5x n_variables minimum** for PCA stability; ≥ 10x preferred for EFA
- [ ] **Variables standardized** before PCA (StandardScaler) — otherwise high-variance columns dominate
- [ ] **Reported variance explained per component + scree plot** — don't just say "we used 3 components"
- [ ] **Bootstrap or split-half stability check** — recompute on resamples; loadings should be stable
- [ ] **Loadings are interpretable** — if you can't name a component in <5 words, it may be noise
- [ ] **Did not confuse PCA with EFA** — PCA gives axes that maximize variance; EFA infers latent factors with assumed measurement model. Different goals.

## Time-series

- [ ] **Stationarity check** (ADF / KPSS) before fitting ARIMA-family
- [ ] **Time-aware train/test split** — never random shuffle
- [ ] **Walk-forward validation, not k-fold**
- [ ] **Compared to naive baseline** — last value / last week's value / seasonal naive
- [ ] **Reported uncertainty intervals**, not just point forecasts

## Clustering

- [ ] **Tried multiple k values** + reported a selection criterion (silhouette, elbow, BIC)
- [ ] **Standardized features** before distance-based methods (KMeans, hierarchical)
- [ ] **Validated cluster stability** via bootstrap or split-half
- [ ] **Each cluster is interpretable + actionable** — if you can't describe it in business terms, the partition isn't useful
- [ ] **Did not interpret cluster IDs as ordinal** — KMeans cluster 1 vs cluster 2 has no natural ordering

## Reporting

- [ ] **Numbers have units and context** — "0.42 r" without N is meaningless
- [ ] **Charts have labeled axes, legend, source, n** — no naked plots
- [ ] **The headline can be wrong** — write the answer assuming a critical reader; can you defend it?
- [ ] **The "next experiment" question is named** — what would falsify or strengthen this conclusion?
