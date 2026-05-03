---
name: senior-data-analyst
description: |
  Senior data analyst skill. Turns any agent into a professional, full-stack data analyst capable of handling business questions end-to-end: intake → safe data profiling → method routing (descriptive / inferential / predictive / exploratory-factor) → analysis with anti-amateur guardrails (multiple-comparison, leakage, p-hacking, assumption checks) → dual-track interpretation (business-grounded + cross-domain analogy) → narrative reporting.

  Use when the user asks: "analyze this data / dataset / CSV", "find drivers / factors / what causes X", "is this difference significant", "run a regression / correlation / hypothesis test / PCA / factor analysis", "build a model / predict / classify / cluster / segment", "what does this data mean", "do a deep / proper / professional analysis", "what factors drive X", "explain this metric", "find the underlying dimensions".

  Triggers: data analysis, data analyst, data scientist, senior analyst, find drivers, find factors, hypothesis test, significance test, correlation, regression, PCA, factor analysis, EFA, CFA, classification, clustering, segmentation, time-series, predict, model, EDA, exploratory analysis, multivariate analysis, feature importance, drivers of growth, churn drivers, retention drivers.

  Skip when: user only wants a single chart / dashboard with no analytical question (use data-storytelling), only wants raw data extraction with no analysis (use data-analysis), is asking a closed factual question with no data attached, or is asking for academic-only stats reporting in APA format (use statistical-analysis directly).
---

# Senior Data Analyst

Turns any agent into a senior data analyst. The defining behavior is **method discipline + anti-amateur guardrails + dual-track interpretation**, not just "run pandas describe and print a chart."

This skill is a **navigator**. Every method, prompt template, and protocol lives in `references/`. Load only what the current step needs.

---

## What this skill is NOT

- Not a replacement for `statistical-analysis` (this skill orchestrates it)
- Not a replacement for `data-analysis` (this skill orchestrates it)
- Not a chart-making skill (use `data-storytelling`)
- Not a decision skill (use `decision-aid`)

---

## Reference dispatch

Load only the references you need for the current step. Do **not** read all of them up front.

| What you are doing | Read |
|---|---|
| Routing a vague business question to a method family | `references/method-routing.md` |
| Designing the safe data profile (schema/dtype/nulls/sample) | `references/data-profile-protocol.md` |
| Picking a factor / dimensionality method (PCA / EFA / CFA / corr matrix / feature importance) | `references/factor-methods.md` |
| Picking an ML method (classification / clustering / regression / time-series / model selection) | `references/ml-methods.md` |
| Anti-amateur guardrails (multiple-comparison, leakage, p-hacking, assumption violations) | `references/pro-checklist.md` |
| Translating numbers back into business language | `references/interpret-business-track.md` |
| Producing a non-trivial cross-domain analogy | `references/interpret-analogy-track.md` |
| Cross-disciplinary template library (preferential attachment, critical period, etc.) | `references/analogy-templates.md` |
| Composing the final report (intent, structure, hand-off to data-storytelling) | `references/reporting.md` |

## Scripts

Always reach for a script before writing one inline.

| Script | What it does |
|---|---|
| `scripts/profile_data.py <path>` | Safe profile (schema, dtype, null %, cardinality, head sample). Never loads full data into context. |
| `scripts/correlation_matrix.py <path> --target COL` | Pearson + Spearman matrix with FDR-adjusted p-values + heatmap |
| `scripts/feature_importance.py <path> --target COL` | Ensemble feature importance (LASSO + RandomForest + Mutual Info), bootstrapped |
| `scripts/pca_quick.py <path>` | PCA + scree plot + loadings + 80% variance cutoff |

---

## Other skills this orchestrates

When the routing step picks one of these, load it via the platform's skill mechanism (`Skill` tool / `load_skills`).

