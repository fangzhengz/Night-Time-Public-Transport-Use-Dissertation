#!/usr/bin/env python
"""07 - Internal stability VALIDATION for the all-modes rail clustering
(secondary robustness check, NOT the official K-selection source).

STATUS: this script and every number it writes (STABILITY_K5_K6_ALLMODES*,
STABILITY_K5_K7_ALLMODES*, and their per-K seed_ARI_mean / bootstrap_ARI_mean_200
/ weakest_cluster_jaccard columns) are a validation battery, not the
dissertation's official K-selection evidence. `08_k_selection_panel.py` /
`rail_allmodes_k_selection_panel.csv` is the official source for random-seed
ARI, bootstrap ARI and weakest-cluster Jaccard at the adopted K -- cite that
CSV in the main text, not this one. The two report DIFFERENT quantities under
similar English names:
  * this script's seed_ARI_mean is the mean ARI of each of 20 (n_init=100)
    full-data refits AGAINST THE ALREADY-SAVED/ADOPTED partition;
  * 08's seed_ari_mean is the mean PAIRWISE ARI among 5 (n_init=200) refits
    of that K, none of which is privileged as "the" adopted labelling.
Same distinction for bootstrap_ARI_mean_200 (vs adopted, 200 reps) versus 08's
bootstrap_ari_mean (vs its own best-of-5-seeds labels, 50 reps), and for
weakest_cluster_jaccard (min of per-cluster means, vs adopted) versus 08's
bootstrap_min_jaccard_mean (mean of per-replicate minimums, vs its own
labels). Found 2026-08-17 after a write-up draft cited this script's 0.859 /
0.480 / 0.399 next to a figure whose axis was actually 08's 0.964 / 0.510 /
0.301 -- see numbat_all_area_test/README.md's Interpretation boundary section
for the resolution. This script remains useful as a K=5-vs-adjacent-candidate
structural comparison (transition matrix, per-cluster silhouette); it is just
not the source for the headline stability numbers.

This is a parameterised adaptation of
`FYP/rail_k_selection_validation/src/run_rail_k_validation.py` (which
validated the canonical 270-station K=5 vs K=6 choice). That script hardcodes
K=5/K=6 throughout; here the same statistical methodology (deterministic
reference refit, cluster-level silhouette, K-transition structure, paired
bootstrap stability, full-data random-seed stability) is generalised to a
configurable (K_LOW, K_HIGH) pair and applied to the all-modes feature
matrix. Output filenames are derived from K_LOW/K_HIGH, so re-running with
a different pair does not overwrite a previous pair's results.

The comparison pair is configurable through RAIL_K_LOW / RAIL_K_HIGH and is
run on the current NaPTAN-matched input (see
`FYP/data_processing/rail_allmodes/` and
`outputs/archive_420station_allmodes/README.md`). K=5 is this refit's own
BIC winner in both the standard grid and the equal-budget panel; K=6 and
K=7 are adjacent candidates tested with the same rigorous bootstrap/seed
battery. Output filenames encode the selected pair, so the K=5-vs-K=6 and
K=5-vs-K=7 results do not overwrite one another.

Self-contained and read-only with respect to both the canonical clustering
pipeline and the other scripts in this folder; writes only beneath its own
configured output root.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow
import scipy
import sklearn
from scipy.optimize import linear_sum_assignment
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

# ---------------------------------------------------------------- config
K_LOW = int(os.environ.get("RAIL_K_LOW", "5"))
K_HIGH = int(os.environ.get("RAIL_K_HIGH", "7"))
BOOTSTRAP = 200
SEED_RUNS = 20
# 2026-08-01: reference and seed refits raised 20 -> 100 for the widened
# 440-dim matrix, which does not converge at 20 (see 03_cluster_allmodes.py).
# BOOTSTRAP_N_INIT stays at 3 deliberately: it is the protocol used for the
# archived native-window battery, so keeping it preserves comparability with
# those numbers. The consequence is that bootstrap ARI mixes sampling
# variability with optimisation noise and is therefore a CONSERVATIVE
# (pessimistic) stability estimate -- state that rather than reading it as a
# pure resampling result.
REFERENCE_N_INIT = 100
BOOTSTRAP_N_INIT = 3
SEED_N_INIT = 100
RANDOM_STATE = 42
REG_COVAR = 1e-6
MAX_ITER = 300
PROGRESS_EVERY = 10

SCRIPT_PATH = Path(__file__).resolve()
TEST_ROOT = SCRIPT_PATH.parents[1]
FYP_ROOT = TEST_ROOT.parents[0]
DATA_DIR = TEST_ROOT / "outputs" / "data"
FIGURES_DIR = TEST_ROOT / "outputs" / "figures"
REPORT_DIR = TEST_ROOT / "outputs" / "report"

FEATURES_PATH = DATA_DIR / "X_rail_allmodes.parquet"
LABELS_LOW_PATH = DATA_DIR / f"rail_allmodes_k{K_LOW}_labels.csv"
LABELS_HIGH_PATH = DATA_DIR / f"rail_allmodes_k{K_HIGH}_labels.csv"
ORIGINAL_KDIAG_PATH = DATA_DIR / "rail_allmodes_kdiag.csv"
# Coordinate matching now lives in data_processing/rail_allmodes/ (moved 2026-07-24).
COORDS_PATH = FYP_ROOT / "data_processing" / "rail_allmodes" / "outputs" / "data" / "rail_allmodes_coords.csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_gmm(k: int, seed: int, n_init: int) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type="diag",
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    )


def load_label(path: Path, k: int, index: pd.Index) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"unit", "cluster"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["unit"] = frame["unit"].astype(str)
    if frame["unit"].duplicated().any():
        raise ValueError(f"{path} contains duplicate unit IDs")
    frame = frame.set_index("unit").reindex(index)
    if frame["cluster"].isna().any():
        absent = frame.index[frame["cluster"].isna()].tolist()[:10]
        raise ValueError(f"{path} is missing feature units, e.g. {absent}")
    frame["cluster"] = frame["cluster"].astype(int)
    observed = sorted(frame["cluster"].unique().tolist())
    if observed != list(range(k)):
        raise ValueError(f"{path} labels are {observed}, expected 0..{k - 1}")
    return frame


def validate_inputs() -> tuple[pd.DataFrame, dict[int, np.ndarray], pd.DataFrame]:
    for path in [FEATURES_PATH, LABELS_LOW_PATH, LABELS_HIGH_PATH, ORIGINAL_KDIAG_PATH]:
        if not path.is_file():
            raise FileNotFoundError(path)

    features = pd.read_parquet(FEATURES_PATH)
    if features.empty:
        raise ValueError("Feature matrix is empty")
    features.index = features.index.astype(str)
    if features.index.duplicated().any():
        raise ValueError("Feature matrix contains duplicate unit IDs")
    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise ValueError("Feature matrix contains NaN or infinite values")

    labels = {
        K_LOW: load_label(LABELS_LOW_PATH, K_LOW, features.index)["cluster"].to_numpy(),
        K_HIGH: load_label(LABELS_HIGH_PATH, K_HIGH, features.index)["cluster"].to_numpy(),
    }

    if COORDS_PATH.is_file():
        coords = pd.read_csv(COORDS_PATH, encoding="utf-8-sig")
        coords["unit"] = coords["unit"].astype(str)
        keep = [c for c in ["unit", "Station", "mode_label", "lon", "lat"] if c in coords]
        coords = coords[keep].drop_duplicates("unit").set_index("unit")
    else:
        coords = pd.DataFrame(index=features.index)
    return features, labels, coords


def overlap_matrices(reference, candidate, reference_k, candidate_k):
    counts = np.zeros((reference_k, candidate_k), dtype=int)
    jaccard = np.zeros((reference_k, candidate_k), dtype=float)
    recall = np.zeros((reference_k, candidate_k), dtype=float)
    precision = np.zeros((reference_k, candidate_k), dtype=float)
    for ref_cluster in range(reference_k):
        ref_mask = reference == ref_cluster
        for cand_cluster in range(candidate_k):
            cand_mask = candidate == cand_cluster
            intersection = int(np.logical_and(ref_mask, cand_mask).sum())
            union = int(np.logical_or(ref_mask, cand_mask).sum())
            counts[ref_cluster, cand_cluster] = intersection
            jaccard[ref_cluster, cand_cluster] = intersection / union if union else 0.0
            recall[ref_cluster, cand_cluster] = intersection / ref_mask.sum()
            precision[ref_cluster, cand_cluster] = intersection / cand_mask.sum()
    return counts, jaccard, recall, precision


def match_clusters(reference, candidate, reference_k, candidate_k, objective="jaccard"):
    counts, jaccard, recall, precision = overlap_matrices(reference, candidate, reference_k, candidate_k)
    score = jaccard if objective == "jaccard" else counts.astype(float)
    row_ind, col_ind = linear_sum_assignment(-score)
    rows = []
    for ref_cluster, cand_cluster in zip(row_ind, col_ind, strict=True):
        rows.append(
            {
                "reference_cluster": int(ref_cluster),
                "matched_candidate_cluster": int(cand_cluster),
                "intersection": int(counts[ref_cluster, cand_cluster]),
                "reference_size": int((reference == ref_cluster).sum()),
                "candidate_size": int((candidate == cand_cluster).sum()),
                "jaccard": float(jaccard[ref_cluster, cand_cluster]),
                "recall": float(recall[ref_cluster, cand_cluster]),
                "precision": float(precision[ref_cluster, cand_cluster]),
            }
        )
    return pd.DataFrame(rows).sort_values("reference_cluster"), counts


def summarize_series(values: pd.Series, prefix: str) -> dict[str, float]:
    return {
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_sd": float(values.std(ddof=0)),
        f"{prefix}_median": float(values.median()),
        f"{prefix}_q025": float(values.quantile(0.025)),
        f"{prefix}_q975": float(values.quantile(0.975)),
        f"{prefix}_min": float(values.min()),
        f"{prefix}_max": float(values.max()),
    }


def reference_diagnostics(x, labels):
    global_rows, cluster_rows, refit_rows = [], [], []
    for k in (K_LOW, K_HIGH):
        saved = labels[k]
        samples = silhouette_samples(x, saved)
        global_rows.append(
            {
                "K": k,
                "silhouette": float(silhouette_score(x, saved)),
                "calinski_harabasz": float(calinski_harabasz_score(x, saved)),
                "davies_bouldin": float(davies_bouldin_score(x, saved)),
                "min_cluster_size": int(np.bincount(saved, minlength=k).min()),
                "max_cluster_size": int(np.bincount(saved, minlength=k).max()),
            }
        )
        for cluster in range(k):
            cluster_values = pd.Series(samples[saved == cluster])
            cluster_rows.append(
                {
                    "K": k,
                    "cluster": cluster,
                    "n": int(len(cluster_values)),
                    **summarize_series(cluster_values, "silhouette"),
                    "negative_share": float((cluster_values < 0).mean()),
                }
            )
        model = make_gmm(k, RANDOM_STATE, REFERENCE_N_INIT).fit(x)
        refit = model.predict(x)
        refit_rows.append(
            {
                "K": k,
                "BIC_refit": float(model.bic(x)),
                "AIC_refit": float(model.aic(x)),
                "log_likelihood_per_station": float(model.score(x)),
                "saved_vs_refit_ARI": float(adjusted_rand_score(saved, refit)),
                "converged": bool(model.converged_),
                "n_iter": int(model.n_iter_),
            }
        )
    return pd.DataFrame(global_rows), pd.DataFrame(cluster_rows), pd.DataFrame(refit_rows)


def transition_analysis(units, labels, coords):
    low = labels[K_LOW]
    high = labels[K_HIGH]
    mapping, counts = match_clusters(low, high, K_LOW, K_HIGH, objective="counts")
    contingency = pd.DataFrame(
        counts,
        index=[f"K{K_LOW}_C{i}" for i in range(K_LOW)],
        columns=[f"K{K_HIGH}_C{i}" for i in range(K_HIGH)],
    )
    expected_high = dict(zip(mapping["reference_cluster"], mapping["matched_candidate_cluster"], strict=True))
    detail = pd.DataFrame({"unit": units, f"k{K_LOW}": low, f"k{K_HIGH}": high}).set_index("unit")
    detail = detail.join(coords, how="left")
    detail[f"best_matched_k{K_HIGH}_for_k{K_LOW}"] = detail[f"k{K_LOW}"].map(expected_high)
    detail["follows_best_match"] = detail[f"k{K_HIGH}"] == detail[f"best_matched_k{K_HIGH}_for_k{K_LOW}"]
    detail = detail.reset_index()

    composition_rows = []
    for high_cluster in range(K_HIGH):
        mask = high == high_cluster
        source_counts = pd.Series(low[mask]).value_counts().sort_index()
        for source_low, count in source_counts.items():
            composition_rows.append(
                {
                    f"k{K_HIGH}_cluster": high_cluster,
                    f"source_k{K_LOW}_cluster": int(source_low),
                    "count": int(count),
                    f"k{K_HIGH}_cluster_size": int(mask.sum()),
                    f"source_share_within_k{K_HIGH}": float(count / mask.sum()),
                }
            )
    composition = pd.DataFrame(composition_rows)
    best_count = int(mapping["intersection"].sum())
    summary = {
        "adjusted_rand_index": float(adjusted_rand_score(low, high)),
        "best_match_count": best_count,
        "best_match_share": float(best_count / len(low)),
    }
    return contingency, mapping, composition, detail, summary


def bootstrap_stability(x, labels):
    rng = np.random.default_rng(RANDOM_STATE)
    plan = [(rng.choice(len(x), len(x), replace=True), int(rng.integers(0, 2**31 - 1))) for _ in range(BOOTSTRAP)]
    cluster_rows, global_rows = [], []
    for iteration, (sample_index, base_seed) in enumerate(plan, start=1):
        for k in (K_LOW, K_HIGH):
            model_seed = base_seed + k
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model = make_gmm(k, model_seed, BOOTSTRAP_N_INIT).fit(x[sample_index])
            predicted = model.predict(x)
            matched, _ = match_clusters(labels[k], predicted, k, k, objective="jaccard")
            for row in matched.itertuples(index=False):
                cluster_rows.append(
                    {
                        "iteration": iteration,
                        "K": k,
                        "reference_cluster": row.reference_cluster,
                        "matched_candidate_cluster": row.matched_candidate_cluster,
                        "jaccard": row.jaccard,
                        "recall": row.recall,
                        "precision": row.precision,
                        "reference_size": row.reference_size,
                        "candidate_size": row.candidate_size,
                    }
                )
            global_rows.append(
                {
                    "iteration": iteration,
                    "K": k,
                    "sample_unique_n": int(np.unique(sample_index).size),
                    "model_seed": model_seed,
                    "adjusted_rand_index": float(adjusted_rand_score(labels[k], predicted)),
                    "converged": bool(model.converged_),
                    "n_iter": int(model.n_iter_),
                    "convergence_warnings": sum(issubclass(w.category, ConvergenceWarning) for w in caught),
                }
            )
        if iteration % PROGRESS_EVERY == 0 or iteration == BOOTSTRAP:
            print(f"[bootstrap] {iteration}/{BOOTSTRAP}", flush=True)

    clusters = pd.DataFrame(cluster_rows)
    globals_ = pd.DataFrame(global_rows)
    cluster_summary_rows = []
    for (k, cluster), group in clusters.groupby(["K", "reference_cluster"], sort=True):
        cluster_summary_rows.append(
            {
                "K": int(k),
                "reference_cluster": int(cluster),
                "replicates": int(len(group)),
                **summarize_series(group["jaccard"], "jaccard"),
                **summarize_series(group["recall"], "recall"),
                **summarize_series(group["precision"], "precision"),
                "share_jaccard_below_0_50": float((group["jaccard"] < 0.50).mean()),
                "share_jaccard_at_least_0_75": float((group["jaccard"] >= 0.75).mean()),
            }
        )
    global_summary_rows = []
    for k, group in globals_.groupby("K", sort=True):
        global_summary_rows.append(
            {
                "K": int(k),
                "replicates": int(len(group)),
                **summarize_series(group["adjusted_rand_index"], "ARI"),
                "convergence_rate": float(group["converged"].mean()),
                "total_convergence_warnings": int(group["convergence_warnings"].sum()),
            }
        )
    return clusters, globals_, pd.DataFrame(cluster_summary_rows), pd.DataFrame(global_summary_rows)


def paired_bootstrap_comparison(bootstrap_global_iterations: pd.DataFrame):
    wide = bootstrap_global_iterations.pivot(
        index="iteration", columns="K", values="adjusted_rand_index"
    ).rename(columns={K_LOW: f"ARI_K{K_LOW}", K_HIGH: f"ARI_K{K_HIGH}"})
    diff_col = f"ARI_difference_K{K_LOW}_minus_K{K_HIGH}"
    wide[diff_col] = wide[f"ARI_K{K_LOW}"] - wide[f"ARI_K{K_HIGH}"]
    wide = wide.reset_index()
    diff = wide[diff_col]
    summary = pd.DataFrame(
        [
            {
                "replicates": int(len(diff)),
                **summarize_series(diff, diff_col),
                f"share_K{K_LOW}_greater_than_K{K_HIGH}": float((diff > 0).mean()),
                f"share_K{K_HIGH}_greater_than_K{K_LOW}": float((diff < 0).mean()),
                "share_equal": float(np.isclose(diff, 0.0).mean()),
            }
        ]
    )
    return wide, summary, diff_col


def seed_stability(x, labels):
    cluster_rows, global_rows = [], []
    for run in range(1, SEED_RUNS + 1):
        seed = RANDOM_STATE + 10_000 + run
        for k in (K_LOW, K_HIGH):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model = make_gmm(k, seed, SEED_N_INIT).fit(x)
            predicted = model.predict(x)
            matched, _ = match_clusters(labels[k], predicted, k, k, objective="jaccard")
            for row in matched.itertuples(index=False):
                cluster_rows.append(
                    {
                        "run": run,
                        "seed": seed,
                        "K": k,
                        "reference_cluster": row.reference_cluster,
                        "matched_candidate_cluster": row.matched_candidate_cluster,
                        "jaccard": row.jaccard,
                        "recall": row.recall,
                        "precision": row.precision,
                    }
                )
            global_rows.append(
                {
                    "run": run,
                    "seed": seed,
                    "K": k,
                    "adjusted_rand_index": float(adjusted_rand_score(labels[k], predicted)),
                    "BIC": float(model.bic(x)),
                    "converged": bool(model.converged_),
                    "n_iter": int(model.n_iter_),
                    "convergence_warnings": sum(issubclass(w.category, ConvergenceWarning) for w in caught),
                }
            )
        if run % max(1, min(PROGRESS_EVERY, 5)) == 0 or run == SEED_RUNS:
            print(f"[seed stability] {run}/{SEED_RUNS}", flush=True)

    clusters = pd.DataFrame(cluster_rows)
    globals_ = pd.DataFrame(global_rows)
    cluster_summary_rows = []
    for (k, cluster), group in clusters.groupby(["K", "reference_cluster"], sort=True):
        cluster_summary_rows.append(
            {
                "K": int(k),
                "reference_cluster": int(cluster),
                "runs": int(len(group)),
                **summarize_series(group["jaccard"], "jaccard"),
                "share_exact_jaccard_1": float(np.isclose(group["jaccard"], 1.0).mean()),
            }
        )
    global_summary_rows = []
    for k, group in globals_.groupby("K", sort=True):
        global_summary_rows.append(
            {
                "K": int(k),
                "runs": int(len(group)),
                **summarize_series(group["adjusted_rand_index"], "ARI"),
                **summarize_series(group["BIC"], "BIC"),
                "convergence_rate": float(group["converged"].mean()),
                "total_convergence_warnings": int(group["convergence_warnings"].sum()),
            }
        )
    return clusters, globals_, pd.DataFrame(cluster_summary_rows), pd.DataFrame(global_summary_rows)


def write_plots(contingency, silhouette, bootstrap_clusters, bootstrap_global, paired_bootstrap, diff_col, n_stations):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    image = ax.imshow(contingency.to_numpy(), cmap="Purples", aspect="auto")
    for row in range(contingency.shape[0]):
        for col in range(contingency.shape[1]):
            ax.text(col, row, str(int(contingency.iloc[row, col])), ha="center", va="center", fontsize=10)
    ax.set_xticks(range(contingency.shape[1]), contingency.columns)
    ax.set_yticks(range(contingency.shape[0]), contingency.index)
    ax.set_xlabel(f"K={K_HIGH} cluster")
    ax.set_ylabel(f"K={K_LOW} cluster")
    ax.set_title(f"K={K_LOW} to K={K_HIGH} membership transition (all-modes, {n_stations} stations)")
    fig.colorbar(image, ax=ax, label="Stations")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"rail_allmodes_k{K_LOW}_k{K_HIGH}_transition_heatmap.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, k in zip(axes, (K_LOW, K_HIGH), strict=True):
        part = silhouette[silhouette["K"] == k].sort_values("cluster")
        colors = ["#2F6B4F" if v >= 0.05 else "#9A3D3D" for v in part["silhouette_mean"]]
        ax.bar(part["cluster"].astype(str), part["silhouette_mean"], color=colors)
        ax.axhline(0, color="black", linewidth=0.8)
        for row in part.itertuples(index=False):
            ax.text(
                row.cluster,
                row.silhouette_mean + (0.008 if row.silhouette_mean >= 0 else -0.014),
                f"neg {row.negative_share:.0%}",
                ha="center", va="bottom" if row.silhouette_mean >= 0 else "top", fontsize=8,
            )
        ax.set_title(f"K={k}")
        ax.set_xlabel("Cluster")
    axes[0].set_ylabel("Mean silhouette")
    fig.suptitle(f"Cluster-level separation (all-modes, {n_stations} stations)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"rail_allmodes_k{K_LOW}_k{K_HIGH}_cluster_silhouette_comparison.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, k in zip(axes, (K_LOW, K_HIGH), strict=True):
        part = bootstrap_clusters[bootstrap_clusters["K"] == k].sort_values("reference_cluster")
        x_pos = np.arange(len(part))
        lower = part["jaccard_mean"] - part["jaccard_q025"]
        upper = part["jaccard_q975"] - part["jaccard_mean"]
        ax.bar(x_pos, part["jaccard_mean"], color="#500778", alpha=0.85)
        ax.errorbar(x_pos, part["jaccard_mean"], yerr=np.vstack([lower, upper]), fmt="none", ecolor="black", capsize=3)
        ax.axhline(0.50, color="#9A3D3D", linestyle="--", linewidth=1, label="weak < 0.50")
        ax.axhline(0.75, color="#2F6B4F", linestyle=":", linewidth=1, label="strong >= 0.75")
        ax.set_xticks(x_pos, [f"C{i}" for i in part["reference_cluster"]])
        ax.set_ylim(0, 1.03)
        ax.set_title(f"K={k}")
        ax.set_xlabel("Reference cluster")
    axes[0].set_ylabel("Bootstrap matched Jaccard")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=8)
    fig.suptitle(f"Cluster-level bootstrap stability, {BOOTSTRAP} replicates (all-modes, {n_stations} stations)")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(FIGURES_DIR / f"rail_allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_cluster_stability.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    x_pos = np.arange(len(bootstrap_global))
    lower = bootstrap_global["ARI_mean"] - bootstrap_global["ARI_q025"]
    upper = bootstrap_global["ARI_q975"] - bootstrap_global["ARI_mean"]
    ax.bar(x_pos, bootstrap_global["ARI_mean"], color=["#2F6B4F", "#500778"])
    ax.errorbar(x_pos, bootstrap_global["ARI_mean"], yerr=np.vstack([lower, upper]), fmt="none", ecolor="black", capsize=4)
    ax.set_xticks(x_pos, [f"K={k}" for k in bootstrap_global["K"]])
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Adjusted Rand Index")
    ax.set_title(f"Global paired-bootstrap stability (all-modes, {n_stations} stations)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"rail_allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_global_stability.png", dpi=220)
    plt.close(fig)

    difference = paired_bootstrap[diff_col]
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.hist(difference, bins=24, color="#500778", alpha=0.82, edgecolor="white")
    ax.axvline(0, color="#9A3D3D", linestyle="--", linewidth=1.4, label="equal stability")
    ax.axvline(difference.mean(), color="#2F6B4F", linewidth=1.6, label=f"mean = {difference.mean():.3f}")
    ax.set_xlabel(f"Paired bootstrap ARI difference (K={K_LOW} minus K={K_HIGH})")
    ax.set_ylabel("Replicates")
    ax.set_title(f"Distribution of paired stability differences (all-modes, {n_stations} stations)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"rail_allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_paired_ari_difference.png", dpi=220)
    plt.close(fig)


def markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    display = frame.copy()
    for column in display.select_dtypes(include=["float", "floating"]).columns:
        display[column] = display[column].map(lambda v: f"{v:.{digits}f}")
    headers = [str(c) for c in display.columns]
    rows = [[str(v) for v in row] for row in display.itertuples(index=False, name=None)]
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(v)) for w, v in zip(widths, row, strict=True)]
    header_line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True)) + " |"
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    body = ["| " + " | ".join(v.ljust(w) for v, w in zip(row, widths, strict=True)) + " |" for row in rows]
    return "\n".join([header_line, sep, *body])


def build_model_summary(global_diag, refit, original, bootstrap_global, bootstrap_clusters, seed_global):
    original = original[original["K"].isin([K_LOW, K_HIGH])].copy()
    original["K"] = original["K"].astype(int)
    summary = global_diag.merge(refit, on="K", how="left")
    summary = summary.merge(
        original[["K", "BIC", "silhouette", "ARI", "ARI_sd"]].rename(
            columns={
                "BIC": "BIC_original",
                "silhouette": "silhouette_original",
                "ARI": "bootstrap_ARI_original_20",
                "ARI_sd": "bootstrap_ARI_sd_original_20",
            }
        ),
        on="K", how="left",
    )
    summary = summary.merge(
        bootstrap_global[["K", "ARI_mean", "ARI_sd", "ARI_q025", "ARI_q975", "convergence_rate"]].rename(
            columns={
                "ARI_mean": f"bootstrap_ARI_mean_{BOOTSTRAP}",
                "ARI_sd": f"bootstrap_ARI_sd_{BOOTSTRAP}",
                "ARI_q025": f"bootstrap_ARI_q025_{BOOTSTRAP}",
                "ARI_q975": f"bootstrap_ARI_q975_{BOOTSTRAP}",
                "convergence_rate": "bootstrap_convergence_rate",
            }
        ),
        on="K", how="left",
    )
    weak = (
        bootstrap_clusters.assign(weak=lambda d: d["jaccard_mean"] < 0.50)
        .groupby("K")
        .agg(weakest_cluster_jaccard=("jaccard_mean", "min"), weak_cluster_count=("weak", "sum"))
        .reset_index()
    )
    summary = summary.merge(weak, on="K", how="left")
    summary = summary.merge(
        seed_global[["K", "ARI_mean", "ARI_min", "convergence_rate"]].rename(
            columns={"ARI_mean": "seed_ARI_mean", "ARI_min": "seed_ARI_min", "convergence_rate": "seed_convergence_rate"}
        ),
        on="K", how="left",
    )
    return summary.sort_values("K")


def write_reports(model_summary, silhouette, bootstrap_clusters, paired_bootstrap_summary, diff_col,
                   seed_clusters, transition_summary, mapping, metadata):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lo = model_summary.set_index("K").loc[K_LOW]
    hi = model_summary.set_index("K").loc[K_HIGH]
    weak_hi = bootstrap_clusters.loc[
        (bootstrap_clusters["K"] == K_HIGH) & (bootstrap_clusters["jaccard_mean"] < 0.50),
        ["reference_cluster", "jaccard_mean", "share_jaccard_below_0_50"],
    ]
    silhouette_display = silhouette.sort_values(["K", "cluster"])
    paired = paired_bootstrap_summary.iloc[0]
    bic_favors_high = hi["BIC_refit"] < lo["BIC_refit"]

    ari_col = f"bootstrap_ARI_mean_{BOOTSTRAP}"
    weak_text = (
        markdown_table(weak_hi.rename(columns={"reference_cluster": f"K{K_HIGH}_cluster"}))
        if not weak_hi.empty
        else f"No K={K_HIGH} cluster had mean bootstrap Jaccard below 0.50."
    )
    mapping_display = mapping[
        ["reference_cluster", "matched_candidate_cluster", "intersection", "reference_size", "candidate_size", "jaccard"]
    ].rename(columns={"reference_cluster": f"K{K_LOW}_cluster", "matched_candidate_cluster": f"matched_K{K_HIGH}_cluster"})
    compact_summary = model_summary[
        ["K", "BIC_refit", "silhouette", "calinski_harabasz", "davies_bouldin",
         ari_col, f"bootstrap_ARI_q025_{BOOTSTRAP}", f"bootstrap_ARI_q975_{BOOTSTRAP}",
         "weakest_cluster_jaccard", "weak_cluster_count", "seed_ARI_mean"]
    ]

    report_zh = f"""## 材料护照

