"""Quick, low-cost check: does a lower-degrees-of-freedom covariance type
(diag) fix what Codex's 2026-07-19 audit flagged for full-covariance bus
GMM -- BIC collapsing to the K-range ceiling, near-singular covariance on
sparse/low-activity units, and instability under activity-threshold and
reg_covar changes?

Deliberately minimal: reuses the exact feature matrix already used by the
adopted pipeline (X_bus.parquet, unchanged), the exact fit() settings
(n_init, reg_covar, max_iter, random_state) from
`cluster_clean_version_fullweek/src/04_cluster.py`, and this folder's
existing geography-eta2 function. No new data engineering, no bootstrap
(kept out to stay fast) -- this is a go/no-go signal for whether a deeper,
scoped sensitivity grid is worth the time, not a replacement for one.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.metrics import adjusted_rand_score

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

sys.path.insert(0, str(FYP / "cluster_clean_version_fullweek" / "src"))
import config as C  # noqa: E402

sys.path.insert(0, str(HERE.parent))
from run_geography_diagnostic import load_lsoa_coords, eta_squared_oneway  # noqa: E402

X_BUS = FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "X_bus.parquet"
UNIT_METRICS = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

K_RANGE = list(range(2, 13))  # same range as the adopted pipeline
CHECK_COVARIANCE = "diag"
THRESHOLDS_FOR_STABILITY = [50, 250]


def fit(X: np.ndarray, k: int, cov: str, seed: int = C.RANDOM_STATE) -> GaussianMixture:
    return GaussianMixture(
        k, covariance_type=cov, n_init=C.N_INIT, reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER, random_state=seed,
    ).fit(X)


def main() -> None:
    X = pd.read_parquet(X_BUS)
    idx = X.index.astype(str)
    Xv = X.values.astype(float)

    # 1. BIC grid for diag covariance -- does it also collapse to K=12?
    bic_rows = []
    for k in K_RANGE:
        g = fit(Xv, k, CHECK_COVARIANCE)
        bic_rows.append({"K": k, "BIC": g.bic(Xv)})
    bic_df = pd.DataFrame(bic_rows)
    bic_df.to_csv(DATA / "bus_diag_bic_grid.csv", index=False)
    best_k = int(bic_df.loc[bic_df["BIC"].idxmin(), "K"])

    coords = load_lsoa_coords()
    metrics = pd.read_csv(UNIT_METRICS)[["lsoa", "total_activity", "log_total_activity"]]
    metrics["lsoa"] = metrics["lsoa"].astype(str)

    # 2. For BIC-best diag K and for K=3 (comparable to the adopted full-cov solution):
    eval_rows = []
    stability_rows = []
    for k in sorted({best_k, 3}):
        g = fit(Xv, k, CHECK_COVARIANCE)
        labels = pd.DataFrame({"lsoa": idx, "cluster": g.predict(Xv)})
        merged = labels.merge(coords, on="lsoa", how="inner").merge(metrics, on="lsoa", how="inner")

        geo_eta2 = eta_squared_oneway(merged["distance_to_centre"], merged["cluster"])
        activity_eta2 = eta_squared_oneway(merged["log_total_activity"], merged["cluster"])
        eval_rows.append(
            {
                "K": k,
                "is_bic_best_for_diag": k == best_k,
                "n_units": len(merged),
                "geo_eta2_distance": geo_eta2,
                "activity_eta2_log_total": activity_eta2,
            }
        )

        # 3. Cheap threshold-robustness check (no bootstrap; single refit per threshold)
        full_labels = labels.set_index("lsoa")["cluster"]
        for t in THRESHOLDS_FOR_STABILITY:
            keep_units = metrics.loc[metrics["total_activity"] >= t, "lsoa"]
            keep_mask = idx.isin(keep_units)
            if keep_mask.sum() < 50:
                continue
            g_sub = fit(Xv[keep_mask], k, CHECK_COVARIANCE)
            sub_labels = pd.Series(g_sub.predict(Xv[keep_mask]), index=idx[keep_mask])
            common = full_labels.index.intersection(sub_labels.index)
            ari = adjusted_rand_score(full_labels.loc[common], sub_labels.loc[common])
            stability_rows.append(
                {"K": k, "threshold": t, "n_kept": int(keep_mask.sum()), "ari_vs_full_data_labels": ari}
            )

    eval_df = pd.DataFrame(eval_rows)
    stability_df = pd.DataFrame(stability_rows)
    eval_df.to_csv(DATA / "bus_diag_geo_activity_eta2.csv", index=False)
    stability_df.to_csv(DATA / "bus_diag_threshold_stability.csv", index=False)

    full_cov_ceiling = "spherical/diag/tied all previously hit K=12 (Codex audit, full covariance was the only exception at K=3)"
    lines = [
        "# Quick check: does diag covariance fix the full-covariance instability?",
        "",
        "Same X_bus.parquet, same fit() settings as the adopted pipeline "
        "(`cluster_clean_version_fullweek/src/04_cluster.py`); only covariance_type changed to 'diag'.",
        "",
        f"## 1. Does diag also collapse to the K-range ceiling? ({full_cov_ceiling})",
        "",
        bic_df.to_markdown(index=False),
        f"",
        f"BIC-best K for diag covariance: **{best_k}**.",
        "",
        "## 2. Geography and activity-dominance at diag's BIC-best K and at K=3",
        "",
        eval_df.to_markdown(index=False),
        "",
        "Compare against the full-covariance adopted solution "
        "(`../rq1_bus_geography_diagnostic/outputs/data/bus_distance_eta2_by_k.csv`: "
        "K=3 geo eta2=0.049) and the metric~cluster result "
        "(`../rq1_context_metrics_analysis/outputs/data/bus_cluster_metric_significance.csv`: "
        "K=3 full-cov activity epsilon2=0.518).",
        "",
        "## 3. Cheap threshold-robustness (single refit, no bootstrap -- indicative only)",
        "",
        stability_df.to_markdown(index=False) if not stability_df.empty else "(no thresholds produced a usable subsample)",
        "",
        "## Reading",
        "",
        "- If diag's BIC-best K is still at the range ceiling, or activity_eta2 stays as high as "
        "full covariance's 0.518, diag alone does not fix the problem -- the issue is more likely "
        "the feature space itself (per-direction share normalisation on sparse/low-activity units), "
        "and Codex's coverage-tier design is probably necessary, not just a covariance-type swap.",
        "- If diag gives a sensible (non-ceiling) K with meaningfully lower activity_eta2 and higher "
        "threshold-robustness ARI than full covariance's 0.535/0.092 at thresholds 50/500, that is a "
        "cheap, promising direction worth a fuller (but still scoped) sensitivity grid.",
    ]
    (REPORT / "COVARIANCE_SENSITIVITY_CHECK.md").write_text("\n".join(lines), encoding="utf-8")
    print(bic_df.to_string(index=False))
    print()
    print(eval_df.to_string(index=False))
    print()
    print(stability_df.to_string(index=False))


if __name__ == "__main__":
    main()
