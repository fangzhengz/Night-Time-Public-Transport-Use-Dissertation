# -*- coding: utf-8 -*-
"""Compare the distinct K=4 solutions the seed battery found.

The battery showed that at the adopted budget (n_init=20) two of five seeds miss
the reported K=4 optimum, and that at n_init=100 one seed reaches a *better*
likelihood than the adopted labels. This script characterises those solutions so
the choice between keeping and refitting the adopted labels can be made on what
actually differs, not on BIC alone.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]
SRC = FYP / "rq1_bus_stoparea_clustering"
OUT = ROOT / "outputs"

FEATURES = SRC / "outputs" / "features" / "X_bus_stoparea_clr_min36.parquet"
METRICS = SRC / "outputs" / "features" / "sample_metrics.csv"
ADOPTED = SRC / "outputs" / "clr" / "labels" / "k4_labels.csv"

PROFILE_COLUMNS = [
    "log_total_activity",
    "direction_balance",
    "post_midnight_share",
    "post_midnight_persistence",
    "weekend_ratio",
]

CANDIDATES = [
    ("adopted (n_init=20, seed 42)", 42, 20),
    ("n_init=20, seed 7", 7, 20),
    ("n_init=20, seed 123", 123, 20),
    ("n_init=100, seed 7", 7, 100),
    ("n_init=100, seed 123", 123, 100),
]


def main() -> None:
    X_frame = pd.read_parquet(FEATURES)
    X_frame.index = pd.Index(X_frame.index.astype(str), name="lsoa")
    X = X_frame.to_numpy(dtype=float)
    metrics = pd.read_csv(METRICS, dtype={"lsoa": str}).set_index("lsoa").loc[X_frame.index]
    adopted = (
        pd.read_csv(ADOPTED, dtype={"lsoa": str})
        .set_index("lsoa")
        .loc[X_frame.index, "cluster"]
        .to_numpy(dtype=int)
    )

    rows: list[dict] = []
    profiles: list[pd.DataFrame] = []
    for label, seed, n_init in CANDIDATES:
        model = GaussianMixture(
            n_components=4,
            covariance_type="full",
            n_init=n_init,
            reg_covar=1e-6,
            max_iter=300,
            random_state=seed,
        ).fit(X)
        labels = model.predict(X).astype(int)
        sizes = np.bincount(labels, minlength=4)
        rows.append(
            {
                "solution": label,
                "BIC": float(model.bic(X)),
                "ari_vs_adopted": float(adjusted_rand_score(adopted, labels)),
                "sizes": ", ".join(str(int(s)) for s in sorted(sizes, reverse=True)),
                "min_cluster_n": int(sizes.min()),
            }
        )
        print(f"{label:32s} BIC={rows[-1]['BIC']:12.1f} ARI_vs_adopted={rows[-1]['ari_vs_adopted']:.3f}")

        frame = metrics[PROFILE_COLUMNS].copy()
        frame["cluster"] = labels
        summary = frame.groupby("cluster").mean().round(4)
        summary.insert(0, "n", np.bincount(labels, minlength=4))
        summary.insert(0, "solution", label)
        profiles.append(summary.reset_index())

    comparison = pd.DataFrame(rows)
    comparison.to_csv(OUT / "k4_solution_comparison.csv", index=False)
    profile = pd.concat(profiles, ignore_index=True)
    profile.to_csv(OUT / "k4_solution_profiles.csv", index=False)

    print("\n" + comparison.to_string(index=False))
    print("\nPer-cluster profiles")
    print(profile.to_string(index=False))


if __name__ == "__main__":
    main()
