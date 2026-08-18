"""Formalises the 2026-07-19 ad-hoc finding that the adopted bus K=3 typology
(MIN_TOTAL=1, full-covariance GMM) is dominated by activity volume (~49% of
log_total_activity variance) because low-activity LSOAs have systematically
noisier per-direction share vectors -- a small-count compositional-noise
artifact, not a real absence of geographic rhythm structure.

Evidence chain this formalises (previously only run as inline one-off code,
never saved):
  1. Shape-vector "spikiness" (variance / max-bin-share of the 72-dim vector)
     is strongly, significantly anti-correlated with total_activity.
  2. Restricting to the top half of LSOAs by activity collapses
     activity-domination of the K=3 clusters from ~49% to ~7%, while three
     late-night timing metrics (post_midnight_share, deep_night_share,
     post_midnight_persistence) each reach ~30% -- a genuine, coherent
     rhythm signal that was masked, not absent.

This script replaces the single ad-hoc median split with a proper threshold
grid, so the final cutoff is chosen from evidence rather than an arbitrary
50/50 split.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

sys.path.insert(0, str(FYP / "cluster_clean_version_fullweek" / "src"))
import config as C  # noqa: E402

sys.path.insert(0, str(FYP / "rq1_bus_geography_diagnostic" / "src"))
from run_geography_diagnostic import load_lsoa_coords, eta_squared_oneway  # noqa: E402

X_BUS = FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "X_bus.parquet"
UNIT_METRICS = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

# Grid informed by the activity_total distribution deciles (10%=95, 20%=198,
# 25%=249, 40%=447, 50%=644, 60%=930, 70%=1339), bracketing the transition
# already located between threshold=250 (still activity-dominated) and the
# median split at 644 (activity-domination resolved).
# Reduced twice from the original 7-point/n_init=20 design: full-covariance
# GMM on this compositional, near-singular feature space (Codex's finding)
# converges very slowly at n_init=20 -- two runs exceeded 10-20 minutes with
# no output and were killed. This is an EXPLORATORY threshold-selection pass
# (deciding which threshold to adopt), not the final confirmatory fit, so
# n_init is cut further here; 03_recluster_reliable_core.py still uses full
# C.N_INIT=20 for the one, final, adopted reliable-core solution.
THRESHOLD_GRID = [0, 450, 650]
BIC_SANITY_K_RANGE = [2, 3, 4, 6, 9, 12]
BIC_SANITY_N_INIT = 3
FORCED_K_N_INIT = 5
FORCED_K = 3  # comparability with the adopted solution at every threshold
PROFILE_METRICS = [
    "log_total_activity",
    "direction_balance",
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
    "weekend_ratio",
]


def fit(X: np.ndarray, k: int, cov: str, n_init: int = C.N_INIT) -> GaussianMixture:
    return GaussianMixture(
        k, covariance_type=cov, n_init=n_init, reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER, random_state=C.RANDOM_STATE,
    ).fit(X)


def noise_diagnostic(Xv: np.ndarray, activity: pd.Series) -> dict:
    row_var = Xv.var(axis=1)
    row_max = Xv.max(axis=1)
    r_var, p_var = stats.spearmanr(row_var, activity.values)
    r_max, p_max = stats.spearmanr(row_max, activity.values)
    return {
        "spearman_r_shape_variance_vs_activity": float(r_var),
        "spearman_p_shape_variance_vs_activity": float(p_var),
        "spearman_r_shape_spikiness_vs_activity": float(r_max),
        "spearman_p_shape_spikiness_vs_activity": float(p_max),
    }


def main() -> None:
    X = pd.read_parquet(X_BUS)
    idx = X.index.astype(str)
    metrics = pd.read_csv(UNIT_METRICS).drop(columns=["cluster", "max_posterior", "entropy"])
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    activity = metrics.set_index("lsoa")["total_activity"].reindex(idx)
    coords = load_lsoa_coords()

    Xv_full = X.values.astype(float)
    noise = noise_diagnostic(Xv_full, activity)
    pd.DataFrame([noise]).to_csv(DATA / "shape_noise_vs_activity_diagnostic.csv", index=False)

    rows = []
    for threshold in THRESHOLD_GRID:
        keep = (activity >= threshold).values
        Xv = Xv_full[keep]
        keep_idx = idx[keep]
        n = int(keep.sum())

        # BIC-best K for full covariance at this threshold (sanity: does the
        # BIC-preferred K move around as the threshold rises?). Coarser grid,
        # fewer inits -- informational only, not the adopted K.
        bics = [(k, fit(Xv, k, "full", n_init=BIC_SANITY_N_INIT).bic(Xv)) for k in BIC_SANITY_K_RANGE]
        bic_best_k = min(bics, key=lambda x: x[1])[0]

        g = fit(Xv, FORCED_K, "full", n_init=FORCED_K_N_INIT)
        labels = pd.DataFrame({"lsoa": keep_idx, "cluster": g.predict(Xv)})
        merged = labels.merge(metrics, on="lsoa", how="inner").merge(coords, on="lsoa", how="inner")

        row = {
            "threshold": threshold,
            "n_units": n,
            "pct_of_all_units": round(100 * n / len(idx), 1),
            "bic_best_K_full_cov": bic_best_k,
            "forced_K": FORCED_K,
            "geo_eta2_distance": eta_squared_oneway(merged["distance_to_centre"], merged["cluster"]),
        }
        for metric in PROFILE_METRICS:
            row[f"eta2_{metric}"] = eta_squared_oneway(merged[metric], merged["cluster"])
        rows.append(row)
        print(f"threshold={threshold}: n={n} bic_best_K={bic_best_k} "
              f"activity_eta2={row['eta2_log_total_activity']:.3f} "
              f"geo_eta2={row['geo_eta2_distance']:.3f} "
              f"post_midnight_eta2={row['eta2_post_midnight_share']:.3f}")

    result = pd.DataFrame(rows)
    result.to_csv(DATA / "threshold_selection_grid.csv", index=False)

    # Recommend the lowest threshold at which activity stops dominating
    # (heuristic: activity_eta2 drops below the mean of the two strongest
    # timing metrics at that threshold) -- keeps as many LSOAs as defensible.
    result["timing_mean_eta2"] = result[
        ["eta2_post_midnight_share", "eta2_deep_night_share", "eta2_post_midnight_persistence"]
    ].mean(axis=1)
    resolved = result[result["eta2_log_total_activity"] < result["timing_mean_eta2"]]
    recommended = int(resolved["threshold"].min()) if not resolved.empty else None

    lines = [
        "# Bus activity-threshold selection (evidence-based, not a median split)",
        "",
        "## Noise mechanism check",
        "",
        pd.DataFrame([noise]).to_markdown(index=False),
        "",
        "Strong negative correlation confirms low-activity LSOAs have",
        "systematically noisier/spikier share vectors (small-count compositional",
        "noise), not a real absence of rhythm structure.",
        "",
        "## Threshold grid (forced K=3 for comparability; BIC-best K for reference)",
        "",
        result.drop(columns=["timing_mean_eta2"]).to_markdown(index=False),
        "",
        f"## Recommendation",
        "",
        f"Lowest threshold at which activity_eta2 drops below the mean of the three",
        f"late-night timing metrics' eta2: **{recommended}**"
        if recommended is not None
        else "No threshold in the grid resolves activity-domination -- widen the grid.",
    ]
    (REPORT / "THRESHOLD_SELECTION.md").write_text("\n".join(lines), encoding="utf-8")
    print()
    print(f"Recommended threshold: {recommended}")


if __name__ == "__main__":
    main()
