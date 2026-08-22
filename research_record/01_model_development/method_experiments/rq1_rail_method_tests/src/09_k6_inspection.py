# -*- coding: utf-8 -*-
"""Inspect K=6 on the adopted (padded) rail matrix before ruling it out.

K=6 attains a better BIC than the adopted K=5 once the optimisation budget is
equalised across K (-1,904,055 vs -1,903,892 over 5 seeds x n_init=200). The
margin is 0.009% of the criterion and K=5 is far more seed-reproducible, but
that is an argument to see K=6's structure rather than to dismiss it unseen.

Two things this script establishes that the raw BIC number cannot:
  1. whether K=6's best-BIC solution is itself reproducible, or a lucky basin
     only one seed reaches
  2. what K=6 actually splits -- a substantively new type, or one adopted
     cluster cut in two

Read-only. Emits no labels for downstream use.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

warnings.filterwarnings("ignore", category=ConvergenceWarning)

ADOPTED_X = C.CANONICAL / "outputs" / "data" / "X_rail_allmodes.parquet"
ADOPTED_LABELS = C.CANONICAL / "outputs" / "data" / "rail_allmodes_k5_labels.csv"
SEEDS = [42, 7, 123, 2026, 999, 55, 808, 1234]
N_INIT = 200
OUT = C.OUT / "k6_inspection"
OUT.mkdir(parents=True, exist_ok=True)
GREEN, RED = "#2F6B4F", "#9A3D3D"


def fit(X, k, seed):
    return GaussianMixture(
        k, covariance_type=C.PRIMARY_COVARIANCE, n_init=N_INIT,
        reg_covar=C.REG_COVAR, max_iter=C.MAX_ITER, random_state=seed,
    ).fit(X)


def main() -> None:
    import geopandas as gpd

    X_frame = pd.read_parquet(ADOPTED_X)
    X_frame.index = X_frame.index.astype(str)
    X = X_frame.to_numpy(dtype=float)
    adopted = pd.read_csv(ADOPTED_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    metrics = pd.read_csv(C.RAIL_UNIT_METRICS, dtype={"NLC": str}).set_index("NLC")
    coords = pd.read_csv(
        C.FYP / "data_processing" / "rail_allmodes" / "outputs" / "data"
        / "rail_allmodes_coords.csv", dtype={"unit": str},
    ).set_index("unit")

    # 1. Which basin does each seed reach, and how often is it the best one?
    runs = []
    for seed in SEEDS:
        model = fit(X, 6, seed)
        runs.append(
            {"seed": seed, "bic": float(model.bic(X)),
             "labels": pd.Series(model.predict(X), index=X_frame.index)}
        )
    best = min(runs, key=lambda r: r["bic"])
    for run in runs:
        run["ari_to_best"] = adjusted_rand_score(best["labels"], run["labels"])
    table = pd.DataFrame(
        [{"seed": r["seed"], "BIC": r["bic"], "ARI_to_best": r["ari_to_best"],
          "sizes": sorted(np.bincount(r["labels"], minlength=6).tolist())} for r in runs]
    ).sort_values("BIC")
    table.to_csv(OUT / "k6_seed_basins.csv", index=False)
    reached = int((table["ARI_to_best"] > 0.99).sum())
    print(f"K=6 best BIC {best['bic']:.1f} at seed {best['seed']}; "
          f"{reached}/{len(SEEDS)} seeds reach that basin (ARI>0.99)")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    labels = best["labels"]

    # 2. What does it split? Align K=6 onto K=5's numbering where possible.
    shared = X_frame.index.intersection(adopted.index)
    contingency = pd.crosstab(adopted.loc[shared], labels.loc[shared])
    contingency.to_csv(OUT / "k5_vs_k6_contingency.csv")
    print("\nadopted K=5 (rows) x K=6 (cols):")
    print(contingency.to_string())

    rows = []
    for cluster in sorted(labels.unique()):
        members = labels.index[labels == cluster]
        parents = adopted.reindex(members).value_counts()
        rows.append(
            {
                "k6_cluster": int(cluster), "n": len(members),
                "dir_balance": metrics["direction_balance"].reindex(members).mean(),
                "nt_extension": metrics["night_tube_extension_share"].reindex(members).mean(),
                "weekend": metrics["weekend_common_ratio"].reindex(members).mean(),
                "median_activity": metrics["total_activity"].reindex(members).median(),
                "pct_LU": 100 * coords["is_lu"].reindex(members).mean(),
                "mainly_from_k5": f"C{int(parents.index[0])} ({parents.iloc[0]}/{len(members)})",
                "top_stations": ", ".join(
                    str(coords["Station"].get(u, u))
                    for u in sorted(members, key=lambda u: -metrics["total_activity"].get(u, 0))[:4]
                ),
            }
        )
    profile = pd.DataFrame(rows).sort_values("n", ascending=False)
    profile.to_csv(OUT / "k6_cluster_profile.csv", index=False)
    print("\nK=6 cluster profile:")
    print(profile.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))

    # 3. Map
    base = gpd.read_file(C.FYP / "map" / "London_LSOA_2021_Boundaries.geojson").to_crs("EPSG:27700")
    frame = coords.loc[coords.index.intersection(X_frame.index),
                       ["Station", "is_lu", "easting", "northing"]].copy()
    frame["k6"] = labels.reindex(frame.index)
    frame["k5"] = adopted.reindex(frame.index)
    frame = frame.dropna(subset=["easting", "k6", "k5"])
    palette = matplotlib.colormaps["tab10"].resampled(6)

    fig, axes = plt.subplots(1, 2, figsize=(17, 8.6))
    for ax, column, k, title in [
        (axes[0], "k5", 5, "ADOPTED K=5 (seed-ARI 0.798)"),
        (axes[1], "k6", 6, f"K=6 at best BIC (seed {best['seed']}, seed-ARI 0.674)"),
    ]:
        base.plot(ax=ax, color="#f4f4f4", edgecolor="#dcdcdc", linewidth=0.2)
        for value in sorted(frame[column].unique()):
            subset = frame[frame[column] == value]
            lu = subset[subset["is_lu"]]
            other = subset[~subset["is_lu"]]
            ax.scatter(lu.easting, lu.northing, s=34, marker="o", color=palette(int(value)),
                       edgecolor="white", linewidth=0.5,
                       label=f"C{int(value)} (n={len(subset)})", zorder=3)
            if len(other):
                ax.scatter(other.easting, other.northing, s=42, marker="^",
                           color=palette(int(value)), edgecolor="black",
                           linewidth=0.4, zorder=4)
        ax.set_title(title, fontsize=11)
        ax.set_axis_off()
        ax.legend(loc="lower right", fontsize=7.5)
        ax.set_xlim(frame.easting.min() - 3000, frame.easting.max() + 3000)
        ax.set_ylim(frame.northing.min() - 3000, frame.northing.max() + 3000)
    fig.suptitle(
        f"Rail, padded 18:00-05:00 matrix: adopted K=5 versus K=6\n"
        f"K=6 BIC {best['bic']:,.0f} vs K=5 -1,903,892 (0.009% better) - "
        f"K=6 basin reached by {reached}/{len(SEEDS)} seeds",
        fontsize=12, y=1.0,
    )
    fig.tight_layout()
    fig.savefig(OUT / "k5_vs_k6_map.png", dpi=190, bbox_inches="tight")
    plt.close(fig)

    # 4. Profiles, in the same house style as 04_figures
    colmap = pd.DataFrame(
        [{"col": c, "direction": c.rsplit("_", 2)[0], "day": c.rsplit("_", 2)[1],
          "minute": int(c.rsplit("_", 2)[2])} for c in X_frame.columns]
    )
    clusters = sorted(labels.unique())
    fig, axes = plt.subplots(len(clusters), 1, figsize=(11.5, 2.0 * len(clusters)),
                             squeeze=False, sharey=True)
    reference = colmap[colmap.direction == C.RAIL_DIRECTIONS[0]].reset_index(drop=True)
    ticks, tick_labels, boundaries = [], [], []
    for day in C.RAIL_DAYS:
        index = reference.index[reference.day == day]
        ticks.append(int(np.mean(index)))
        tick_labels.append(f"{day}\n18:00-04:45")
        boundaries.append(int(index[-1]) + 0.5)
    for axis, cluster in zip(axes[:, 0], clusters):
        mask = (labels == cluster).to_numpy()
        for direction, colour in zip(C.RAIL_DIRECTIONS, [GREEN, RED]):
            selection = colmap[colmap.direction == direction].reset_index(drop=True)
            sub = X_frame.loc[mask, selection.col.tolist()]
            axis.plot(np.arange(len(selection)), sub.median(0).values, color=colour,
                      lw=1.2, marker="o", ms=1.6, label=direction)
            axis.fill_between(np.arange(len(selection)), sub.quantile(0.1).values,
                              sub.quantile(0.9).values, color=colour, alpha=0.12, lw=0)
        for boundary in boundaries[:-1]:
            axis.axvline(boundary, color="#bbb", lw=0.7, ls="--")
        axis.set_title(f"C{cluster} (n={int(mask.sum())})", fontsize=9)
        axis.grid(axis="y", color="#eee", lw=0.5)
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_xticks(ticks); axis.set_xticklabels(tick_labels, fontsize=7)
    axes[0, 0].legend(fontsize=8, loc="upper right")
    fig.suptitle("Rail K=6 at best BIC — cluster profiles (full-week closure, padded window)",
                 y=1.0, fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "k6_profiles.png", dpi=175, bbox_inches="tight")
    plt.close(fig)

    (OUT / "summary.json").write_text(
        json.dumps({"best_bic": best["bic"], "best_seed": best["seed"],
                    "seeds_reaching_best_basin": reached, "n_seeds": len(SEEDS),
                    "ari_vs_adopted_k5": adjusted_rand_score(adopted.loc[shared], labels.loc[shared]),
                    "sizes": sorted(np.bincount(labels, minlength=6).tolist())},
                   indent=2), encoding="utf-8")
    print("\nSaved to", OUT)


if __name__ == "__main__":
    main()
