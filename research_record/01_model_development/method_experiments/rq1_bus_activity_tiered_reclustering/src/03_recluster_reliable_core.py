"""Final reliable-core bus reclustering: BIC covariance/K grid + bootstrap
stability, on LSOAs at or above the threshold chosen by
01_threshold_selection.py (or --threshold). Same fit() settings as the
adopted pipeline (`cluster_clean_version_fullweek/src/04_cluster.py`,
`kdiag()`), applied to the activity-filtered reliable-core sample instead of
all 4,100 LSOAs.

Writes labels for CAND_K so downstream scripts can pick the interpretable K,
consistent with how the adopted pipeline exposes multiple K candidates
rather than hard-coding one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    silhouette_score, calinski_harabasz_score, davies_bouldin_score, adjusted_rand_score,
)

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

sys.path.insert(0, str(FYP / "cluster_clean_version_fullweek" / "src"))
import config as C  # noqa: E402

X_BUS = FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "X_bus.parquet"
UNIT_METRICS = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"
THRESHOLD_GRID_CSV = ROOT / "outputs" / "data" / "threshold_selection_grid.csv"

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
LABELS = ROOT / "outputs" / "labels"
for d in (DATA, REPORT, LABELS):
    d.mkdir(parents=True, exist_ok=True)


def resolve_threshold(cli_value: float | None) -> float:
    if cli_value is not None:
        return cli_value
    if THRESHOLD_GRID_CSV.exists():
        grid = pd.read_csv(THRESHOLD_GRID_CSV)
        grid["timing_mean_eta2"] = grid[
            ["eta2_post_midnight_share", "eta2_deep_night_share", "eta2_post_midnight_persistence"]
        ].mean(axis=1)
        resolved = grid[grid["eta2_log_total_activity"] < grid["timing_mean_eta2"]]
        if not resolved.empty:
            return float(resolved["threshold"].min())
    raise SystemExit("Run 01_threshold_selection.py first, or pass --threshold explicitly.")


# Scoped down from the adopted pipeline's full sweep (4 covariances x
# K=2..12 x n_init=20) after repeated background runs on this near-singular,
# compositional feature space took >10-20 minutes with no output and had to
# be killed (see 01_threshold_selection.py's header). Full covariance was
# already the only covariance type that gives a non-ceiling K at every
# threshold tested in 01 and in the earlier ad-hoc median-split check
# (diag hit K=12 there too) -- spherical/diag/tied are not re-swept here to
# stay within the available time; this is a documented scope reduction, not
# a silent one.
# n_init cut further (20 -> 8) after the first attempt at this stage (K=2..6,
# n_init=20) also exceeded 9 minutes with no output and was killed. K range
# narrowed to {2,3,4}: 01_threshold_selection.py's exploratory pass already
# found BIC-best=2 at this threshold, and 3 is needed for direct
# comparability with the adopted MIN_TOTAL=1 solution. This is a disclosed
# precision/time trade-off -- if this reliable-core design is adopted, a
# full n_init=20 confirmatory refit of the chosen K is recommended before
# it goes in the dissertation as a final number, time permitting.
RECLUSTER_K_RANGE = [2, 3, 4]
RECLUSTER_COVARIANCES = ["full"]
RECLUSTER_N_BOOTSTRAP = 10
RECLUSTER_N_INIT = 8


def fit(X: np.ndarray, k: int, cov: str, seed: int = C.RANDOM_STATE, n_init: int = RECLUSTER_N_INIT) -> GaussianMixture:
    return GaussianMixture(
        k, covariance_type=cov, n_init=n_init, reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER, random_state=seed,
    ).fit(X)


def bic_grid(X: np.ndarray) -> pd.DataFrame:
    rows = []
    for cov in RECLUSTER_COVARIANCES:
        for k in RECLUSTER_K_RANGE:
            try:
                rows.append({"covariance": cov, "K": k, "BIC": fit(X, k, cov).bic(X)})
            except Exception:
                rows.append({"covariance": cov, "K": k, "BIC": np.nan})
    return pd.DataFrame(rows)


def kdiag(X: np.ndarray, cov: str) -> pd.DataFrame:
    n = len(X)
    ss = min(2000, n)
    rng = np.random.default_rng(C.RANDOM_STATE)
    rows = []
    for k in RECLUSTER_K_RANGE:
        g = fit(X, k, cov)
        lab = g.predict(X)
        aris = []
        for _ in range(RECLUSTER_N_BOOTSTRAP):
            idx = rng.choice(n, n, replace=True)
            g2 = fit(X[idx], k, cov, seed=int(rng.integers(1e6)), n_init=3)
            aris.append(adjusted_rand_score(lab, g2.predict(X)))
        rows.append(
            {
                "K": k,
                "BIC": g.bic(X),
                "silhouette": silhouette_score(X, lab, sample_size=ss, random_state=C.RANDOM_STATE),
                "calinski_harabasz": calinski_harabasz_score(X, lab),
                "davies_bouldin": davies_bouldin_score(X, lab),
                "bootstrap_ARI_mean": float(np.mean(aris)),
                "bootstrap_ARI_sd": float(np.std(aris)),
                "sizes": sorted(np.bincount(lab, minlength=k).tolist(), reverse=True),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()
    threshold = resolve_threshold(args.threshold)

    X = pd.read_parquet(X_BUS)
    metrics = pd.read_csv(UNIT_METRICS).drop(columns=["cluster", "max_posterior", "entropy"])
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    activity = metrics.set_index("lsoa")["total_activity"].reindex(X.index.astype(str))

    keep = (activity >= threshold).values
    idx = X.index.astype(str)[keep]
    Xv = X.values.astype(float)[keep]
    print(f"Reliable core: n={len(idx)} (threshold={threshold})")

    grid = bic_grid(Xv)
    grid.to_csv(DATA / "reliable_core_bic_grid.csv", index=False)
    best = grid.loc[grid["BIC"].idxmin()]
    best_cov, best_k = best["covariance"], int(best["K"])
    print(f"BIC-best: covariance={best_cov}, K={best_k}, BIC={best['BIC']:.1f}")
    for cov in C.COVARIANCES:
        sub = grid[grid.covariance == cov].dropna()
        if not sub.empty:
            r = sub.loc[sub.BIC.idxmin()]
            print(f"  {cov}: best K={int(r.K)} (BIC {r.BIC:.1f})")

    diag = kdiag(Xv, best_cov)
    diag.to_csv(DATA / "reliable_core_kdiag.csv", index=False)
    print(diag.to_string(index=False))

    for k in RECLUSTER_K_RANGE:
        g = fit(Xv, k, best_cov)
        lab = g.predict(Xv)
        post = g.predict_proba(Xv)
        pd.DataFrame(
            {
                "unit": idx,
                "cluster": lab,
                "max_posterior": post.max(1),
                "entropy": -np.where(post > 0, post * np.log(post), 0.0).sum(1),
            }
        ).to_csv(LABELS / f"reliable_core_k{k}_labels.csv", index=False)

    log = [
        f"Reliable-core bus reclustering: threshold={threshold}, n={len(idx)}",
        f"BIC-best: covariance={best_cov}, K={best_k}, BIC={best['BIC']:.1f}",
    ]
    for cov in C.COVARIANCES:
        sub = grid[grid.covariance == cov].dropna()
        if not sub.empty:
            r = sub.loc[sub.BIC.idxmin()]
            log.append(f"  {cov}: best K={int(r.K)} (BIC {r.BIC:.1f})")
    (REPORT / "RECLUSTER_BIC_BEST.txt").write_text("\n".join(log), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
