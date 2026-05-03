#!/usr/bin/env python3
"""
Safe data profiling for senior-data-analyst skill.

Usage:
    python3 profile_data.py <path> [--max-cols 30]

Returns JSON to stdout. NOTE: pandas may load the full file into the script's
own memory to compute stats — but the script never dumps full file contents
back into the agent's context. The agent reads only the bounded JSON profile
(schema, dtypes, null %, cardinality, head/tail samples).
"""

import argparse
import json
import os
import sys
from pathlib import Path


def detect_format(path: str) -> str:
    ext = Path(path).suffix.lower().lstrip(".")
    return {"csv": "csv", "tsv": "tsv", "xlsx": "xlsx", "xls": "xlsx",
            "parquet": "parquet", "jsonl": "jsonl", "json": "jsonl"}.get(ext, "unknown")


def load_dataframe(path: str, fmt: str):
    import pandas as pd
    if fmt == "csv":
        return pd.read_csv(path)
    if fmt == "tsv":
        return pd.read_csv(path, sep="\t")
    if fmt == "xlsx":
        return pd.read_excel(path)
    if fmt == "parquet":
        return pd.read_parquet(path)
    if fmt == "jsonl":
        return pd.read_json(path, lines=True)
    raise ValueError(f"Unsupported format: {fmt}")


def profile_numeric(s, head_n=5):
    s_clean = s.dropna()
    if len(s_clean) == 0:
        return {"all_null": True}
    return {
        "min": float(s_clean.min()),
        "max": float(s_clean.max()),
        "mean": round(float(s_clean.mean()), 4),
        "std": round(float(s_clean.std()), 4) if len(s_clean) > 1 else 0.0,
        "p25": float(s_clean.quantile(0.25)),
        "p50": float(s_clean.quantile(0.50)),
        "p75": float(s_clean.quantile(0.75)),
        "head": [float(x) for x in s_clean.head(head_n).tolist()],
    }


def profile_object(s, head_n=5):
    s_clean = s.dropna().astype(str)
    if len(s_clean) == 0:
        return {"all_null": True}
    lengths = s_clean.str.len()
    return {
        "len_mean": round(float(lengths.mean()), 2),
        "len_max": int(lengths.max()),
        "head": [str(x)[:200] for x in s_clean.head(head_n).tolist()],
    }


def profile_datetime(s, head_n=5):
    s_clean = s.dropna()
    if len(s_clean) == 0:
        return {"all_null": True}
    return {
        "min": str(s_clean.min()),
        "max": str(s_clean.max()),
        "head": [str(x) for x in s_clean.head(head_n).tolist()],
    }


def detect_pk_candidates(df) -> list:
    n = len(df)
    candidates = []
    for col in df.columns:
        try:
            n_unique = df[col].nunique(dropna=True)
            if n_unique == n and df[col].notna().all():
                candidates.append(col)
        except Exception:
            pass
    return candidates


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", help="Path to data file (csv/tsv/xlsx/parquet/jsonl)")
    p.add_argument("--max-cols", type=int, default=30,
                   help="Truncate column profiles past this count to keep output bounded")
    p.add_argument("--head-n", type=int, default=5)
    args = p.parse_args()

    if not os.path.exists(args.path):
        print(json.dumps({"error": f"file not found: {args.path}"}))
        sys.exit(1)

    fmt = detect_format(args.path)
    if fmt == "unknown":
        print(json.dumps({"error": f"unsupported format for: {args.path}"}))
        sys.exit(1)

    try:
        import pandas as pd
    except ImportError:
        print(json.dumps({"error": "pandas not installed; pip install pandas openpyxl pyarrow"}))
        sys.exit(1)

    df = load_dataframe(args.path, fmt)
    n_rows, n_cols = df.shape
    warnings = []
    columns = []

    cols_to_profile = list(df.columns)
    truncated = False
    if len(cols_to_profile) > args.max_cols:
        cols_to_profile = cols_to_profile[: args.max_cols]
        truncated = True

    for col in cols_to_profile:
        s = df[col]
        col_info = {
            "name": col,
            "dtype": str(s.dtype),
            "null_pct": round(float(s.isna().mean()) * 100, 2),
            "n_unique": int(s.nunique(dropna=True)),
        }
        try:
            if pd.api.types.is_numeric_dtype(s):
                col_info.update(profile_numeric(s, args.head_n))
            elif pd.api.types.is_datetime64_any_dtype(s):
                col_info.update(profile_datetime(s, args.head_n))
            else:
                col_info.update(profile_object(s, args.head_n))
        except Exception as e:
            col_info["profile_error"] = str(e)
        columns.append(col_info)

        if col_info.get("null_pct", 0) > 50:
            warnings.append(f"Column '{col}' is {col_info['null_pct']}% null")
        if col_info.get("n_unique") == 1:
            warnings.append(f"Column '{col}' is constant — exclude from analysis")
        if col_info.get("n_unique") == n_rows and not pd.api.types.is_numeric_dtype(s):
            warnings.append(f"Column '{col}' looks like an ID (n_unique == n_rows)")
        if str(s.dtype) == "object":
            sample = s.dropna().astype(str).head(20)
            if len(sample) and sample.str.match(r"^\d{4}-\d{2}-\d{2}").mean() > 0.8:
                warnings.append(f"Column '{col}' looks like a date stored as object — consider datetime parsing")

    pk_candidates = detect_pk_candidates(df)
    duplicates = {
        "by_pk": int(df.duplicated(subset=pk_candidates).sum()) if pk_candidates else None,
        "exact_row": int(df.duplicated().sum()),
    }

    head_5 = df.head(5).to_dict(orient="records")
    tail_5 = df.tail(5).to_dict(orient="records")

    out = {
        "path": os.path.abspath(args.path),
        "format": fmt,
        "n_rows": int(n_rows),
        "n_cols": int(n_cols),
        "columns": columns,
        "truncated_cols": truncated,
        "primary_key_candidates": pk_candidates,
        "duplicates": duplicates,
        "head_5": _safe_records(head_5),
        "tail_5": _safe_records(tail_5),
        "warnings": warnings,
    }

    print(json.dumps(out, indent=2, default=str))


def _safe_records(records):
    out = []
    for row in records:
        new_row = {}
        for k, v in row.items():
            if isinstance(v, str) and len(v) > 200:
                new_row[k] = v[:200] + "..."
            else:
                new_row[k] = v
        out.append(new_row)
    return out


if __name__ == "__main__":
    main()