- 来源: numbat_all_area_test 扩展检验 -- 稳定性电池(K={K_LOW} vs K={K_HIGH})
- 生成时间: {metadata['finished_at']}
- 验证状态: 已核查 -- **本报告是验证/稳健性检验版本,不是正式版本**

> **本报告非正式版本。** 这是"已采纳解 vs 相邻候选解"的稳健性验证电池,
> 不是 K 选择的正式依据。正文如果要引用 random-seed ARI、bootstrap ARI 或
> weakest-cluster Jaccard,必须使用 `08_k_selection_panel.py` 产出的
> `rail_allmodes_k_selection_panel.csv`(该 CSV 才是与正文配图对应的正式
> 数值),不要引用下表里的 `seed_ARI_mean`/`bootstrap_ARI_mean_{BOOTSTRAP}`/
> `weakest_cluster_jaccard`——这三列的参照对象是"已保存/已采纳的标签"而非
> "同批次种子/重抽样彼此之间",与正式版口径不同,数值也不同。

# 地铁全模式聚类 K={K_LOW} 与 K={K_HIGH} 内部稳定性检验(验证版本)

## 检验边界

本检验只使用{metadata['n_stations']}个站点(LU+DLR+Overground+伊丽莎白线,电车因数据结构性缺失
已剔除,详见主报告)的344维全周进出站时序特征,以及已保存的 K={K_LOW}、
K={K_HIGH} 标签。K={K_LOW}/K={K_HIGH} 是本次全模式数据自己的 BIC
最接近的一对(见 `rail_allmodes_bic_best.txt`),与 canonical 270站检验
这组 K 值用于检查已采用解与相邻候选解之间的稳定性差异,是正式 K 选择结论
之外的补充稳健性检验,不能替代 `08_k_selection_panel.py` 的正式结果。方法学
(diag协方差GMM、bootstrap={BOOTSTRAP}次、
seed_runs={SEED_RUNS}次)与既有的 `rail_k_selection_validation` 完全一致。