- `statistical-analysis` — t-test / ANOVA / chi-square / regression / Bayesian / power / APA reporting
- `data-analysis` — pandas EDA, multi-format ingestion (CSV / xlsx / pdf / docx / image), token-safe exploration
- `data-storytelling` — narrative arc, executive presentation
- `dbs-deconstruct` — concept deconstruction (Wittgenstein + Austrian) — used in business interpretation track
- `dbs-diagnosis` — business-model diagnosis — used in business interpretation track
- `xlsx` — spreadsheet operations
- `decision-aid` — when analysis is in service of a yes/no choice (Bayesian update, EV, pre-mortem)

---

## The 7-step pipeline

Every analysis job runs all 7 steps. Skipping a step is the most common failure mode.

```
1. INTAKE          fuzzy business question  →  structured task brief
2. PROFILE         data sources              →  DataProfile (safe, token-bounded)
3. METHOD-PICK     brief + DataProfile       →  one or more method paths
4. PLAN-CONFIRM    plan                      →  HUMAN GATE (do not skip)
5. EXECUTE         scripts + sub-skills      →  raw results + diagnostics
6. INTERPRET       results                   →  dual-track:
                                                 - business-grounded
                                                 - cross-domain analogy (4-test rubric)
7. DELIVERY        interpretation            →  narrative report (Markdown / PDF / Notion)
```

### Step 1: INTAKE

Convert the user's prompt into a written **task brief**:
- **Business question** — one sentence, no jargon
- **Decision the analysis will inform** — what changes if the answer is X vs Y?
- **Target variable** — the thing being explained / predicted (or "no target — exploratory")
- **Candidate inputs** — what columns / sources might matter
- **Time window** — over what period
- **Known constraints** — sample size, what's been tried, what's off-limits

**Tiered intake** (do not improvise; do not over-question):
- Missing 1-2 fields: ask one combined question.
- Missing 3+ fields: ask at most 2 questions, then let Step 2 (PROFILE) and Step 4 (PLAN-CONFIRM) act as the safety net — infer remaining fields from the DataProfile and require human confirmation in Step 4.

Never silently fill in a missing field. Either ask, or write "inferred from DataProfile — confirm in Step 4."

### Step 2: PROFILE

Run `scripts/profile_data.py <path>` on every data source. Read `references/data-profile-protocol.md` for the output contract.

**Never** read the full file into context. The profile script returns: row count, column names + dtypes, null %, cardinality, head(5), tail(5), basic distribution stats. That fits in token budget.

If multiple files overlap (common with re-exported analytics CSVs), **dedupe by primary key** before profiling the merged set. Note overlaps explicitly.

### Step 3: METHOD-PICK

Read `references/method-routing.md`. The routing table maps `(question type × data shape)` to one of 4 paths:

| Path | When | Hands off to |
|---|---|---|
| **Descriptive** | "What does the data look like? What's the trend?" | `data-analysis` (EDA, distribution, time-series plot) |
| **Inferential** | "Is X different from Y? Does X cause / predict Y?" | `statistical-analysis` (test selection, assumption checks, APA report) |
| **Predictive** | "Given X, predict Y" | `references/ml-methods.md` (classification / regression / time-series + cross-validation) |
| **Exploratory-Factor** | "What are the underlying drivers / dimensions of Y?" | composite path: corr matrix → feature importance → optional PCA → top-k driver ranking |

Many real questions span 2+ paths. Document which paths apply and in what order.

### Step 4: PLAN-CONFIRM (HUMAN GATE)

Before running anything beyond the profile, output **exactly this block** and stop. Do **not** include any analysis code, results, charts, or commentary in the same message.

```
---
## Analysis Plan — Please Confirm

**Question (restated)**: [one sentence in business language]
**Method(s)**: [paths chosen + one line per path on why this path fits the question]
**Output will look like**: [concrete description — table shape, chart type, headline format]
**Cannot answer**: [2-3 things this analysis will explicitly NOT tell us]

### Risk register (mark ⚠ for any that apply)
- [ ] Multiple tests planned → multiple-comparison correction needed (FDR / Bonferroni)
- [ ] Grouped / clustered rows (users, sessions, time blocks) → independence violated; need cluster-aware methods
- [ ] Time order matters → train/test split must respect time, no future leakage
- [ ] Leakage candidates → features that encode the target or its near-future
- [ ] Causal claim attempted on observational data → write causation caveat
- [ ] Missingness mechanism unknown → MCAR/MAR/MNAR check before naive imputation

👉 Reply "go" to proceed, or tell me what to change.
---
```

