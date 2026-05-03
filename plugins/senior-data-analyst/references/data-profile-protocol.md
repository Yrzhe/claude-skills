# Data Profile Protocol

The DataProfile is what the agent uses to reason about a dataset without loading it into context. Step 2 (PROFILE) and Step 3 (METHOD-PICK) both depend on it.

## Hard rule

Never read a full data file into the agent's context window. For files larger than ~1000 rows, the profile script's output is the only data the agent should see during routing.

If the user pastes a small (<200 rows) CSV directly into chat, you may inspect it. Anything from a file path goes through `scripts/profile_data.py`.

## Required output fields

`scripts/profile_data.py <path>` must return JSON with:

```json
{
  "path": "<absolute path>",
  "format": "csv|xlsx|parquet|jsonl",
  "n_rows": 506,
  "n_cols": 17,
  "columns": [
    {
      "name": "Impressions",
      "dtype": "int64",
      "null_pct": 0.0,
      "n_unique": 412,
      "min": 1, "max": 24593,
      "mean": 1842.3, "std": 3120.4,
      "p25": 142, "p50": 612, "p75": 1820,
      "head": [70, 14, 25, 1834, 412]
    },
    {
      "name": "Post text",
      "dtype": "object",
      "null_pct": 0.0,
      "n_unique": 506,
      "len_mean": 187.4, "len_max": 1024,
      "head": ["@aarondfrancis ran 4...", "@petergyang Built...", ...]
    }
  ],
  "head_5": [...],
  "tail_5": [...],
  "primary_key_candidates": ["Post id"],
  "duplicates": {"by_pk": 0, "exact_row": 2},
  "warnings": [
    "Column 'Date' parsed as object — consider datetime conversion",
    "5 columns have >80% zeros — possible sparse encoding"
  ]
}
```

Numeric columns include distribution stats; object/text columns include length stats. The script must keep total output under 8K tokens — if too many columns, truncate to top 30 + a `truncated_cols` field.

## How the agent uses the profile

When routing in Step 3:

| Profile signal | Implication |
|---|---|
| `n_rows < 30` | Inferential tests have very low power. Flag in plan. Bayesian / non-parametric preferred. |
| `n_rows < 100` AND target is numeric | Linear regression OK; ML almost never. Flag. |
| `null_pct > 50%` on a candidate input | Drop or impute with explicit method. Don't silent-drop. |
| `n_unique == n_rows` for object | This is an ID column, not a feature. Exclude from analysis. |
| `n_unique == 1` | Constant column. Exclude. |
| `n_unique == 2` AND dtype is bool/object | Binary feature, fine for chi-square / logistic. |
| Numeric col `std/mean > 5` | High dispersion — consider log-transform or robust stats. |
| `p25 == p50 == p75` | Heavily skewed; non-parametric tests required. |
| `duplicates.by_pk > 0` | Dedupe before analysis. Note overlap if combining files. |
| Date column as object | Parse to datetime before any time-series analysis. |

## Multi-file deduplication

If the user provides multiple files that overlap (common with re-exported analytics CSVs):

1. Run profile on each file
2. Check `primary_key_candidates` — most likely the analytics platform's row id
3. Concat all files, drop duplicates by PK, then re-profile the merged set
4. Report: input file count, raw row total, deduped row total, overlap %

Do not skip this. Combining 5 overlapping CSVs without dedup biases every count, mean, and correlation.

## When the profile is suspicious

These warrant a halt and clarification with the user:

- Profile says 0 rows or 1 column → file path or format is wrong
- Profile shows `n_unique == 1` for the user's named target → can't analyze a constant
- Profile shows >90% null on the user's named target → ask what to do (impute? drop? use a different target?)
- Profile shows a date range that doesn't match the user's stated time window → confirm before proceeding