## 全局证据

{markdown_table(compact_summary)}

- BIC 差值(K{K_HIGH}−K{K_LOW}):`{hi['BIC_refit'] - lo['BIC_refit']:.3f}`,
  {'因此 BIC 支持 K=' + str(K_HIGH) if bic_favors_high else '因此 BIC 支持 K=' + str(K_LOW)}。
- silhouette 差值(K{K_HIGH}−K{K_LOW}):`{hi['silhouette'] - lo['silhouette']:.6f}`。
- {BOOTSTRAP}次配对 bootstrap 平均 ARI:K={K_LOW} 为
  `{lo[ari_col]:.3f}`,K={K_HIGH} 为 `{hi[ari_col]:.3f}`。
- 配对差值 K{K_LOW}−K{K_HIGH} 的均值为
  `{paired[f'{diff_col}_mean']:.3f}`,95%经验区间为
  `[{paired[f'{diff_col}_q025']:.3f}, {paired[f'{diff_col}_q975']:.3f}]`;
  K={K_LOW} 在 `{paired[f'share_K{K_LOW}_greater_than_K{K_HIGH}']:.1%}`
  的配对重抽样中更高。
- 完整样本随机种子平均 ARI:K={K_LOW} 为 `{lo['seed_ARI_mean']:.3f}`,
  K={K_HIGH} 为 `{hi['seed_ARI_mean']:.3f}`。

