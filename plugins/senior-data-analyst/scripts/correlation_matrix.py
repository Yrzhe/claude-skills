#!/usr/bin/env python3
"""
Correlation matrix with FDR-adjusted p-values for senior-data-analyst.

Usage:
    python3 correlation_matrix.py <path> [--target COL] [--out-dir DIR]

Computes Pearson + Spearman for every (X, target) pair (or full matrix if no target).
Applies Benjamini-Hochberg FDR correction. Saves heatmap PNG and JSON results.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def detect_format(path):
    ext = Path(path).suffix.lower().lstrip(".")
    return {"csv": "csv", "tsv": "tsv", "xlsx": "xlsx", "parquet": "parquet"}.get(ext, "csv")


def load_df(path, fmt):
    import pandas as pd
    if fmt == "csv":
        return pd.read_csv(path)
    if fmt == "tsv":
        return pd.read_csv(path, sep="\t")
    if fmt == "xlsx":
        return pd.read_excel(path)
    if fmt == "parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def fdr_bh(pvalues):
    """Benjamini-Hochberg FDR correction. Returns adjusted p-values."""
    import numpy as np
    p = np.asarray(pvalues, dtype=float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(adj, 1.0)
    return out


def fisher_ci(r, n, alpha=0.05):
    """95% CI for a correlation via Fisher z transform."""
    import numpy as np
    if abs(r) >= 1 or n <= 3:
        return (None, None)
    z = 0.5 * np.log((1 + r) / (1 - r))
    se = 1 / (n - 3) ** 0.5
    z_crit = 1.959963984540054  # 1.96 for 95%
    lo, hi = z - z_crit * se, z + z_crit * se
    return (float(np.tanh(lo)), float(np.tanh(hi)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--target", default=None,
                   help="Target column. If set, returns target-vs-X table; if not, full matrix.")
    p.add_argument("--out-dir", default="./analysis_out",
                   help="Where to save outputs")
    p.add_argument("--method", choices=["pearson", "spearman", "both"], default="both")
    args = p.parse_args()

    try:
        import pandas as pd
        import numpy as np
        from scipy import stats
    except ImportError as e:
        print(json.dumps({"error": f"missing dependency: {e}; pip install pandas scipy matplotlib seaborn"}))
        sys.exit(1)

    fmt = detect_format(args.path)
    df = load_df(args.path, fmt)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if args.target:
        if args.target not in df.columns:
            print(json.dumps({"error": f"target '{args.target}' not in columns"}))
            sys.exit(1)
        if args.target not in numeric_cols:
            print(json.dumps({"error": f"target '{args.target}' is not numeric"}))
            sys.exit(1)
        x_cols = [c for c in numeric_cols if c != args.target]
    else:
        x_cols = numeric_cols

    results = []
    pearson_pvals = []
    spearman_pvals = []

    if args.target:
        y = df[args.target]
        for col in x_cols:
            x = df[col]
            mask = x.notna() & y.notna()
            n = int(mask.sum())
            if n < 3:
                continue
            x_clean, y_clean = x[mask], y[mask]
            row = {"feature": col, "n": n}

            if args.method in ("pearson", "both"):
                try:
                    r_p, p_p = stats.pearsonr(x_clean, y_clean)
                    lo, hi = fisher_ci(r_p, n)
                    row["pearson_r"] = round(float(r_p), 4)
                    row["pearson_p"] = float(p_p)
                    row["pearson_ci"] = [round(lo, 4) if lo else None, round(hi, 4) if hi else None]
                    pearson_pvals.append(p_p)
                except Exception as e:
                    row["pearson_error"] = str(e)

            if args.method in ("spearman", "both"):
                try:
                    r_s, p_s = stats.spearmanr(x_clean, y_clean)
                    lo, hi = fisher_ci(r_s, n)
                    row["spearman_r"] = round(float(r_s), 4)
                    row["spearman_p"] = float(p_s)
                    row["spearman_ci"] = [round(lo, 4) if lo else None, round(hi, 4) if hi else None]
                    spearman_pvals.append(p_s)
                except Exception as e:
                    row["spearman_error"] = str(e)

            results.append(row)

        # FDR adjustment
        if pearson_pvals:
            adj_p = fdr_bh(pearson_pvals)
            pi = 0
            for row in results:
                if "pearson_p" in row:
                    row["pearson_p_fdr"] = float(adj_p[pi])
                    pi += 1
        if spearman_pvals:
            adj_s = fdr_bh(spearman_pvals)
            si = 0
            for row in results:
                if "spearman_p" in row:
                    row["spearman_p_fdr"] = float(adj_s[si])
                    si += 1

        results.sort(key=lambda r: -abs(r.get("spearman_r", r.get("pearson_r", 0))))

        json_path = out_dir / "correlation_with_target.json"
        with open(json_path, "w") as f:
            json.dump({
                "target": args.target,
                "n_features": len(results),
                "results": results,
            }, f, indent=2)

        out = {
            "mode": "target",
            "target": args.target,
            "n_features": len(results),
            "json_path": str(json_path),
            "top_5_by_spearman_abs": results[:5],
        }
    else:
        # Full pairwise matrix
        if args.method == "spearman":
            mat = df[numeric_cols].corr(method="spearman")
        else:
            mat = df[numeric_cols].corr(method="pearson")
        json_path = out_dir / "correlation_matrix.json"
        mat.to_json(json_path)
        out = {
            "mode": "full_matrix",
            "n_cols": len(numeric_cols),
            "json_path": str(json_path),
            "columns": numeric_cols,
        }

    # Heatmap
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns

        fig_path = out_dir / "correlation_heatmap.png"
        if args.target:
            r_col = "spearman_r" if args.method != "pearson" else "pearson_r"
            heat_df = pd.DataFrame({
                "feature": [r["feature"] for r in results],
                r_col: [r.get(r_col, 0) for r in results],
            }).set_index("feature")
            plt.figure(figsize=(6, max(4, 0.35 * len(heat_df))))
            sns.heatmap(heat_df, annot=True, cmap="RdBu_r", center=0, fmt=".2f", vmin=-1, vmax=1)
            plt.title(f"Correlation with {args.target}")
        else:
            plt.figure(figsize=(max(6, 0.5 * len(numeric_cols)), max(5, 0.5 * len(numeric_cols))))
            sns.heatmap(mat, annot=True, cmap="RdBu_r", center=0, fmt=".2f", vmin=-1, vmax=1)
            plt.title("Correlation matrix")
        plt.tight_layout()
        plt.savefig(fig_path, dpi=120)
        plt.close()
        out["heatmap_path"] = str(fig_path)
    except Exception as e:
        out["heatmap_error"] = str(e)

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
