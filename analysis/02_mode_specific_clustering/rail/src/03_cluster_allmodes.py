from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    silhouette_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    adjusted_rand_score,
)

"""03 - GMM clustering + diagnostics on the ALL-MODES rail feature matrix.

Reuses the exact GMM search methodology from
`FYP/analysis/02_mode_specific_clustering/rail/src/04_cluster.py` (same K_RANGE, N_INIT,
REG_COVAR, MAX_ITER, RANDOM_STATE): a BIC grid picks the best covariance
family, then a K-sweep computes silhouette / CH / DB / bootstrap ARI, and
labels are saved for a band of candidate K.

Scope note: the BIC grid here is restricted to {diag, full} rather than the
canonical {spherical, diag, tied, full} -- diag is the family the canonical
270-station rail result actually uses, and full is kept as a cross-check;
spherical/tied are not part of the comparison this test is designed to
answer (see plan). The K-sweep / bootstrap / saved labels all use diag
specifically, so they are directly comparable to the canonical
rail_kdiag.csv / rail_k{K}_labels.csv, which are also diag-covariance.
"""

DATA_DIR = Path(__file__).resolve().parents[1] / "outputs" / "data"
X_PATH = DATA_DIR / "X_rail_allmodes.parquet"

K_RANGE = list(range(2, 13))
COVARIANCES = ["diag", "full"]
# 2026-08-01: raised from 20 to 100. The widened 440-dim feature matrix does
# NOT converge at 20 -- it lands on a local optimum whose BIC is 709.7 worse
# than the one reached from n_init >= 50, and that inferior optimum produced a
# MORE attractive-looking typology (a clean 19-station West End cluster) than
# the correct one, so the failure mode is not visibly broken output. Verified
# on this matrix: identical partitions at n_init 50/100/200/300.
# The former 344-dim matrix did converge at 20, so this changes nothing about
# the archived result -- but any future feature-space change must re-check.
N_INIT = 100
REG_COVAR = 1e-6
MAX_ITER = 300
RANDOM_STATE = 42
N_BOOTSTRAP = 20
CAND_K = list(range(3, 9))  # 3..8, matches canonical
PRIMARY_COVARIANCE = "diag"  # what canonical rail actually uses


def fit(X, k, cov, seed=RANDOM_STATE, n_init=N_INIT):
    return GaussianMixture(
        k,
        covariance_type=cov,
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    ).fit(X)


def bic_grid(X):
    rows = []
    for cov in COVARIANCES:
        for k in K_RANGE:
            try:
                rows.append({"covariance": cov, "K": k, "BIC": fit(X, k, cov).bic(X)})
            except Exception as exc:
                print(f"  [warn] cov={cov} K={k} failed: {exc}")
                rows.append({"covariance": cov, "K": k, "BIC": np.nan})
    return pd.DataFrame(rows)


def kdiag(X, cov):
    n = len(X)
    ss = min(2000, n)
    rng = np.random.default_rng(RANDOM_STATE)
    rows = []
    for k in K_RANGE:
        g = fit(X, k, cov)
        lab = g.predict(X)
        aris = []
        for _ in range(N_BOOTSTRAP):
            idx = rng.choice(n, n, replace=True)
            g2 = fit(X[idx], k, cov, seed=int(rng.integers(1e6)), n_init=3)
            aris.append(adjusted_rand_score(lab, g2.predict(X)))
        rows.append(
            {
                "K": k,
                "BIC": g.bic(X),
                "silhouette": silhouette_score(X, lab, sample_size=ss, random_state=RANDOM_STATE),
                "calinski_harabasz": calinski_harabasz_score(X, lab),
                "davies_bouldin": davies_bouldin_score(X, lab),
                "ARI": float(np.mean(aris)),
                "ARI_sd": float(np.std(aris)),
                "sizes": sorted(np.bincount(lab, minlength=k).tolist(), reverse=True),
            }
        )
        print(f"  [kdiag] K={k} done", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    X = pd.read_parquet(X_PATH)
    idx = X.index
    Xv = X.values.astype(float)
    log = [f"=== rail_allmodes: X {X.shape} ==="]

    print("[1/3] BIC grid over", COVARIANCES, flush=True)
    grid = bic_grid(Xv)
    grid.to_csv(DATA_DIR / "rail_allmodes_bic_grid.csv", index=False)
    best = grid.loc[grid["BIC"].idxmin()]
    best_cov, best_k = best["covariance"], int(best["K"])
    log.append(f"BIC-best (of {COVARIANCES}): covariance={best_cov}, K={best_k}, BIC={best['BIC']:.1f}")
    for cov in COVARIANCES:
        sub = grid[grid.covariance == cov].dropna()
        if not sub.empty:
            r = sub.loc[sub.BIC.idxmin()]
            log.append(f"  {cov}: best K={int(r.K)} (BIC {r.BIC:.1f})")

    print(f"[2/3] K-sweep diagnostics using covariance={PRIMARY_COVARIANCE} (canonical family)", flush=True)
    d = kdiag(Xv, PRIMARY_COVARIANCE)
    d.to_csv(DATA_DIR / "rail_allmodes_kdiag.csv", index=False)
    log.append(
        f"kdiag (cov={PRIMARY_COVARIANCE}) silhouette: "
        + ", ".join(f"K{int(r.K)}={r.silhouette:.3f}" for _, r in d.iterrows())
    )
    log.append(
        f"kdiag (cov={PRIMARY_COVARIANCE}) BIC: "
        + ", ".join(f"K{int(r.K)}={r.BIC:.1f}" for _, r in d.iterrows())
    )

    print(f"[3/3] Saving labels for K in {CAND_K} using covariance={PRIMARY_COVARIANCE}", flush=True)
    for k in CAND_K:
        g = fit(Xv, k, PRIMARY_COVARIANCE)
        lab = g.predict(Xv)
        post = g.predict_proba(Xv)
        log_post = np.zeros_like(post)
        np.log(post, out=log_post, where=post > 0)
        pd.DataFrame(
            {
                "unit": idx.astype(str),
                "cluster": lab,
                "max_posterior": post.max(1),
                "entropy": -(post * log_post).sum(1),
            }
        ).to_csv(DATA_DIR / f"rail_allmodes_k{k}_labels.csv", index=False)

    (DATA_DIR / "rail_allmodes_bic_best.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))
    print("done")


if __name__ == "__main__":
    main()
