# -*- coding: utf-8 -*-
"""08 - K-selection evidence panel for the adopted (padded, 440-dim) rail matrix.

STATUS: this is the OFFICIAL K-selection source. `rail_allmodes_k_selection_panel.csv`
and this script's own figure are what the dissertation's main-text K-selection
figure and any cited random-seed ARI / bootstrap ARI / weakest-cluster Jaccard
number must come from. `07_stability_allmodes.py` (STABILITY_K5_K6/K7_ALLMODES*)
is a separate, secondary validation battery -- it reports agreement WITH the
saved/adopted labels rather than agreement AMONG same-budget seeds/resamples,
so its similarly-named columns are not interchangeable with the ones here.

Produces the full K=2..12 diagnostic set on one page so the choice of K can be
made against all of it at once rather than one criterion at a time.

TWO THINGS THIS DOES DIFFERENTLY FROM A STANDARD K SWEEP
--------------------------------------------------------
1. **BIC is computed at an equalised search budget.** A grid that fits every K
   at the same `n_init` systematically under-optimises higher K: a K-component
   mixture carries K x (2d+1) parameters, so it needs more restarts to reach
   its own optimum. On this matrix that bias is large enough to invert the
   ranking - at n_init=20 K=5 appeared to beat K=6 by 745, and at
   5 seeds x n_init=200 K=6 in fact attains the better BIC. Every K here gets
   the same SEEDS x N_INIT budget and the best BIC found is reported, so the
   curve shows what BIC actually says rather than an artefact of the sweep.

2. **A survival panel for the night-persistent cluster.** The 26-station
   night-persistent group is this study's headline structure, so "does this K
   keep it intact" is a decision criterion, not a curiosity. Reported as the
   Jaccard between that group and whichever cluster best hosts it, averaged
   over seeds. A K that scores well on every generic index while fragmenting
   the group is not a usable K for this dissertation.

Read-only with respect to labels: writes figures and a table, no cluster
assignments.
"""
from __future__ import annotations

import sys
import warnings
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

warnings.filterwarnings("ignore", category=ConvergenceWarning)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs" / "data"
FIG = ROOT / "outputs" / "figures"
X_PATH = DATA / "X_rail_allmodes.parquet"
ADOPTED_LABELS = DATA / "rail_allmodes_k5_labels.csv"

K_RANGE = list(range(2, 13))
SEEDS = [42, 7, 123, 2026, 999]
N_INIT = 200
BOOTSTRAP = 50
BOOTSTRAP_N_INIT = 3
COV = "diag"
REG_COVAR = 1e-6
MAX_ITER = 300
ADOPTED_K = 5
PURPLE, GREEN, RED, GREY = "#500778", "#2F6B4F", "#9A3D3D", "#9A9A9A"


def fit(X, k, seed, n_init=N_INIT):
    return GaussianMixture(
        k, covariance_type=COV, n_init=n_init, reg_covar=REG_COVAR,
        max_iter=MAX_ITER, random_state=seed,
    ).fit(X)


def matched_min_jaccard(base, other, k):
    contingency = np.zeros((k, k), dtype=int)
    for left, right in zip(base, other):
        contingency[int(left), int(right)] += 1
    union = (contingency.sum(1, keepdims=True) + contingency.sum(0, keepdims=True)
             - contingency)
    scores = np.divide(contingency, union, out=np.zeros_like(contingency, float),
                       where=union > 0)
    rows, cols = linear_sum_assignment(-scores)
    return float(scores[rows, cols].min())


