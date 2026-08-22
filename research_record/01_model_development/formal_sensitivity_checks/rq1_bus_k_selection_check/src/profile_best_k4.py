# -*- coding: utf-8 -*-
"""Spatial and temporal characterisation of the best-likelihood K=4 solution.

The seed battery found that the adopted bus labels (n_init=20, seed 42,
BIC -399,343) are beaten by an n_init=100, seed 7 fit (BIC -401,814). This
script characterises that better solution the same way the adopted one was
characterised, so the two can be compared on what actually differs rather than
on BIC: temporal profiles, spatial map, continuous-metric profile, borough
geography, and a membership crosstab against the adopted labels.

Cluster ids are relabelled to the adopted solution's ids by Hungarian matching
on the confusion matrix, so "C1" means the same group in both. Writes only into
this folder.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
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

BEST_SEED = 7
BEST_N_INIT = 100
K = 4

PROFILE_COLUMNS = [
    "log_total_activity",
    "total_activity",
    "direction_balance",
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
    "weekend_ratio",
]


def align_to_adopted(new: np.ndarray, adopted: np.ndarray, k: int) -> np.ndarray:
    """Relabel `new` so cluster ids line up with `adopted` by maximum overlap."""
    confusion = np.zeros((k, k), dtype=int)
    for a, b in zip(adopted, new):
        confusion[int(a), int(b)] += 1
    rows, columns = linear_sum_assignment(-confusion)
    mapping = {int(column): int(row) for row, column in zip(rows, columns)}
    return np.array([mapping[int(label)] for label in new], dtype=int)


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

    print(f"Fitting K={K}, full covariance, n_init={BEST_N_INIT}, seed={BEST_SEED} ...")
    model = GaussianMixture(
        n_components=K,
        covariance_type="full",
        n_init=BEST_N_INIT,
        reg_covar=C.REG_COVAR,
        max_iter=C.MAX_ITER,
        random_state=BEST_SEED,
    ).fit(X)
    raw_labels = model.predict(X).astype(int)
    labels = align_to_adopted(raw_labels, adopted, K)
    print(f"BIC={model.bic(X):.1f}; sizes after alignment={np.bincount(labels, minlength=K).tolist()}")

    pd.DataFrame({"lsoa": units, "cluster": labels}).to_csv(
        OUT / "best_k4_labels.csv", index=False
    )

    # --- continuous-metric profile -----------------------------------------
    frame = metrics[PROFILE_COLUMNS].copy()
    frame["cluster"] = labels
    profile = frame.groupby("cluster").agg(["mean", "median"]).round(4)
    profile.columns = [f"{column}_{statistic}" for column, statistic in profile.columns]
    profile.insert(0, "n", np.bincount(labels, minlength=K))
    profile.to_csv(OUT / "best_k4_metric_profile.csv")
    print("\nContinuous-metric profile (means)")
    print(frame.groupby("cluster").mean().round(4).to_string())

    # --- membership crosstab vs adopted ------------------------------------
    crosstab = pd.crosstab(
        pd.Series(adopted, name="adopted"), pd.Series(labels, name="best_likelihood")
    )
    crosstab.to_csv(OUT / "best_k4_vs_adopted_crosstab.csv")
    print("\nMembership crosstab (rows adopted, columns best-likelihood)")
    print(crosstab.to_string())

    # --- temporal profiles --------------------------------------------------
    raw_share = pd.read_parquet(
        SRC / "outputs" / "features" / "X_bus_stoparea_raw_share_min36.parquet"
    )
    raw_share.index = pd.Index(raw_share.index.astype(str), name="lsoa")
    raw_share = raw_share.loc[units]

    sizes = np.bincount(labels, minlength=K)
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
                share = sizes[cluster] / sizes.sum() * 100
                ax.set_ylabel(
                    f"C{cluster}\nn={int(sizes[cluster]):,} ({share:.1f}%)",
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
        f"Best-likelihood K=4 (n_init={BEST_N_INIT}, seed {BEST_SEED}, BIC {model.bic(X):,.0f})\n"
        "cluster ids aligned to the adopted solution; raw full-week share",
        y=1.01,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "best_k4_profiles.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # --- side-by-side maps --------------------------------------------------
    import geopandas as gpd

    boundaries = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(columns={code_column: "lsoa"})
    all_units = pd.Index(all_metrics.index.astype(str))

    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    for ax, (title, these) in zip(
        axes,
        [
            ("Adopted (n_init=20, seed 42)\nBIC -399,343", adopted),
            (f"Best likelihood (n_init={BEST_N_INIT}, seed {BEST_SEED})\nBIC {model.bic(X):,.0f}", labels),
        ],
    ):
        mapped = map_style.build_status_frame(boundaries, units, these, all_units)
        map_style.draw_cluster_map(ax, mapped, K, legend_fontsize=7)
        ax.set_title(title, fontsize=11)
    fig.suptitle("Bus StopArea CLR K=4: adopted versus best-likelihood solution", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES / "best_k4_map_comparison.png", dpi=170, bbox_inches="tight")
    plt.close(fig)

    # --- borough geography ---------------------------------------------------
    if C.LSOA_LAD_LOOKUP.exists():
        lookup = pd.read_csv(C.LSOA_LAD_LOOKUP, usecols=["LSOA21CD", "LAD22CD"])
        lookup["LSOA21CD"] = lookup["LSOA21CD"].astype(str)
        lookup["borough"] = lookup["LAD22CD"].map(C.TARGET_LADS)
        rows: list[dict] = []
        for name, these in [("adopted", adopted), ("best_likelihood", labels)]:
            target = pd.DataFrame({"LSOA21CD": units, "cluster": these}).merge(
                lookup[["LSOA21CD", "borough"]], on="LSOA21CD", how="left"
            )
            target = target[target["borough"].notna()]
            target = target.assign(
                area_group=np.where(
                    target["borough"].isin(["Westminster", "Camden"]), "central", "outer"
                )
            )
            distributions = {}
            for group in ["central", "outer"]:
                counts = target.loc[target["area_group"] == group, "cluster"].value_counts()
                values = np.array([counts.get(c, 0) for c in range(K)], dtype=float)
                distributions[group] = values / values.sum() if values.sum() else values
            central, outer = distributions["central"], distributions["outer"]
            row = {
                "solution": name,
                "central_outer_total_variation": 0.5 * float(np.abs(central - outer).sum()),
                "central_outer_same_cluster_probability": float(np.dot(central, outer)),
            }
            for cluster in range(K):
                row[f"central_share_C{cluster}"] = float(central[cluster])
                row[f"outer_share_C{cluster}"] = float(outer[cluster])
            rows.append(row)
        geography = pd.DataFrame(rows)
        geography.to_csv(OUT / "best_k4_geography.csv", index=False)
        print("\nCentral-versus-outer diagnostic")
        print(geography.to_string(index=False))

    print(f"\nFigures -> {FIGURES}")


if __name__ == "__main__":
    main()
