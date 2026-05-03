#!/usr/bin/env python3
"""
Ensemble feature importance: LASSO + RandomForest + Mutual Info, with bootstrap stability.

Usage:
    python3 feature_importance.py <path> --target COL [--n-bootstrap 200] [--task auto|reg|cls]

Outputs ranked features. Only features in top-k of >=2 methods are reported as stable.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--target", required=True)
    p.add_argument("--n-bootstrap", type=int, default=200)
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--out-dir", default="./analysis_out")
    p.add_argument("--task", choices=["auto", "reg", "cls"], default="auto")
    args = p.parse_args()

    try:
        import pandas as pd
        import numpy as np
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LassoCV, LogisticRegressionCV
        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
        from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
        from sklearn.utils import resample
    except ImportError as e:
        print(json.dumps({"error": f"missing dep: {e}; pip install pandas numpy scikit-learn"}))
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

    if args.target not in df.columns:
        print(json.dumps({"error": f"target '{args.target}' not in columns"}))
        sys.exit(1)

    y = df[args.target]
    X_full = df.drop(columns=[args.target]).select_dtypes(include="number")
    mask = y.notna() & X_full.notna().all(axis=1)
    X = X_full[mask].copy()
    y = y[mask].copy()

    if len(X) < 30:
        print(json.dumps({"error": f"too few samples ({len(X)}) for stable feature importance"}))
        sys.exit(1)
    if X.shape[1] == 0:
        print(json.dumps({"error": "no numeric features other than target"}))
        sys.exit(1)

    # Detect task
    if args.task == "auto":
        if y.nunique() <= 10 and y.dtype != float:
            task = "cls"
        else:
            task = "reg"
    else:
        task = args.task

    feature_names = X.columns.tolist()
    n_features = len(feature_names)

    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bootstrap_ranks = {
        "lasso": np.zeros((args.n_bootstrap, n_features)),
        "rf": np.zeros((args.n_bootstrap, n_features)),
        "mi": np.zeros((args.n_bootstrap, n_features)),
    }

    rng = np.random.RandomState(42)

    for b in range(args.n_bootstrap):
        idx = rng.randint(0, len(X), size=len(X))
        Xb = X_std[idx]
        yb = y.values[idx]

        # LASSO / Logistic-L1
        try:
            if task == "reg":
                m = LassoCV(cv=3, max_iter=2000, random_state=42).fit(Xb, yb)
                imp = np.abs(m.coef_)
            else:
                m = LogisticRegressionCV(cv=3, penalty="l1", solver="saga",
                                         max_iter=1000, random_state=42).fit(Xb, yb)
                imp = np.abs(m.coef_).mean(axis=0) if m.coef_.ndim > 1 else np.abs(m.coef_)
            bootstrap_ranks["lasso"][b] = _to_rank(imp)
        except Exception:
            pass

        # RandomForest
        try:
            if task == "reg":
                rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1).fit(Xb, yb)
            else:
                rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1).fit(Xb, yb)
            bootstrap_ranks["rf"][b] = _to_rank(rf.feature_importances_)
        except Exception:
            pass

        # Mutual info
        try:
            if task == "reg":
                mi = mutual_info_regression(Xb, yb, random_state=42)
            else:
                mi = mutual_info_classif(Xb, yb, random_state=42)
            bootstrap_ranks["mi"][b] = _to_rank(mi)
        except Exception:
            pass

    summary = []
    for i, name in enumerate(feature_names):
        ranks = {m: bootstrap_ranks[m][:, i].mean() for m in bootstrap_ranks}
        ranks_std = {m: bootstrap_ranks[m][:, i].std() for m in bootstrap_ranks}
        avg_rank = float(np.mean(list(ranks.values())))
        summary.append({
            "feature": name,
            "avg_rank": round(avg_rank, 2),
            "lasso_rank_mean": round(float(ranks["lasso"]), 2),
            "lasso_rank_std": round(float(ranks_std["lasso"]), 2),
            "rf_rank_mean": round(float(ranks["rf"]), 2),
            "rf_rank_std": round(float(ranks_std["rf"]), 2),
            "mi_rank_mean": round(float(ranks["mi"]), 2),
            "mi_rank_std": round(float(ranks_std["mi"]), 2),
        })

    summary.sort(key=lambda r: r["avg_rank"])

    # Stability: a feature is "stable top-k" if it appears in top-k of >=2 methods on average
    top_k = args.top_k
    stable = []
    for r in summary:
        in_top_k = sum(1 for m in ("lasso", "rf", "mi") if r[f"{m}_rank_mean"] <= top_k)
        r["methods_with_top_k"] = in_top_k
        if in_top_k >= 2:
            stable.append(r["feature"])

    json_path = out_dir / "feature_importance.json"
    with open(json_path, "w") as f:
        json.dump({
            "task": task,
            "target": args.target,
            "n_samples": len(X),
            "n_features": n_features,
            "n_bootstrap": args.n_bootstrap,
            "top_k_threshold": top_k,
            "stable_top_features": stable,
            "ranking": summary,
        }, f, indent=2)

    print(json.dumps({
        "task": task,
        "n_samples": len(X),
        "n_features": n_features,
        "stable_top_features": stable,
        "top_5_by_avg_rank": summary[:5],
        "json_path": str(json_path),
    }, indent=2, default=str))


def _to_rank(scores):
    """Higher score → lower rank number (1 is best)."""
    import numpy as np
    s = np.asarray(scores, dtype=float)
    s = np.nan_to_num(s, nan=0.0)
    order = (-s).argsort()
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(s) + 1)
    return ranks


if __name__ == "__main__":
    main()
