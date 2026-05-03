# ML / Predictive Methods

For the Predictive path. When the goal is a model that generalizes to new data — held-out test set is mandatory.

This reference is intentionally compact. ML is a deep subject; this skill v0.1 covers the most common cases an AI PM analyst will hit. For deeper needs, hand off to a dedicated ML skill or a human.

---

## Method picker by problem type

| Problem | Default first try | When to upgrade |
|---|---|---|
| Binary classification | Logistic regression | Tree boosting (XGBoost/LightGBM) when n>1K + features interact |
| Multi-class classification | Logistic regression OvR or RandomForest | Boosting + class weights when imbalanced |
| Regression (continuous outcome) | Linear regression with regularization (Ridge/Lasso) | RandomForest / XGBoost when non-linear patterns |
| Clustering | KMeans (after standardization) | HDBSCAN when clusters have varying density / DBSCAN for arbitrary shapes |
| Dimensionality reduction (visualization) | PCA → t-SNE / UMAP for non-linear viz | UMAP scales better than t-SNE |
| Time-series forecasting | Naive baseline + ARIMA | Prophet for strong seasonality; LSTM/transformer only when justified |
| Anomaly detection | Isolation Forest | Autoencoder when high-dimensional |
| Recommendation / ranking | Matrix factorization (ALS) | Neural collab filtering at scale |

---

## The one rule that beats everything else

**Compare to a stupid baseline.** Always.

- Classification: predict majority class
- Regression: predict mean (or last value for time-series)
- Time-series: yesterday's value, last week's same hour, seasonal naive

If your fancy model doesn't beat the stupid baseline on the held-out set, the model isn't doing anything useful — even if accuracy looks high.

---

## Cross-validation protocol

| Data shape | Use |
|---|---|
| iid, n > 1000 | k-fold (k=5 or 10), stratified for classification |
| iid, n < 500 | Repeated k-fold or LOOCV (compute permitting) |
| Time-ordered | Walk-forward / time-series split — NEVER random k-fold |
| Grouped (multiple rows per user/customer) | Group k-fold (split by group, not row) |
| Heavily imbalanced (binary) | Stratified k-fold + report PR-AUC/F1, not accuracy |

A single train/test split is too noisy for n < ~10K. Default to CV unless the dataset is huge.

---

## Hyperparameter tuning

Use proper train/val/test split or nested CV:

```
train (60%)  →  val (20%)  →  test (20%)
       train hyperparams on val
       evaluate ONCE on test
```

If you tune on test, you have leakage. The reported test metric becomes a lower bound on generalization error, biased optimistic.

For boosted trees: tune learning rate × depth × n_estimators × regularization. Use Optuna or HyperOpt. 50-200 trials is usually enough.

---

## Metric picker

**Don't default to accuracy.** It's misleading on imbalanced data and ignores ranking quality.

| Goal | Metric |
|---|---|
| Balanced binary classification | Accuracy, ROC-AUC |
| Imbalanced binary | PR-AUC, F1, balanced accuracy, Matthews correlation |
| Probability calibration matters | Brier score + reliability diagram |
| Top-k ranking | NDCG@k, MAP@k, Recall@k |
| Regression (symmetric errors) | RMSE |
| Regression (median-focused) | MAE |
| Regression (relative errors) | MAPE (caveat: undefined at 0) |
| Clustering | Silhouette + interpretability check (no perfect metric) |

---

## Feature engineering checklist

Before modeling, for each feature:

- [ ] Is the dtype right? (categorical encoded properly, dates parsed, numerics not stored as strings)
- [ ] Are there missing values? Impute with explicit method (median for numeric, mode for categorical, "missing" indicator) or drop with justification
- [ ] Are there outliers? Decide: keep, winsorize, log-transform, or drop based on domain
- [ ] Is the feature on a similar scale to others? (StandardScaler for distance-based / regularized models; trees don't care)
- [ ] Could this feature contain target leakage? (info that wasn't available at prediction time)
- [ ] Is this feature highly correlated with another? (drop or combine)

---

## Common amateur failures (handled in pro-checklist.md)

- **Data leakage** — most common ML failure; check by asking "would this feature be known at prediction time?"
- **Train/test contamination** — feature engineering on full dataset before splitting; standardization fitted on train+test
- **Optimizing on test set** — repeatedly running, peeking, retraining
- **Ignoring class imbalance** — default RandomForest on 95/5 imbalance gets 95% accuracy by predicting majority
- **No baseline comparison** — claiming "85% accuracy" without saying majority class is 80%
- **Reporting train metrics** — only test metrics are real

---

## Calibration check

For probabilistic classifiers: predicted probabilities should match observed frequencies.

Plot: bin predictions into 10 buckets by predicted probability, compute observed positive rate in each bucket, plot observed vs predicted. A well-calibrated model lies on the diagonal.

If miscalibrated, fix with Platt scaling or isotonic regression on a calibration set (separate from train and test).

---

## When to NOT build a model

- n_samples is too small (<100 for regression, <500 for classification with multiple classes)
- The signal is weak — best CV score barely beats baseline
- The decision doesn't depend on prediction quality (e.g., user just wants to understand the data — use Descriptive or Exploratory-Factor path instead)
- Causal inference is the actual question — predictive models do not give causal effects

In these cases, return to METHOD-PICK and choose Descriptive / Inferential / Exploratory-Factor.