## K={K_LOW} 到 K={K_HIGH} 的成员结构

- 两套标签 ARI:`{transition_summary['adjusted_rand_index']:.3f}`。
- 最佳一对一匹配:`{transition_summary['best_match_count']}` /
  `{metadata['n_stations']}`(`{transition_summary['best_match_share']:.1%}`)。

{markdown_table(mapping_display)}

## K={K_HIGH} 中的弱复现成分

{weak_text}

## 全部簇级 silhouette

{markdown_table(silhouette_display[['K', 'cluster', 'n', 'silhouette_mean', 'silhouette_median', 'negative_share']])}

## 方法解释

1. bootstrap 检验的是站点重抽样下的成员复现性,不是某个 K 正确的概率。
2. 随机种子检验的是优化过程敏感性,两者不能混为一谈。
3. 本检验与 `rail_k_selection_validation`(canonical 270站,K=5 vs K=6)
   是同一套方法学在不同站点范围上的重复应用,两份报告的数字不可直接相减
   比较(站点数、特征分布都不同),只能分别在各自范围内解读。

## 局限

- 结论以当前344维特征、标准化方式、GMM模型和对角协方差为条件。
- 本检验的{metadata['n_stations']}站里有{metadata['n_stations']-270}个是本次扩展检验才纳入,未经过与原270站同等程度的
  人工核查(不过14处同址跨模式站点已在 `01b_merge_colocated_stations.py`
  里合并处理)。
