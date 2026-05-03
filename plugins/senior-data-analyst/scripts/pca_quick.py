#!/usr/bin/env python3
"""
PCA with scree plot, loadings, and 80% variance cutoff suggestion.

Usage:
    python3 pca_quick.py <path> [--exclude COL,COL,...] [--n-components auto|N]
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--exclude", default="", help="Comma-separated cols to exclude (e.g. ID, target)")
    p.add_argument("--n-components", default="auto",
                   help="auto = pick at 80% variance, or specify integer")
    p.add_argument("--out-dir", default="./analysis_out")
    args = p.parse_args()

    try:
        import pandas as pd
        import numpy as np
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
    except ImportError as e:
        print(json.dumps({"error": f"missing dep: {e}; pip install pandas numpy scikit-learn matplotlib"}))
        sys.exit(1)

    ext = Path(args.path).suffix.lower().lstrip(".")
    if ext == "csv":
        df = pd.read_csv(args.path)
    elif ext == "tsv":
        df = pd.read_csv(args.path, sep="\t")
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(args.path)
    elif ext == "parquet":
        df = pd.read_parquet(args.path)
    else:
        df = pd.read_csv(args.path)

    exclude = [c.strip() for c in args.exclude.split(",") if c.strip()]
    X_full = df.drop(columns=exclude, errors="ignore").select_dtypes(include="number")
    X = X_full.dropna()

    if X.shape[1] < 3:
        print(json.dumps({"error": f"PCA needs >=3 numeric columns, got {X.shape[1]}"}))
        sys.exit(1)
    if len(X) < 5 * X.shape[1]:
        warning = (f"WARNING: n_samples ({len(X)}) < 5 * n_features ({X.shape[1]}). "
                   "PCA stability is poor. Consider more data or fewer features.")
    else:
        warning = None

    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)

    full = PCA().fit(X_std)
    explained = full.explained_variance_ratio_
    cumulative = explained.cumsum()
    n_for_80 = int((cumulative >= 0.80).argmax() + 1) if (cumulative >= 0.80).any() else len(explained)

    if args.n_components == "auto":
        n_kept = n_for_80
    else:
        n_kept = int(args.n_components)

    pca = PCA(n_components=n_kept).fit(X_std)
    loadings = pca.components_.T  # shape (n_features, n_kept)
    feature_names = X.columns.tolist()

    components = []
    for k in range(n_kept):
        loads = [(feature_names[i], round(float(loadings[i, k]), 4))
                 for i in range(len(feature_names))]
        loads_sorted = sorted(loads, key=lambda t: -abs(t[1]))
        components.append({
            "component": f"PC{k+1}",
            "variance_explained": round(float(explained[k]), 4),
            "cumulative_variance": round(float(cumulative[k]), 4),
            "top_loadings": loads_sorted[:8],
        })

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "pca_results.json"
    with open(json_path, "w") as f:
        json.dump({
            "n_samples": len(X),
            "n_features_in": X.shape[1],
            "n_components_kept": n_kept,
            "n_components_for_80pct": n_for_80,
            "all_explained_variance": [round(float(v), 4) for v in explained],
            "all_cumulative": [round(float(v), 4) for v in cumulative],
            "components": components,
            "warning": warning,
        }, f, indent=2)

    # Scree plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig_path = out_dir / "pca_scree.png"
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ks = list(range(1, len(explained) + 1))
        ax1.bar(ks, explained, alpha=0.6, label="Variance explained")
        ax1.set_xlabel("Component")
        ax1.set_ylabel("Variance explained per component")
        ax2 = ax1.twinx()
        ax2.plot(ks, cumulative, color="red", marker="o", label="Cumulative")
        ax2.axhline(0.80, color="grey", linestyle="--", linewidth=0.8)
        ax2.set_ylabel("Cumulative variance")
        ax2.set_ylim(0, 1.05)
        plt.title(f"PCA scree (n_features={X.shape[1]}, 80% at PC{n_for_80})")
        plt.tight_layout()
        plt.savefig(fig_path, dpi=120)
        plt.close()
        scree_path = str(fig_path)
    except Exception as e:
        scree_path = None

    print(json.dumps({
        "n_samples": len(X),
        "n_features_in": X.shape[1],
        "n_components_kept": n_kept,
        "n_components_for_80pct": n_for_80,
        "first_3_components_variance": [round(float(v), 4) for v in explained[:3]],
        "components_summary": components[:3],
        "json_path": str(json_path),
        "scree_path": scree_path,
        "warning": warning,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
