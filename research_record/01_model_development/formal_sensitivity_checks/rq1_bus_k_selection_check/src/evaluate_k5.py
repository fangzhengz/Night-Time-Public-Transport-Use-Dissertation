# -*- coding: utf-8 -*-
"""Does the current bus CLR model support K=5?

The seed battery showed K=5 is the most seed-reproducible K after K=3, which
raises the question directly. This script fits K=5 at the higher restart budget
and asks what the fifth component actually is: which K=4 cluster it comes out
of, whether it is temporally or spatially distinct, and whether it survives
resampling.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, silhouette_samples
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = HERE.parents[2]
SRC = FYP / "rq1_bus_stoparea_clustering"
sys.path.insert(0, str(SRC / "src"))
import config as C  # noqa: E402
import map_style  # noqa: E402

OUT = ROOT / "outputs"
FIGURES = OUT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

K = 5
SEED = 42
N_INIT = 100
BOOTSTRAP_N = 40
BOOTSTRAP_N_INIT = 3

PROFILE_COLUMNS = [
    "log_total_activity",
    "total_activity",
    "direction_balance",
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
    "weekend_ratio",
]
CENTRE_LON, CENTRE_LAT = -0.1281, 51.5074
BNG = 27700


def matched_jaccard(base: np.ndarray, other: np.ndarray, k: int) -> np.ndarray:
    from scipy.optimize import linear_sum_assignment

    contingency = np.zeros((k, k), dtype=int)
    for left, right in zip(base, other):
        contingency[int(left), int(right)] += 1
    base_sizes = contingency.sum(axis=1, keepdims=True)
    other_sizes = contingency.sum(axis=0, keepdims=True)
    union = base_sizes + other_sizes - contingency
    scores = np.divide(
        contingency, union, out=np.zeros_like(contingency, dtype=float), where=union > 0
    )
    rows, columns = linear_sum_assignment(-scores)
    matched = np.zeros(k, dtype=float)
    matched[rows] = scores[rows, columns]
    return matched


def main() -> None:
    X_frame = pd.read_parquet(SRC / "outputs" / "features" / "X_bus_stoparea_clr_min36.parquet")
    X_frame.index = pd.Index(X_frame.index.astype(str), name="lsoa")
    X = X_frame.to_numpy(dtype=float)
    units = X_frame.index

    all_metrics = pd.read_csv(
        SRC / "outputs" / "features" / "sample_metrics.csv", dtype={"lsoa": str}
    ).set_index("lsoa")
    metrics = all_metrics.loc[units]

    adopted = (
        pd.read_csv(SRC / "outputs" / "clr" / "labels" / "k4_labels.csv", dtype={"lsoa": str})
        .set_index("lsoa")
        .loc[units, "cluster"]
        .to_numpy(dtype=int)
    )

    print(f"Fitting K={K}, full covariance, n_init={N_INIT}, seed={SEED} ...")
    model = GaussianMixture(
        n_components=K,
        covariance_type="full",
        n_init=N_INIT,
        reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER,
        random_state=SEED,
    ).fit(X)
    labels = model.predict(X).astype(int)
    sizes = np.bincount(labels, minlength=K)
    print(f"BIC={model.bic(X):,.1f}; sizes={sizes.tolist()}; ARI vs adopted K=4={adjusted_rand_score(adopted, labels):.3f}")

    pd.DataFrame({"lsoa": units, "cluster": labels}).to_csv(OUT / "k5_labels.csv", index=False)

    # --- what does the fifth component come out of? -------------------------
    crosstab = pd.crosstab(
        pd.Series(adopted, name="adopted_k4"), pd.Series(labels, name="k5")
    )
    crosstab.to_csv(OUT / "k5_vs_adopted_k4_crosstab.csv")
    print("\nCrosstab (rows adopted K=4, columns K=5)")
    print(crosstab.to_string())

    # --- continuous profile + silhouette per cluster ------------------------
    silhouettes = silhouette_samples(X, labels)
    frame = metrics[PROFILE_COLUMNS].copy()
    frame["cluster"] = labels
    profile = frame.groupby("cluster").mean().round(4)
    profile.insert(0, "n", sizes)
    profile["mean_silhouette"] = [
        float(silhouettes[labels == cluster].mean()) for cluster in range(K)
    ]
    profile.to_csv(OUT / "k5_metric_profile.csv")
    print("\nK=5 continuous profile")
    print(profile.to_string())

    # --- bootstrap stability of each cluster --------------------------------
    print(f"\nBootstrap x{BOOTSTRAP_N} ...")
    rng = np.random.default_rng(C.SEED)
    per_cluster: list[np.ndarray] = []
    aris: list[float] = []
    for _ in range(BOOTSTRAP_N):
        sample = rng.choice(len(X), size=len(X), replace=True)
        seed = int(rng.integers(1, 2**31 - 1))
        boot = GaussianMixture(
            n_components=K,
            covariance_type="full",
            n_init=BOOTSTRAP_N_INIT,
            reg_covar=C.REG_COVAR,
            max_iter=C.MAX_ITER,
            random_state=seed,
        ).fit(X[sample])
        other = boot.predict(X)
        per_cluster.append(matched_jaccard(labels, other, K))
        aris.append(float(adjusted_rand_score(labels, other)))
    per_cluster_array = np.vstack(per_cluster)
    stability = pd.DataFrame(
        {
            "cluster": range(K),
            "n": sizes,
            "bootstrap_jaccard_mean": per_cluster_array.mean(axis=0).round(4),
            "bootstrap_jaccard_min": per_cluster_array.min(axis=0).round(4),
        }
    )
    stability.to_csv(OUT / "k5_bootstrap_by_cluster.csv", index=False)
    print(f"Bootstrap ARI mean={np.mean(aris):.3f}")
    print(stability.to_string(index=False))

    # --- centrality ----------------------------------------------------------
    import geopandas as gpd

    boundaries = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(columns={code_column: "lsoa"})
    boundaries = boundaries.to_crs(BNG)
    centre = gpd.GeoSeries.from_xy([CENTRE_LON], [CENTRE_LAT], crs=4326).to_crs(BNG).iloc[0]
    boundaries["km"] = boundaries.geometry.centroid.distance(centre) / 1000.0
    km = boundaries.set_index("lsoa")["km"].reindex(units)
    centrality = (
        pd.DataFrame({"cluster": labels, "km": km.to_numpy()})
        .dropna()
        .groupby("cluster")["km"]
        .agg(["count", "mean", "median"])
        .round(3)
    )
    centrality.to_csv(OUT / "k5_centrality.csv")
    print("\nK=5 distance from Charing Cross (km)")
    print(centrality.to_string())

    # --- figures -------------------------------------------------------------
    raw_share = pd.read_parquet(
        SRC / "outputs" / "features" / "X_bus_stoparea_raw_share_min36.parquet"
    )
    raw_share.index = pd.Index(raw_share.index.astype(str), name="lsoa")
    raw_share = raw_share.loc[units]

    fig, axes = plt.subplots(K, 3, figsize=(13, 2.15 * K), sharex=True, sharey=True)
    axes = np.atleast_2d(axes)
    for cluster in range(K):
        means = raw_share.loc[labels == cluster].mean(axis=0)
        for day_index, day_type in enumerate(C.DAY_TYPES):
            ax = axes[cluster, day_index]
            for direction, colour in [("boardings", "#0072B2"), ("alightings", "#D55E00")]:
                values = [means[f"{direction}_{day_type}_{hour}"] for hour in C.HOURS]
                ax.plot(range(12), values, marker="o", markersize=2, color=colour, label=direction)
            if cluster == 0:
                ax.set_title(day_type)
            if day_index == 0:
                ax.set_ylabel(
                    f"C{cluster}\nn={int(sizes[cluster]):,} ({sizes[cluster] / sizes.sum() * 100:.1f}%)",
                    color=map_style.cluster_colour(cluster),
                    fontweight="bold",
                    fontsize=9,
                )
            ax.grid(alpha=0.2)
    axes[-1, 1].set_xticks(
        range(12),
        ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"],
        rotation=45,
    )
    axes[0, -1].legend(loc="upper right", fontsize=8)
    fig.suptitle(
        f"Bus StopArea CLR K=5 (n_init={N_INIT}, seed {SEED}, BIC {model.bic(X):,.0f})\n"
        "raw full-week share",
        y=1.01,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "k5_profiles.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    boundaries_wgs = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries_wgs if column.lower() == "lsoa21cd")
    boundaries_wgs = boundaries_wgs[[code_column, "geometry"]].rename(
        columns={code_column: "lsoa"}
    )
    mapped = map_style.build_status_frame(
        boundaries_wgs, units, labels, pd.Index(all_metrics.index.astype(str))
    )
    fig, ax = plt.subplots(figsize=(10, 10))
    map_style.draw_cluster_map(ax, mapped, K)
    ax.set_title(f"Bus StopArea CLR K=5 (n_init={N_INIT}, seed {SEED})", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES / "k5_map.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"\nFigures -> {FIGURES}")


if __name__ == "__main__":
    main()