- 稳定性不能自动赋予簇以城市功能或社会经济含义。

## 复现方式

```
python src/07_stability_allmodes.py
```
"""
    (REPORT_DIR / f"STABILITY_K{K_LOW}_K{K_HIGH}_ALLMODES_ZH.md").write_text(report_zh, encoding="utf-8")

    reproducible_note = (
        f"K={K_HIGH} has lower (better) refitted BIC than K={K_LOW}."
        if bic_favors_high
        else f"K={K_LOW} has lower (better) refitted BIC than K={K_HIGH}."
    )
    report_en = f"""## Material Passport

- Origin: `numbat_all_area_test` extension check -- stability battery (K={K_LOW} vs K={K_HIGH})
- Generated: {metadata['finished_at']}
- Verification status: checked -- **this is a VALIDATION report, not the official one**

> **NOT the official K-selection report.** This is a robustness/validation
> battery comparing the adopted solution against an adjacent candidate; it
> is not the official basis for K selection. Any dissertation text citing
> random-seed ARI, bootstrap ARI, or weakest-cluster Jaccard must use
> `08_k_selection_panel.py`'s `rail_allmodes_k_selection_panel.csv` (the
> official source, matching the main-text figure) -- not the
> `seed_ARI_mean` / `bootstrap_ARI_mean_{BOOTSTRAP}` / `weakest_cluster_jaccard`
> columns below, which measure agreement WITH the saved/adopted labels
> rather than agreement AMONG same-budget seeds/resamples and are therefore
> numerically different from the official figures even though the column
> names look alike.