def main() -> None:
    X_frame = pd.read_parquet(X_PATH)
    X_frame.index = X_frame.index.astype(str)
    X = X_frame.to_numpy(dtype=float)
    adopted = pd.read_csv(ADOPTED_LABELS, dtype={"unit": str}).set_index("unit")["cluster"]
    adopted = adopted.reindex(X_frame.index)
    if adopted.isna().any():
        raise ValueError("Adopted K=5 labels do not cover the current feature matrix")

    # Identify the night-persistent cluster directly from the current feature
    # matrix. This keeps K selection independent of downstream RQ2 metrics,
    # which may legitimately be stale immediately after a clustering refit.
    post_0100_cols = [c for c in X_frame.columns if int(c.rsplit("_", 1)[1]) >= 1500]
    post_0100_share = X_frame[post_0100_cols].sum(axis=1) / X_frame.sum(axis=1)
    night_cluster = int(post_0100_share.groupby(adopted).mean().idxmax())
    night_group = set(adopted[adopted == night_cluster].index)
    print(f"night-persistent group: n={len(night_group)}")

    rows = []
    for k in K_RANGE:
        runs = []
        for seed in SEEDS:
            model = fit(X, k, seed)
            runs.append((float(model.bic(X)), seed, model.predict(X)))
        best_bic, best_seed, best_labels = min(runs, key=lambda r: r[0])

        # seed agreement across the equal-budget runs
        seed_aris = [adjusted_rand_score(a[2], b[2]) for a, b in combinations(runs, 2)]

        # how often does the best basin get found at all
        reached = sum(1 for r in runs if adjusted_rand_score(best_labels, r[2]) > 0.99)

        # night-group survival, averaged over the seed runs
        jaccards = []
        for _, _, labels in runs:
            series = pd.Series(labels, index=X_frame.index)
            host = series.reindex(list(night_group)).value_counts().index[0]
            hosted = set(series[series == host].index)
            jaccards.append(len(night_group & hosted) / len(night_group | hosted))

        rng = np.random.default_rng(42)
        boot_ari, boot_jac = [], []
        for _ in range(BOOTSTRAP):
            sample = rng.choice(len(X), size=len(X), replace=True)
            other = fit(X[sample], k, int(rng.integers(1, 2**31 - 1)),
                        n_init=BOOTSTRAP_N_INIT).predict(X)
            boot_ari.append(adjusted_rand_score(best_labels, other))
            boot_jac.append(matched_min_jaccard(best_labels, other, k))

        sizes = np.bincount(best_labels, minlength=k)
        rows.append({
            "K": k, "BIC": best_bic, "best_seed": best_seed,
            "silhouette": silhouette_score(X, best_labels),
            "calinski_harabasz": calinski_harabasz_score(X, best_labels),
            "davies_bouldin": davies_bouldin_score(X, best_labels),
            "seed_ari_mean": float(np.mean(seed_aris)),
            "seeds_reaching_best_basin": reached, "n_seeds": len(SEEDS),
            "bootstrap_ari_mean": float(np.mean(boot_ari)),
            "bootstrap_min_jaccard_mean": float(np.mean(boot_jac)),
            "min_cluster_n": int(sizes.min()),
            "night_group_jaccard_mean": float(np.mean(jaccards)),
        })
        print(f"  K={k}: BIC={best_bic:.1f} sil={rows[-1]['silhouette']:.3f} "
              f"seedARI={rows[-1]['seed_ari_mean']:.3f} "
              f"basin={reached}/{len(SEEDS)} "
              f"nightJ={rows[-1]['night_group_jaccard_mean']:.3f} "
              f"minN={sizes.min()}")

    table = pd.DataFrame(rows)
    table.to_csv(DATA / "rail_allmodes_k_selection_panel.csv", index=False)

    panels = [
        ("BIC", "BIC (lower = better)\nbest of 5 seeds x n_init=200", PURPLE, False),
        ("silhouette", "Silhouette (higher = better)", GREEN, False),
        ("calinski_harabasz", "Calinski-Harabasz (higher = better)", GREEN, False),
        ("davies_bouldin", "Davies-Bouldin (lower = better)", RED, False),
        ("seed_ari_mean", "Random-seed agreement\nmean pairwise ARI", PURPLE, True),
        ("bootstrap_ari_mean", f"Bootstrap ARI ({BOOTSTRAP} replicates)", PURPLE, True),
        ("bootstrap_min_jaccard_mean", "Weakest cluster reproducibility\nmean min matched Jaccard", RED, True),
        ("night_group_jaccard_mean", f"NIGHT-PERSISTENT GROUP survival\nJaccard with best host cluster (n={len(night_group)})", GREEN, True),
        ("min_cluster_n", "Smallest cluster size", GREY, False),
    ]
    fig, axes = plt.subplots(3, 3, figsize=(15.5, 11.5))
    for ax, (column, title, colour, unit_axis) in zip(axes.flat, panels):
        ax.plot(table["K"], table[column], marker="o", ms=5, lw=1.6, color=colour)
        ax.axvline(ADOPTED_K, color="#cc0000", lw=1.1, ls="--", alpha=0.65)
        value = table.loc[table["K"] == ADOPTED_K, column].iloc[0]
        ax.scatter([ADOPTED_K], [value], s=110, facecolor="none",
                   edgecolor="#cc0000", linewidth=1.8, zorder=5)
        ax.set_title(title, fontsize=9.5)
        ax.set_xlabel("K")
        ax.set_xticks(K_RANGE)
        ax.grid(color="#eee")
        ax.spines[["top", "right"]].set_visible(False)
        if unit_axis:
            ax.set_ylim(0, 1.02)
    fig.suptitle(
        f"Rail all-modes ({len(X_frame)} stations, padded 18:00-05:00, {X_frame.shape[1]} features) — K selection evidence, K=2..12\n"
        "red marker = adopted K=5.  BIC uses an EQUALISED budget across K "
        "(5 seeds x n_init=200), because a fixed n_init under-optimises higher K and biases BIC downward in K.",
        fontsize=11.5, y=1.0,
    )
    fig.tight_layout()
    fig.savefig(FIG / "rail_allmodes_k_selection_panel.png", dpi=185, bbox_inches="tight")
    fig.savefig(FIG / "rail_allmodes_k_selection_panel.pdf", bbox_inches="tight")
    plt.close(fig)

    print()
    print(table.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nSaved:", FIG / "rail_allmodes_k_selection_panel.png")


if __name__ == "__main__":
    main()
