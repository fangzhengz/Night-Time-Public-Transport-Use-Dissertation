"""Does raising the activity threshold also fix the K-selection instability
(non-full covariance always preferring the K-range ceiling), or only the
activity-domination/ARI symptom Codex already measured?

This is the missing piece for the threshold question: if BIC-best K stays
sensible and consistent across covariance types once low-activity units are
excluded, thresholding alone is close to sufficient. If diag/spherical still
want the ceiling K even at a stricter threshold, the instability is a
property of the feature representation itself, not just low-activity noise,
and thresholding alone will not fully resolve it.

Reuses X_bus.parquet and the adopted fit() settings unchanged; only the
input rows (which LSOAs) and covariance_type vary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]

sys.path.insert(0, str(FYP / "cluster_clean_version_fullweek" / "src"))
import config as C  # noqa: E402

X_BUS = FYP / "cluster_clean_version_fullweek" / "outputs" / "features" / "X_bus.parquet"
UNIT_METRICS = FYP / "rq1_context_metrics_analysis" / "outputs" / "data" / "bus_unit_metrics.csv"

DATA = ROOT / "outputs" / "data"
REPORT = ROOT / "outputs" / "report"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

K_RANGE = list(range(2, 13))
COVARIANCES = ["full", "diag"]
THRESHOLDS = [0, 100, 250, 500]  # 0 = current adopted (MIN_TOTAL=1) baseline


def fit(X: np.ndarray, k: int, cov: str) -> GaussianMixture:
    return GaussianMixture(
        k, covariance_type=cov, n_init=C.N_INIT, reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER, random_state=C.RANDOM_STATE,
    ).fit(X)


def main() -> None:
    X = pd.read_parquet(X_BUS)
    idx = X.index.astype(str)
    metrics = pd.read_csv(UNIT_METRICS)[["lsoa", "total_activity"]]
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    activity = metrics.set_index("lsoa")["total_activity"].reindex(idx)

    rows = []
    for threshold in THRESHOLDS:
        keep = (activity >= threshold).values
        Xv = X.values[keep].astype(float)
        n = keep.sum()
        for cov in COVARIANCES:
            bics = []
            for k in K_RANGE:
                g = fit(Xv, k, cov)
                bics.append({"K": k, "BIC": g.bic(Xv)})
            bic_df = pd.DataFrame(bics)
            best = bic_df.loc[bic_df["BIC"].idxmin()]
            rows.append(
                {
                    "threshold": threshold,
                    "n_units": int(n),
                    "covariance": cov,
                    "best_K": int(best["K"]),
                    "at_range_ceiling": bool(int(best["K"]) == K_RANGE[-1]),
                    "best_BIC": float(best["BIC"]),
                }
            )
            print(f"threshold={threshold} n={n} cov={cov}: best_K={int(best['K'])}"
                  f"{' (CEILING)' if int(best['K']) == K_RANGE[-1] else ''}")

    result = pd.DataFrame(rows)
    result.to_csv(DATA / "bus_threshold_covariance_bic_grid.csv", index=False)

    lines = [
        "# Does raising the activity threshold also fix K-selection instability?",
        "",
        "For each activity threshold, BIC-best K is found independently for full and",
        "diag covariance (same fit() settings as the adopted pipeline). threshold=0 is",
        "the current adopted baseline (MIN_TOTAL=1, all 4,100 LSOAs).",
        "",
        result.to_markdown(index=False),
        "",
        "## Reading",
        "",
        "- If diag's best_K stops being at the range ceiling (12) once the threshold is",
        "  raised, and full's best_K stays in a similar, low, stable range across",
        "  thresholds, thresholding is close to sufficient on its own -- pick a threshold",
        "  from the data-retention curve and proceed with a normal re-cluster + relabel.",
        "- If diag keeps hitting the ceiling even at threshold=500 (43% of LSOAs excluded),",
        "  the K-selection instability is not primarily about low-activity noise -- it is a",
        "  property of the feature representation itself, and thresholding alone will not",
        "  fully resolve it (Codex's coverage-tier design, or a change to the feature",
        "  construction itself, would still be needed).",
    ]
    (REPORT / "THRESHOLD_COVARIANCE_GRID.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