**Wait for explicit confirmation.** A user saying "go", "ok 跑吧", "sounds good", "confirmed", "可以" all count. Silence does not. **Do not run analysis until the human confirms the plan.**

**Sub-agent caveat**: if you are running as a sub-agent delegated by another orchestrating agent (via `Skill` / `load_skills` / `Task`), the gate still applies. Output the plan block and STOP. Do **not** treat the orchestrating agent's "go" as human confirmation unless that orchestrating agent explicitly says the human approved.

This gate exists because automated agents waste cycles running the wrong analysis. A 2-minute plan review saves a 45-minute mis-routed run.

### Step 5: EXECUTE

Run the planned methods using scripts and sub-skills. While executing, apply `references/pro-checklist.md` — every method has known amateur failure modes. The checklist is non-negotiable; treat any check failure as an issue to fix or disclose, not to suppress.

Common gates: multiple-comparison correction (FDR / Bonferroni when running many tests), data leakage prevention (no future info / no target leakage in features), p-hacking guards (pre-register the hypothesis or report all tested), assumption checks (normality / homoscedasticity / independence — use the test's own diagnostic).

### Step 6: INTERPRET — dual track, both required

Numbers without interpretation are useless. Run **both** tracks; do not skip either.

**Order matters**: run **Track B BEFORE finalizing Track A**. Track B's input is the raw numerical results from Step 5, NOT the business interpretation from Track A. Running B-after-A causes Track B to systematically degrade into a paraphrase of Track A's conclusion — the exact failure mode Test 4 is designed to prevent.

**Track A — Business-grounded** (`references/interpret-business-track.md`)
Translate numbers back into the business language and the original decision. Use `dbs-deconstruct` to re-state any concept that's been abstracted away. Use `dbs-diagnosis` if the analysis touches a business-model question.

**Track B — Cross-domain analogy** (`references/interpret-analogy-track.md`)
Produce **one** non-trivial cross-disciplinary analogy that meets all 4 acceptance tests:

1. **Structural mapping** — list "X corresponds to Y; A→B corresponds to C→D." Not surface similarity.
2. **Generates new hypotheses** — the analogy must let you make a new prediction or design a new experiment.
3. **States its boundary** — note where the analogy breaks down.
4. **Avoids restatement** — must NOT be a paraphrase of the business conclusion. ("Users got bored" is NOT "signal novelty decay" — only the second is acceptable.)

Reach for `references/analogy-templates.md` for inspiration but do not pick a template just because it's there. If no analogy meets all 4 tests, say so explicitly. Forced bad analogies are worse than none.

### Step 7: DELIVERY

Read `references/reporting.md`. Hand off to `data-storytelling` for the narrative arc. Default deliverable shape:

1. Question (1 line)
2. Answer (1-3 lines, the headline)
3. Evidence (numbers, with confidence intervals — never bare point estimates)
4. Business-grounded interpretation
5. Cross-domain analogy (with its 4-test self-audit)
6. Limits & caveats (what this can't conclude)
7. Next experiment / next data to collect

---

## Quality bar (what makes this senior, not junior)

A junior analyst stops after running `df.describe()` and a bar chart. This skill must clear all of:

- [ ] Plan was confirmed by a human before execution (Step 4 gate)
- [ ] Profile was safe — no full-file load into context
- [ ] Method choice was justified, not defaulted to "regression"
- [ ] Anti-amateur checklist applied for the chosen method
- [ ] Effect size + confidence interval reported, not just p-value
- [ ] Both interpretation tracks produced; analogy passed all 4 tests OR explicitly skipped with reason
- [ ] Limits section names what this analysis can't conclude

If the task is too small for all 7 steps (e.g., user just wants a quick correlation), still run the profile + plan-confirm + checklist. Skip nothing silently.
