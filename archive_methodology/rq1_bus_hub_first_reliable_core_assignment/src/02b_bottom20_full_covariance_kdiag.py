"""Full-covariance-only K diagnostics and bootstrap for the bottom-20%-excluded
sample, following the same convention used throughout this investigation
(spherical/diag/tied are known to select degenerate ceiling-K solutions with
singleton clusters -- see bottom20_excluded_bic_grid.csv, tied K=8/9/11/12
all have min_cluster_n=1). This script re-fits only covariance=full for
K=2..12 on the same core sample as 02_bottom20_excluded_bic.py and computes
the identical diagnostics (activity/timing effect sizes, silhouette,
bootstrap stability), so the two covariance families can be compared on
equal footing.

Writes only inside rq1_bus_hub_first_reliable_core_assignment/outputs.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent
BASE_SRC = FYP / "rq1_bus_hub_first_reclustering" / "src"
sys.path.insert(0, str(BASE_SRC))
import config as C  # noqa: E402
import run_fullweek_first_pass as base  # noqa: E402

X_INPUT = (
    FYP / "rq1_bus_hub_first_reclustering_alpha_sensitivity" / "outputs" / "features"
    / "X_bus_fullweek_alpha0_fixed_sample.parquet"
)
META_INPUT = FYP / "rq1_bus_hub_first_reclustering" / "outputs" / "features" / "bus_fullweek_meta_alpha5.csv"
METRICS_INPUT = FYP / "rq1_bus_hub_first_alpha_grid_screen" / "outputs" / "data" / "hub_first_raw_metrics.csv"

OUT = ROOT / "outputs"
DATA = OUT / "data"
DIAGNOSTICS = OUT / "diagnostics"
REPORT = OUT / "report"

TIMING_METRICS = ["post_midnight_share", "deep_night_share", "post_midnight_persistence"]
EXCLUDE_QUANTILE = 0.20
K_RANGE = list(range(2, 13))
PROFILE_K = list(range(2, 9))
BOOTSTRAP_REPLICATES = 20


def log(msg: str) -> None:
    print(msg, flush=True)


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = float(y.mean())
    total = float(np.square(y - grand).sum())
    if total <= 0:
        return float("nan")
    between = sum(int((labels == c).sum()) * (float(y[labels == c].mean()) - grand) ** 2 for c in np.unique(labels))
    return float(between / total)


def kw_epsilon_squared(values: pd.Series, labels: np.ndarray) -> float:
    groups = [values.to_numpy(dtype=float)[labels == c] for c in np.unique(labels)]
    result = stats.kruskal(*groups)
    n = sum(len(g) for g in groups)
    k = len(groups)
    return float((float(result.statistic) - k + 1) / (n - k))


def main() -> None:
    started = time.time()
    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)
    metrics = pd.read_csv(METRICS_INPUT)
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    metrics = metrics.set_index("lsoa").reindex(X.index)

    cutoff = float(meta["total_activity"].quantile(EXCLUDE_QUANTILE))
    keep_mask = meta["total_activity"].to_numpy(dtype=float) >= cutoff
    X_core = X.loc[keep_mask]
    metrics_core = metrics.loc[keep_mask]
    Xv = X_core.to_numpy(dtype=float)
    log(f"n_core={len(Xv)} (cutoff={cutoff:.2f})")

    log("Fitting full covariance K=2..12, n_init=20")
    rows = []
    labels_by_k: dict[int, np.ndarray] = {}
    for k in K_RANGE:
        model, _, seconds = base.fit_gmm(Xv, k, "full", C.RANDOM_STATE, C.N_INIT)
        labels = model.predict(Xv)
        labels_by_k[k] = labels
        row = {
            "K": k,
            "BIC": float(model.bic(Xv)),
            "silhouette": float(silhouette_score(Xv, labels)),
            "davies_bouldin": float(davies_bouldin_score(Xv, labels)),
            "activity_eta2": eta_squared(metrics_core["log_total_activity"], labels),
            "activity_kw_epsilon2": kw_epsilon_squared(metrics_core["log_total_activity"], labels),
            "timing_mean_eta2": float(np.mean([eta_squared(metrics_core[m], labels) for m in TIMING_METRICS])),
            "direction_balance_eta2": eta_squared(metrics_core["direction_balance"], labels),
            "weekend_ratio_eta2": eta_squared(metrics_core["weekend_ratio"], labels),
            **base.cluster_size_metrics(labels, k),
        }
        row["gate_activity_below_timing"] = row["activity_eta2"] < row["timing_mean_eta2"]
        rows.append(row)
        log(
            f"  K={k:2d} BIC={row['BIC']:.1f} sil={row['silhouette']:.3f} "
            f"activity_eta2={row['activity_eta2']:.3f} timing_mean_eta2={row['timing_mean_eta2']:.3f} "
            f"pass={row['gate_activity_below_timing']} min_share={row['min_cluster_share']:.3f} ({seconds:.1f}s)"
        )
    kdiag = pd.DataFrame(rows)

    log(f"Bootstrap K={PROFILE_K}, n={BOOTSTRAP_REPLICATES}, n_init={C.BOOTSTRAP_N_INIT}")
    rng = np.random.default_rng(C.RANDOM_STATE)
    boot_rows = []
    for k in PROFILE_K:
        base_labels = labels_by_k[k]
        for replicate in range(BOOTSTRAP_REPLICATES):
            idx = rng.choice(len(Xv), size=len(Xv), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model, _, _ = base.fit_gmm(Xv[idx], k, "full", seed, C.BOOTSTRAP_N_INIT)
            predicted = model.predict(Xv)
            matched = base.matched_jaccard(base_labels, predicted, k)
            boot_rows.append(
                {
                    "K": k,
                    "replicate": replicate + 1,
                    "ARI": float(adjusted_rand_score(base_labels, predicted)),
                    "mean_matched_cluster_jaccard": float(matched.mean()),
                    "min_matched_cluster_jaccard": float(matched.min()),
                }
            )
        sub = pd.DataFrame(boot_rows)
        sub = sub[sub["K"] == k]
        log(f"  K={k}: ARI mean={sub['ARI'].mean():.3f}; min-cluster Jaccard mean={sub['min_matched_cluster_jaccard'].mean():.3f}")
    bootstrap = pd.DataFrame(boot_rows)
    boot_summary = bootstrap.groupby("K", as_index=False).agg(
        bootstrap_ari_mean=("ARI", "mean"),
        bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")

    kdiag.to_csv(DIAGNOSTICS / "bottom20_excluded_full_covariance_kdiag.csv", index=False)
    bootstrap.to_csv(DIAGNOSTICS / "bottom20_excluded_full_covariance_bootstrap.csv", index=False)
    log(f"Done in {time.time()-started:.1f}s")
    log(str(DIAGNOSTICS / "bottom20_excluded_full_covariance_kdiag.csv"))


if __name__ == "__main__":
    main()
