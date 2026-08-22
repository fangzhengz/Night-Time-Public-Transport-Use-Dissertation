# -*- coding: utf-8 -*-
"""Posterior membership diagnostic for the reported CLR K=4 solution.

The reported K=4 solution (see 02_run_clustering.py::refit_reported_solution)
only ever calls GaussianMixture.predict(), which discards the posterior
responsibilities the E-step already computed. This script refits the exact
reported model (full covariance, K=4, best seed=7, n_init=100 -- see
outputs_1805_min33/clr/run_environment.json) and calls predict_proba() to
recover per-LSOA assignment confidence (max posterior, entropy). It writes
labels unchanged (verified by ARI==1.0 against the saved labels) and never
touches cluster membership.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

VARIANT = "clr"
K = 4
COVARIANCE = "full"
BEST_SEED = 7  # from outputs_1805_min33/clr/run_environment.json, final_refit.per_k[K=4].best_seed


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    output = C.OUT / VARIANT
    X_frame = pd.read_parquet(C.FEATURES / f"X_bus_stoparea_{VARIANT}_min33.parquet")
    X_frame.index = pd.Index(X_frame.index.astype(str), name="lsoa")
    X = X_frame.to_numpy(dtype=float)

    model = GaussianMixture(
        n_components=K,
        covariance_type=COVARIANCE,
        n_init=100,
        reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER,
        random_state=BEST_SEED,
    ).fit(X)
    labels = model.predict(X).astype(int)
    post = model.predict_proba(X)
    max_posterior = post.max(axis=1)
    entropy = -np.sum(post * np.log(np.clip(post, 1e-300, 1)), axis=1)

    saved = pd.read_csv(output / "labels" / f"k{K}_labels.csv", dtype={"lsoa": str}).set_index("lsoa")
    saved = saved.loc[X_frame.index]
    ari = adjusted_rand_score(saved["cluster"].to_numpy(), labels)
    if ari < 1.0 - 1e-9:
        raise RuntimeError(f"Refit does not reproduce the reported K={K} labels (ARI={ari:.6f}).")
    log(f"Refit reproduces reported K={K} labels exactly (ARI={ari:.6f}); BIC={model.bic(X):.4f}")

    out = pd.DataFrame(
        {
            "lsoa": X_frame.index,
            "cluster": saved["cluster"].to_numpy(),
            "max_posterior": max_posterior,
            "entropy": entropy,
        }
    )
    labels_out = output / "labels" / f"k{K}_labels_with_posterior.csv"
    out.to_csv(labels_out, index=False)
    log(f"Wrote {labels_out}")

    n = len(out)
    at_one = int((max_posterior >= 0.999999).sum())
    uncertain = out.loc[max_posterior < 0.999999, "max_posterior"]

    thresholds = [0.999, 0.99, 0.95, 0.9]
    summary = {
        "variant": VARIANT,
        "K": K,
        "n": n,
        "share_at_1.0": at_one / n,
        **{f"share_ge_{t}": float((max_posterior >= t).mean()) for t in thresholds},
        "uncertain_n": int(len(uncertain)),
        "uncertain_share": len(uncertain) / n,
        "uncertain_min": float(uncertain.min()) if len(uncertain) else None,
        "uncertain_max": float(uncertain.max()) if len(uncertain) else None,
        "uncertain_median": float(uncertain.median()) if len(uncertain) else None,
        "overall_mean": float(max_posterior.mean()),
        "overall_min": float(max_posterior.min()),
    }
    summary_path = output / "diagnostics" / "posterior_membership_summary.csv"
    pd.DataFrame([summary]).to_csv(summary_path, index=False)
    log(f"Wrote {summary_path}")

    by_cluster = out.groupby("cluster")["max_posterior"].agg(["count", "mean", "min"])
    by_cluster_path = output / "diagnostics" / "posterior_membership_by_cluster.csv"
    by_cluster.to_csv(by_cluster_path)
    log(f"Wrote {by_cluster_path}")

    log("")
    log(f"n = {n}")
    log(f"Share with max_posterior >= 0.999999 (effectively 1.0): {at_one} ({at_one/n*100:.1f}%)")
    for t in thresholds:
        log(f"Share with max_posterior >= {t}: {(max_posterior>=t).mean()*100:.1f}%")
    log(
        f"Remaining {len(uncertain)} LSOAs ({len(uncertain)/n*100:.1f}%) range "
        f"{uncertain.min():.4f}-{uncertain.max():.4f} (median {uncertain.median():.4f})"
    )
    log("")
    log(by_cluster)


if __name__ == "__main__":
    main()