# All-Modes Rail Clustering: K={K_LOW} vs K={K_HIGH} Internal Stability Check (validation version)

## Scope

This check uses only the 344-dimensional full-week entry/exit feature
matrix for the {metadata['n_stations']} all-modes stations (LU + DLR + Overground + Elizabeth
line; trams are structurally excluded, see the main comparison report) and
the saved K={K_LOW}/K={K_HIGH} labels. This pair checks the adopted solution
against an adjacent candidate as a supplementary robustness check; it does
not replace `08_k_selection_panel.py`'s official result, which remains the
authoritative source for BIC ranking and for the random-seed/bootstrap
stability numbers. Methodology (diag
GMM, bootstrap={BOOTSTRAP}, seed_runs={SEED_RUNS}) is identical to
`rail_k_selection_validation`.

## Global evidence

{markdown_table(compact_summary)}

- BIC difference (K{K_HIGH} minus K{K_LOW}): `{hi['BIC_refit'] - lo['BIC_refit']:.3f}`. {reproducible_note}
- Silhouette difference (K{K_HIGH} minus K{K_LOW}): `{hi['silhouette'] - lo['silhouette']:.6f}`.
- Paired {BOOTSTRAP}-replicate bootstrap ARI: K={K_LOW} = `{lo[ari_col]:.3f}`,
  K={K_HIGH} = `{hi[ari_col]:.3f}`.
