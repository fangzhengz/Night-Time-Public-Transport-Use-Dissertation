# -*- coding: utf-8 -*-
"""02 - GMM clustering + diagnostics, bus only -- byte-for-byte the same logic
as ../../cluster_clean_version_fullweek/src/04_cluster.py (same fit/bic_grid/
kdiag, same subsampled silhouette, same bootstrap procedure), run on the
hub-first-only feature matrix built by 01_build_features.py.

Outputs: diagnostics/bus_bic_grid.csv, bus_kdiag.csv, bus_bic_best.txt
         labels/bus_k{K}_labels.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score, adjusted_rand_score)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def fit(X, k, cov, seed=C.RANDOM_STATE, n_init=C.N_INIT):
    return GaussianMixture(k, covariance_type=cov, n_init=n_init, reg_covar=C.REG_COVAR,
                           max_iter=C.MAX_ITER, random_state=seed).fit(X)


def bic_grid(X):
    rows = []
    for cov in C.COVARIANCES:
        for k in C.K_RANGE:
            try:
                rows.append({"covariance": cov, "K": k, "BIC": fit(X, k, cov).bic(X)})
            except Exception:
                rows.append({"covariance": cov, "K": k, "BIC": np.nan})
    return pd.DataFrame(rows)


def kdiag(X, cov):
    n = len(X); ss = min(2000, n); rng = np.random.default_rng(C.RANDOM_STATE)
    rows = []
    for k in C.K_RANGE:
        g = fit(X, k, cov); lab = g.predict(X)
        aris = []
        for _ in range(C.N_BOOTSTRAP):
            idx = rng.choice(n, n, replace=True)
            g2 = fit(X[idx], k, cov, seed=int(rng.integers(1e6)), n_init=3)
            aris.append(adjusted_rand_score(lab, g2.predict(X)))
        rows.append({"K": k, "BIC": g.bic(X),
                     "silhouette": silhouette_score(X, lab, sample_size=ss, random_state=C.RANDOM_STATE),
                     "calinski_harabasz": calinski_harabasz_score(X, lab),
                     "davies_bouldin": davies_bouldin_score(X, lab),
                     "ARI": float(np.mean(aris)), "ARI_sd": float(np.std(aris)),
                     "sizes": sorted(np.bincount(lab, minlength=k).tolist(), reverse=True)})
    return pd.DataFrame(rows)


def run(ds, Xpath):
    X = pd.read_parquet(Xpath); idx = X.index; Xv = X.values.astype(float)
    log = [f"=== {ds}: X {X.shape} ==="]
    grid = bic_grid(Xv); grid.to_csv(C.DIAG / f"{ds}_bic_grid.csv", index=False)
    best = grid.loc[grid["BIC"].idxmin()]; best_cov, best_k = best["covariance"], int(best["K"])
    log.append(f"BIC-best: covariance={best_cov}, K={best_k}, BIC={best['BIC']:.1f}")
    for cov in C.COVARIANCES:
        sub = grid[grid.covariance == cov].dropna()
        if not sub.empty:
            r = sub.loc[sub.BIC.idxmin()]; log.append(f"  {cov}: best K={int(r.K)} (BIC {r.BIC:.1f})")

    d = kdiag(Xv, best_cov); d.to_csv(C.DIAG / f"{ds}_kdiag.csv", index=False)
    log.append(f"kdiag (cov={best_cov}) silhouette: " +
               ", ".join(f"K{int(r.K)}={r.silhouette:.3f}" for _, r in d.iterrows()))

    for k in C.CAND_K:
        g = fit(Xv, k, best_cov); lab = g.predict(Xv); post = g.predict_proba(Xv)
        pd.DataFrame({"unit": idx.astype(str), "cluster": lab, "max_posterior": post.max(1),
                      "entropy": -np.where(post > 0, post * np.log(post), 0.0).sum(1)}
                     ).to_csv(C.LAB / f"{ds}_k{k}_labels.csv", index=False)
    (C.DIAG / f"{ds}_bic_best.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log)); print()


def main():
    run("bus", C.FEAT / "X_bus.parquet")
    print("done")


if __name__ == "__main__":
    main()