- Paired difference K{K_LOW} minus K{K_HIGH}: mean `{paired[f'{diff_col}_mean']:.3f}`,
  95% empirical interval `[{paired[f'{diff_col}_q025']:.3f}, {paired[f'{diff_col}_q975']:.3f}]`;
  K={K_LOW} is higher in `{paired[f'share_K{K_LOW}_greater_than_K{K_HIGH}']:.1%}` of paired resamples.
- Full-data random-seed mean ARI: K={K_LOW} = `{lo['seed_ARI_mean']:.3f}`,
  K={K_HIGH} = `{hi['seed_ARI_mean']:.3f}`.

## K={K_LOW} to K={K_HIGH} structure

- Adjusted Rand Index: `{transition_summary['adjusted_rand_index']:.3f}`
- Best one-to-one matched stations: `{transition_summary['best_match_count']}` /
  `{metadata['n_stations']}` (`{transition_summary['best_match_share']:.1%}`)

{markdown_table(mapping_display)}

## Weak K={K_HIGH} components under bootstrap

{weak_text}

## Full cluster-level silhouette

{markdown_table(silhouette_display[['K', 'cluster', 'n', 'silhouette_mean', 'silhouette_median', 'negative_share']])}

## Interpretation rules

1. Bootstrap measures resampling recurrence, not the probability a given K is correct.
2. Random-seed stability measures optimisation sensitivity; it is a distinct concept.
3. This is the same methodology as `rail_k_selection_validation` (canonical
   270 stations, K=5 vs K=6) applied to a different station scope --
   numbers are not directly comparable across the two reports (different
   station counts and feature distributions); read each within its own scope.

## Limitations

- Conditional on the current 344-dim features, normalisation, GMM family, and diagonal covariance.
- {metadata['n_stations']-270} of the {metadata['n_stations']} stations here were only added in this extension
  check and have not had the same manual review as the canonical 270,
  though the 14 co-located cross-mode sites have been merged via
  `01b_merge_colocated_stations.py`.
- Stability does not by itself confer urban-functional or socio-economic meaning on a cluster.

## Reproduction

```
python src/07_stability_allmodes.py
```
"""
    (REPORT_DIR / f"STABILITY_K{K_LOW}_K{K_HIGH}_ALLMODES.md").write_text(report_en, encoding="utf-8")


def main() -> int:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    data_out = DATA_DIR
    for directory in (data_out, FIGURES_DIR, REPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    print("[load] validating inputs", flush=True)
    features, labels, coords = validate_inputs()
    x = features.to_numpy(dtype=float)
    original = pd.read_csv(ORIGINAL_KDIAG_PATH)

    print("[diagnostics] reference refit and silhouettes", flush=True)
    global_diag, silhouette, refit = reference_diagnostics(x, labels)
    print(f"[transition] K={K_LOW} versus K={K_HIGH} membership", flush=True)
    contingency, mapping, composition, transition_detail, transition_summary = transition_analysis(
        features.index, labels, coords
    )

    print(f"[bootstrap] starting {BOOTSTRAP} paired replicates", flush=True)
    boot_clusters_raw, boot_global_raw, boot_clusters, boot_global = bootstrap_stability(x, labels)
    paired_bootstrap, paired_bootstrap_summary, diff_col = paired_bootstrap_comparison(boot_global_raw)
    print(f"[seed stability] starting {SEED_RUNS} full-data refits", flush=True)
    seed_clusters_raw, seed_global_raw, seed_clusters, seed_global = seed_stability(x, labels)

    model_summary = build_model_summary(global_diag, refit, original, boot_global, boot_clusters, seed_global)

    outputs = {
        f"allmodes_k{K_LOW}_k{K_HIGH}_global_reference_diagnostics.csv": global_diag,
        f"allmodes_k{K_LOW}_k{K_HIGH}_reference_refit_diagnostics.csv": refit,
        f"allmodes_k{K_LOW}_k{K_HIGH}_cluster_silhouette_summary.csv": silhouette,
        f"allmodes_k{K_LOW}_k{K_HIGH}_contingency.csv": contingency.reset_index(names=f"k{K_LOW}_cluster"),
        f"allmodes_k{K_LOW}_k{K_HIGH}_best_mapping.csv": mapping,
        f"allmodes_k{K_LOW}_k{K_HIGH}_source_composition.csv": composition,
        f"allmodes_k{K_LOW}_k{K_HIGH}_station_transition_detail.csv": transition_detail,
        f"allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_cluster_stability_iterations.csv": boot_clusters_raw,
        f"allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_global_stability_iterations.csv": boot_global_raw,
        f"allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_cluster_stability_summary.csv": boot_clusters,
        f"allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_global_stability_summary.csv": boot_global,
        f"allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_paired_ari_comparison.csv": paired_bootstrap,
        f"allmodes_k{K_LOW}_k{K_HIGH}_bootstrap_paired_ari_summary.csv": paired_bootstrap_summary,
        f"allmodes_k{K_LOW}_k{K_HIGH}_seed_cluster_stability_iterations.csv": seed_clusters_raw,
        f"allmodes_k{K_LOW}_k{K_HIGH}_seed_global_stability_iterations.csv": seed_global_raw,
        f"allmodes_k{K_LOW}_k{K_HIGH}_seed_cluster_stability_summary.csv": seed_clusters,
        f"allmodes_k{K_LOW}_k{K_HIGH}_seed_global_stability_summary.csv": seed_global,
        f"allmodes_k{K_LOW}_k{K_HIGH}_model_selection_summary.csv": model_summary,
    }
    fallback_outputs: dict[str, str] = {}
    for filename, frame in outputs.items():
        target = data_out / filename
        try:
            frame.to_csv(target, index=False, encoding="utf-8-sig")
        except PermissionError:
            # Windows/Excel can hold a CSV open. Preserve the locked historical
            # file and write the current result beside it rather than aborting
            # the whole battery before figures and reports are produced.
            fallback = target.with_name(f"{target.stem}_20260807{target.suffix}")
            frame.to_csv(fallback, index=False, encoding="utf-8-sig")
            fallback_outputs[str(target)] = str(fallback)
            print(f"[write warning] locked: {target.name}; wrote {fallback.name}", flush=True)

    print("[figures] rendering", flush=True)
    write_plots(contingency, silhouette, boot_clusters, boot_global, paired_bootstrap, diff_col, features.shape[0])

    finished_at = datetime.now(timezone.utc).isoformat()
    duration = time.perf_counter() - started
    input_paths = {
        "features": FEATURES_PATH.resolve(),
        f"labels_k{K_LOW}": LABELS_LOW_PATH.resolve(),
        f"labels_k{K_HIGH}": LABELS_HIGH_PATH.resolve(),
        "original_kdiag": ORIGINAL_KDIAG_PATH.resolve(),
    }
    metadata = {
        "experiment_id": f"rail-allmodes-k{K_LOW}-k{K_HIGH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
        "command": " ".join([sys.executable, str(SCRIPT_PATH)]),
        "working_directory": str(Path.cwd().resolve()),
        "script": str(SCRIPT_PATH),
        "n_stations": int(features.shape[0]),
        "n_features": int(features.shape[1]),
        "k_low": K_LOW,
        "k_high": K_HIGH,
        "parameters": {
            "bootstrap": BOOTSTRAP,
            "seed_runs": SEED_RUNS,
            "reference_n_init": REFERENCE_N_INIT,
            "bootstrap_n_init": BOOTSTRAP_N_INIT,
            "seed_n_init": SEED_N_INIT,
            "random_state": RANDOM_STATE,
            "reg_covar": REG_COVAR,
            "max_iter": MAX_ITER,
            "covariance_type": "diag",
        },
        "locked_output_fallbacks": fallback_outputs,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "pyarrow": pyarrow.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "inputs": {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in input_paths.items()},
        "transition_summary": transition_summary,
    }
    write_reports(
        model_summary, silhouette, boot_clusters, paired_bootstrap_summary, diff_col,
        seed_clusters, transition_summary, mapping, metadata,
    )
    (REPORT_DIR / f"RUN_METADATA_K{K_LOW}_K{K_HIGH}_ALLMODES.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[complete] {duration:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
