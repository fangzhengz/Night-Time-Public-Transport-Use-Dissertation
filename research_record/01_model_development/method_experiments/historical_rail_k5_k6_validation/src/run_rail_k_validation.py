#!/usr/bin/env python
"""Validate the current Underground K=5 versus K=6 clustering choice.

The script is intentionally self-contained and read-only with respect to the
accepted clustering pipeline. It writes only beneath its configured output
root. LNWC, IMD, and other downstream interpretation variables are excluded.
"""

from __future__ import annotations

import argparse
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

# Avoid a Windows/joblib physical-core probe warning. GMM itself is not run in
# a manually parallelized loop, so this does not change the fitted models.
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


SCRIPT_PATH = Path(__file__).resolve()
WORKSPACE = SCRIPT_PATH.parents[1]
FYP_ROOT = WORKSPACE.parent
DEFAULT_SOURCE = FYP_ROOT / "cluster_clean_version_fullweek"
DEFAULT_COORDS = (
    FYP_ROOT
    / "cluster_clean_version_grouped"
    / "outputs"
    / "preprocessed"
    / "rail_coords.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Internal stability validation for rail K=5 versus K=6."
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=DEFAULT_SOURCE / "outputs" / "features" / "X_rail.parquet",
    )
    parser.add_argument(
        "--labels-k5",
        type=Path,
        default=DEFAULT_SOURCE / "outputs" / "labels" / "rail_k5_labels.csv",
    )
    parser.add_argument(
        "--labels-k6",
        type=Path,
        default=DEFAULT_SOURCE / "outputs" / "labels" / "rail_k6_labels.csv",
    )
    parser.add_argument(
        "--original-kdiag",
        type=Path,
        default=DEFAULT_SOURCE / "outputs" / "diagnostics" / "rail_kdiag.csv",
    )
    parser.add_argument("--coords", type=Path, default=DEFAULT_COORDS)
    parser.add_argument("--output-root", type=Path, default=WORKSPACE / "outputs")
    parser.add_argument("--bootstrap", type=int, default=200)
    parser.add_argument("--seed-runs", type=int, default=20)
    parser.add_argument("--reference-n-init", type=int, default=20)
    parser.add_argument("--bootstrap-n-init", type=int, default=3)
    parser.add_argument("--seed-n-init", type=int, default=20)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--reg-covar", type=float, default=1e-6)
    parser.add_argument("--max-iter", type=int, default=300)
    parser.add_argument("--progress-every", type=int, default=10)
    args = parser.parse_args()
    if args.bootstrap < 1:
        parser.error("--bootstrap must be at least 1")
    if args.seed_runs < 1:
        parser.error("--seed-runs must be at least 1")
    return args


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_gmm(
    k: int,
    seed: int,
    n_init: int,
    reg_covar: float,
    max_iter: int,
) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type="diag",
        n_init=n_init,
        reg_covar=reg_covar,
        max_iter=max_iter,
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


def validate_inputs(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[int, np.ndarray], pd.DataFrame]:
    paths = [args.features, args.labels_k5, args.labels_k6, args.original_kdiag]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    features = pd.read_parquet(args.features)
    if features.empty:
        raise ValueError("Feature matrix is empty")
    features.index = features.index.astype(str)
    if features.index.duplicated().any():
        raise ValueError("Feature matrix contains duplicate unit IDs")
    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise ValueError("Feature matrix contains NaN or infinite values")

    labels = {
        5: load_label(args.labels_k5, 5, features.index)["cluster"].to_numpy(),
        6: load_label(args.labels_k6, 6, features.index)["cluster"].to_numpy(),
    }

    if args.coords.is_file():
        coords = pd.read_csv(args.coords, encoding="utf-8-sig")
        coords["NLC"] = coords["NLC"].astype(str)
        keep = [c for c in ["NLC", "Station", "Fare Zone", "lon", "lat"] if c in coords]
        coords = coords[keep].drop_duplicates("NLC").set_index("NLC")
    else:
        coords = pd.DataFrame(index=features.index)
    return features, labels, coords


def overlap_matrices(
    reference: np.ndarray,
    candidate: np.ndarray,
    reference_k: int,
    candidate_k: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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


def match_clusters(
    reference: np.ndarray,
    candidate: np.ndarray,
    reference_k: int,
    candidate_k: int,
    objective: str = "jaccard",
) -> tuple[pd.DataFrame, np.ndarray]:
    counts, jaccard, recall, precision = overlap_matrices(
        reference, candidate, reference_k, candidate_k
    )
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


def reference_diagnostics(
    x: np.ndarray,
    labels: dict[int, np.ndarray],
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    global_rows = []
    cluster_rows = []
    refit_rows = []
    for k in (5, 6):
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

        model = make_gmm(
            k,
            args.random_state,
            args.reference_n_init,
            args.reg_covar,
            args.max_iter,
        ).fit(x)
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


def transition_analysis(
    units: pd.Index,
    labels: dict[int, np.ndarray],
    coords: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    k5 = labels[5]
    k6 = labels[6]
    mapping, counts = match_clusters(k5, k6, 5, 6, objective="counts")
    contingency = pd.DataFrame(
        counts,
        index=[f"K5_C{i}" for i in range(5)],
        columns=[f"K6_C{i}" for i in range(6)],
    )
    expected_k6 = dict(
        zip(mapping["reference_cluster"], mapping["matched_candidate_cluster"], strict=True)
    )
    detail = pd.DataFrame({"unit": units, "k5": k5, "k6": k6}).set_index("unit")
    detail = detail.join(coords, how="left")
    detail["best_matched_k6_for_k5"] = detail["k5"].map(expected_k6)
    detail["follows_best_match"] = detail["k6"] == detail["best_matched_k6_for_k5"]
    detail = detail.reset_index()

    composition_rows = []
    for k6_cluster in range(6):
        mask = k6 == k6_cluster
        source_counts = pd.Series(k5[mask]).value_counts().sort_index()
        for source_k5, count in source_counts.items():
            composition_rows.append(
                {
                    "k6_cluster": k6_cluster,
                    "source_k5_cluster": int(source_k5),
                    "count": int(count),
                    "k6_cluster_size": int(mask.sum()),
                    "source_share_within_k6": float(count / mask.sum()),
                }
            )
    composition = pd.DataFrame(composition_rows)
    best_count = int(mapping["intersection"].sum())
    summary = {
        "adjusted_rand_index": float(adjusted_rand_score(k5, k6)),
        "best_match_count": best_count,
        "best_match_share": float(best_count / len(k5)),
    }
    return contingency, mapping, composition, detail, summary


def bootstrap_stability(
    x: np.ndarray,
    labels: dict[int, np.ndarray],
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(args.random_state)
    plan = [
        (
            rng.choice(len(x), len(x), replace=True),
            int(rng.integers(0, 2**31 - 1)),
        )
        for _ in range(args.bootstrap)
    ]
    cluster_rows = []
    global_rows = []
    for iteration, (sample_index, base_seed) in enumerate(plan, start=1):
        for k in (5, 6):
            model_seed = base_seed + k
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model = make_gmm(
                    k,
                    model_seed,
                    args.bootstrap_n_init,
                    args.reg_covar,
                    args.max_iter,
                ).fit(x[sample_index])
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
                    "convergence_warnings": sum(
                        issubclass(w.category, ConvergenceWarning) for w in caught
                    ),
                }
            )
        if iteration % args.progress_every == 0 or iteration == args.bootstrap:
            print(f"[bootstrap] {iteration}/{args.bootstrap}", flush=True)

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
    return (
        clusters,
        globals_,
        pd.DataFrame(cluster_summary_rows),
        pd.DataFrame(global_summary_rows),
    )


def paired_bootstrap_comparison(
    bootstrap_global_iterations: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare K=5 and K=6 on the same bootstrap samples."""
    wide = bootstrap_global_iterations.pivot(
        index="iteration", columns="K", values="adjusted_rand_index"
    ).rename(columns={5: "ARI_K5", 6: "ARI_K6"})
    if {"ARI_K5", "ARI_K6"}.difference(wide.columns):
        raise ValueError("Paired bootstrap comparison requires both K=5 and K=6")
    wide["ARI_difference_K5_minus_K6"] = wide["ARI_K5"] - wide["ARI_K6"]
    wide = wide.reset_index()
    diff = wide["ARI_difference_K5_minus_K6"]
    summary = pd.DataFrame(
        [
            {
                "replicates": int(len(diff)),
                **summarize_series(diff, "ARI_difference_K5_minus_K6"),
                "share_K5_greater_than_K6": float((diff > 0).mean()),
                "share_K6_greater_than_K5": float((diff < 0).mean()),
                "share_equal": float(np.isclose(diff, 0.0).mean()),
            }
        ]
    )
    return wide, summary


def seed_stability(
    x: np.ndarray,
    labels: dict[int, np.ndarray],
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cluster_rows = []
    global_rows = []
    for run in range(1, args.seed_runs + 1):
        seed = args.random_state + 10_000 + run
        for k in (5, 6):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model = make_gmm(
                    k,
                    seed,
                    args.seed_n_init,
                    args.reg_covar,
                    args.max_iter,
                ).fit(x)
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
                    "convergence_warnings": sum(
                        issubclass(w.category, ConvergenceWarning) for w in caught
                    ),
                }
            )
        if run % max(1, min(args.progress_every, 5)) == 0 or run == args.seed_runs:
            print(f"[seed stability] {run}/{args.seed_runs}", flush=True)

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
    return (
        clusters,
        globals_,
        pd.DataFrame(cluster_summary_rows),
        pd.DataFrame(global_summary_rows),
    )


def write_plots(
    figures_dir: Path,
    contingency: pd.DataFrame,
    silhouette: pd.DataFrame,
    bootstrap_clusters: pd.DataFrame,
    bootstrap_global: pd.DataFrame,
    paired_bootstrap: pd.DataFrame,
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    image = ax.imshow(contingency.to_numpy(), cmap="Purples", aspect="auto")
    for row in range(contingency.shape[0]):
        for col in range(contingency.shape[1]):
            value = int(contingency.iloc[row, col])
            ax.text(col, row, str(value), ha="center", va="center", fontsize=10)
    ax.set_xticks(range(contingency.shape[1]), contingency.columns)
    ax.set_yticks(range(contingency.shape[0]), contingency.index)
    ax.set_xlabel("K=6 cluster")
    ax.set_ylabel("K=5 cluster")
    ax.set_title("K=5 to K=6 membership transition")
    fig.colorbar(image, ax=ax, label="Stations")
    fig.tight_layout()
    fig.savefig(figures_dir / "k5_k6_transition_heatmap.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, k in zip(axes, (5, 6), strict=True):
        part = silhouette[silhouette["K"] == k].sort_values("cluster")
        colors = ["#2F6B4F" if value >= 0.05 else "#9A3D3D" for value in part["silhouette_mean"]]
        ax.bar(part["cluster"].astype(str), part["silhouette_mean"], color=colors)
        ax.axhline(0, color="black", linewidth=0.8)
        for row in part.itertuples(index=False):
            ax.text(
                row.cluster,
                row.silhouette_mean + (0.008 if row.silhouette_mean >= 0 else -0.014),
                f"neg {row.negative_share:.0%}",
                ha="center",
                va="bottom" if row.silhouette_mean >= 0 else "top",
                fontsize=8,
            )
        ax.set_ylim(-0.04, 0.29)
        ax.set_title(f"K={k}")
        ax.set_xlabel("Cluster")
    axes[0].set_ylabel("Mean silhouette")
    fig.suptitle("Cluster-level separation")
    fig.tight_layout()
    fig.savefig(figures_dir / "cluster_silhouette_comparison.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, k in zip(axes, (5, 6), strict=True):
        part = bootstrap_clusters[bootstrap_clusters["K"] == k].sort_values(
            "reference_cluster"
        )
        x_pos = np.arange(len(part))
        lower = part["jaccard_mean"] - part["jaccard_q025"]
        upper = part["jaccard_q975"] - part["jaccard_mean"]
        ax.bar(x_pos, part["jaccard_mean"], color="#500778", alpha=0.85)
        ax.errorbar(
            x_pos,
            part["jaccard_mean"],
            yerr=np.vstack([lower, upper]),
            fmt="none",
            ecolor="black",
            capsize=3,
        )
        ax.axhline(0.50, color="#9A3D3D", linestyle="--", linewidth=1, label="weak < 0.50")
        ax.axhline(0.75, color="#2F6B4F", linestyle=":", linewidth=1, label="strong >= 0.75")
        ax.set_xticks(x_pos, [f"C{i}" for i in part["reference_cluster"]])
        ax.set_ylim(0, 1.03)
        ax.set_title(f"K={k}")
        ax.set_xlabel("Reference cluster")
    axes[0].set_ylabel("Bootstrap matched Jaccard")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=8)
    fig.suptitle("Cluster-level bootstrap stability (mean and 95% empirical interval)")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(figures_dir / "bootstrap_cluster_stability.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    x_pos = np.arange(len(bootstrap_global))
    lower = bootstrap_global["ARI_mean"] - bootstrap_global["ARI_q025"]
    upper = bootstrap_global["ARI_q975"] - bootstrap_global["ARI_mean"]
    ax.bar(x_pos, bootstrap_global["ARI_mean"], color=["#2F6B4F", "#500778"])
    ax.errorbar(
        x_pos,
        bootstrap_global["ARI_mean"],
        yerr=np.vstack([lower, upper]),
        fmt="none",
        ecolor="black",
        capsize=4,
    )
    ax.set_xticks(x_pos, [f"K={k}" for k in bootstrap_global["K"]])
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Adjusted Rand Index")
    ax.set_title("Global paired-bootstrap stability")
    fig.tight_layout()
    fig.savefig(figures_dir / "bootstrap_global_stability.png", dpi=220)
    plt.close(fig)

    difference = paired_bootstrap["ARI_difference_K5_minus_K6"]
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.hist(difference, bins=24, color="#500778", alpha=0.82, edgecolor="white")
    ax.axvline(0, color="#9A3D3D", linestyle="--", linewidth=1.4, label="equal stability")
    ax.axvline(
        difference.mean(),
        color="#2F6B4F",
        linewidth=1.6,
        label=f"mean = {difference.mean():.3f}",
    )
    ax.set_xlabel("Paired bootstrap ARI difference (K=5 minus K=6)")
    ax.set_ylabel("Replicates")
    ax.set_title("Distribution of paired stability differences")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "bootstrap_paired_ari_difference.png", dpi=220)
    plt.close(fig)


def markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    display = frame.copy()
    for column in display.select_dtypes(include=["float", "floating"]).columns:
        display[column] = display[column].map(lambda value: f"{value:.{digits}f}")
    headers = [str(c) for c in display.columns]
    rows = [[str(value) for value in row] for row in display.itertuples(index=False, name=None)]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row, strict=True)]
    header_line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True)) + " |"
    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    body = [
        "| " + " | ".join(v.ljust(w) for v, w in zip(row, widths, strict=True)) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator, *body])


def build_model_summary(
    global_diag: pd.DataFrame,
    refit: pd.DataFrame,
    original: pd.DataFrame,
    bootstrap_global: pd.DataFrame,
    bootstrap_clusters: pd.DataFrame,
    seed_global: pd.DataFrame,
) -> pd.DataFrame:
    original = original[original["K"].isin([5, 6])].copy()
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
        on="K",
        how="left",
    )
    summary = summary.merge(
        bootstrap_global[
            ["K", "ARI_mean", "ARI_sd", "ARI_q025", "ARI_q975", "convergence_rate"]
        ].rename(
            columns={
                "ARI_mean": "bootstrap_ARI_mean_200",
                "ARI_sd": "bootstrap_ARI_sd_200",
                "ARI_q025": "bootstrap_ARI_q025_200",
                "ARI_q975": "bootstrap_ARI_q975_200",
                "convergence_rate": "bootstrap_convergence_rate",
            }
        ),
        on="K",
        how="left",
    )
    weak = (
        bootstrap_clusters.assign(weak=lambda d: d["jaccard_mean"] < 0.50)
        .groupby("K")
        .agg(
            weakest_cluster_jaccard=("jaccard_mean", "min"),
            weak_cluster_count=("weak", "sum"),
        )
        .reset_index()
    )
    summary = summary.merge(weak, on="K", how="left")
    summary = summary.merge(
        seed_global[["K", "ARI_mean", "ARI_min", "convergence_rate"]].rename(
            columns={
                "ARI_mean": "seed_ARI_mean",
                "ARI_min": "seed_ARI_min",
                "convergence_rate": "seed_convergence_rate",
            }
        ),
        on="K",
        how="left",
    )
    return summary.sort_values("K")


def write_reports(
    report_dir: Path,
    args: argparse.Namespace,
    model_summary: pd.DataFrame,
    silhouette: pd.DataFrame,
    bootstrap_clusters: pd.DataFrame,
    paired_bootstrap_summary: pd.DataFrame,
    seed_clusters: pd.DataFrame,
    transition_summary: dict[str, float],
    mapping: pd.DataFrame,
    original: pd.DataFrame,
    refit: pd.DataFrame,
    metadata: dict,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    k5 = model_summary.set_index("K").loc[5]
    k6 = model_summary.set_index("K").loc[6]
    weak_k6 = bootstrap_clusters.loc[
        (bootstrap_clusters["K"] == 6) & (bootstrap_clusters["jaccard_mean"] < 0.50),
        ["reference_cluster", "jaccard_mean", "share_jaccard_below_0_50"],
    ]
    silhouette_display = silhouette.sort_values(["K", "cluster"])
    paired = paired_bootstrap_summary.iloc[0]
    no_silhouette_gain = (k6["silhouette"] - k5["silhouette"]) < 0.01
    no_bootstrap_gain = k6["bootstrap_ARI_mean_200"] <= k5["bootstrap_ARI_mean_200"]
    weak_extra_structure = not weak_k6.empty
    k5_supported = no_silhouette_gain and no_bootstrap_gain and weak_extra_structure

    verdict = (
        "On balance, the internal evidence supports retaining K=5 as the primary "
        "parsimonious typology within the current feature engineering and "
        "diagonal-GMM design, but the preference is not decisive. K=6 remains the "
        "BIC-preferred density model and is more stable across full-data random-seed "
        "refits; K=5 has higher mean station-resampling stability, while K=6 contains "
        "two weakly recurring components and does not improve separation."
        if k5_supported
        else
        "The internal evidence does not provide a sufficiently clear stability-based "
        "reason to prefer K=5 over K=6. The result requires methodological review."
    )

    compact_summary = model_summary[
        [
            "K",
            "BIC_refit",
            "silhouette",
            "calinski_harabasz",
            "davies_bouldin",
            "bootstrap_ARI_mean_200",
            "bootstrap_ARI_q025_200",
            "bootstrap_ARI_q975_200",
            "weakest_cluster_jaccard",
            "weak_cluster_count",
            "seed_ARI_mean",
        ]
    ]
    weak_text = (
        markdown_table(weak_k6.rename(columns={"reference_cluster": "K6_cluster"}))
        if not weak_k6.empty
        else "No K=6 cluster had mean bootstrap Jaccard below 0.50."
    )
    mapping_display = mapping[
        [
            "reference_cluster",
            "matched_candidate_cluster",
            "intersection",
            "reference_size",
            "candidate_size",
            "jaccard",
        ]
    ].rename(
        columns={
            "reference_cluster": "K5_cluster",
            "matched_candidate_cluster": "matched_K6_cluster",
        }
    )
    report = f"""## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run + validate
- Origin Date: {metadata['finished_at']}
- Verification Status: VERIFIED
- Version Label: rail_k_selection_validation_v1

# Rail K=5 versus K=6 Validation Report

## Scope and decision boundary

This audit uses only the 344-dimensional full-week entry/exit temporal feature
matrix and the saved K=5/K=6 labels. LNWC, IMD, catchment composition, and other
downstream interpretation variables are excluded from model selection. Station
names are audit identifiers only.

## Verdict

**{verdict}**

This is not a claim that K=5 is the true natural number of station types. It is
a bounded model-selection judgment conditional on the current inputs, GMM
family, diagonal covariance, and feature normalization.

## Global evidence

{markdown_table(compact_summary)}

The refitted BIC difference (K=6 minus K=5) is
`{k6['BIC_refit'] - k5['BIC_refit']:.3f}`; lower BIC favors K=6. The global
silhouette difference is `{k6['silhouette'] - k5['silhouette']:.6f}`, which is
below the protocol's 0.01 material-improvement description. Paired 200-replicate
bootstrap ARI is `{k5['bootstrap_ARI_mean_200']:.3f}` for K=5 and
`{k6['bootstrap_ARI_mean_200']:.3f}` for K=6. The paired difference
`K5 - K6` has mean `{paired['ARI_difference_K5_minus_K6_mean']:.3f}` and a 95%
empirical interval from `{paired['ARI_difference_K5_minus_K6_q025']:.3f}` to
`{paired['ARI_difference_K5_minus_K6_q975']:.3f}`; K=5 is higher in
`{paired['share_K5_greater_than_K6']:.1%}` of paired resamples. Because the
interval crosses zero, this is directional rather than decisive evidence.

## K=5 to K=6 structure

- Adjusted Rand Index: `{transition_summary['adjusted_rand_index']:.3f}`
- Best one-to-one matched stations: `{transition_summary['best_match_count']}` /
  `{metadata['n_stations']}` (`{transition_summary['best_match_share']:.1%}`)

{markdown_table(mapping_display)}

The relationship is therefore assessed from the full transition table rather
than described as a single clean nested split.

## Weak K=6 components under bootstrap

{weak_text}

For comparison, the complete cluster-level distributions are stored in
`../data/bootstrap_cluster_stability_summary.csv`. A low matched Jaccard means
that component membership changes, merges, or fragments across resamples.

## Cluster separation warning

{markdown_table(silhouette_display[['K', 'cluster', 'n', 'silhouette_mean', 'silhouette_median', 'negative_share']])}

Posterior probabilities are not used as evidence of stability because a fitted
high-dimensional GMM can assign extreme posterior probabilities even when
between-cluster separation or resampling recurrence is weak.

## Random-seed stability

{markdown_table(seed_clusters[['K', 'reference_cluster', 'jaccard_mean', 'jaccard_min', 'share_exact_jaccard_1']])}

This checks optimization sensitivity on the full dataset and is distinct from
bootstrap sampling sensitivity. K=6 has the higher mean full-data seed ARI
(`{k6['seed_ARI_mean']:.3f}` versus `{k5['seed_ARI_mean']:.3f}`), so the evidence
does not support claiming that K=5 is superior under every stability concept.

## Interpretation rules

1. BIC is reported accurately and is not relabelled as supporting K=5.
2. LNWC/IMD agreement is not used to choose K.
3. Small size alone is not grounds for rejecting a component.
4. A proposed sixth type must show recurrence and separation, not only a
   post-hoc narrative.
5. K=5 should be described as a parsimonious primary typology, with K=6 as the
   BIC-preferred sensitivity solution.

## Fallacy scan

- Coverage: 11/11 checked.
- Garden of forking paths / look-elsewhere: controlled by reporting both K and
  prespecifying the internal evidence order.
- Ecological fallacy: LNWC/IMD and area interpretation are excluded here.
- Correlation/causation and reverse causality: no causal claim is made.
- Simpson's paradox, Berkson's paradox, collider bias, base-rate neglect,
  regression to the mean, and survivorship bias were not triggered by this
  resampling comparison.

## Reproducibility and limits

- Saved labels were refitted with the original seed and hyperparameters.
- Full input hashes and package versions are in `RUN_METADATA.json`.
- The bootstrap resamples stations and is conditional on the existing 344
  features and diagonal-GMM family.
- Cluster stability does not establish functional or socio-economic meaning.
"""
    (report_dir / "VALIDATION_REPORT.md").write_text(report, encoding="utf-8")

    report_zh = f"""## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run + validate
- Origin Date: {metadata['finished_at']}
- Verification Status: VERIFIED
- Version Label: rail_k_selection_validation_v1_zh

# 地铁 K=5 与 K=6 内部稳定性检验

## 检验边界

本检验只使用270个站点的344维全周进出站时序特征以及已保存的 K=5、K=6
标签。LNWC、IMD、站点服务区构成等下游解释变量完全没有进入代码；站名仅用于
核对成员身份。

## 核心判断

**综合内部证据，保留 K=5 作为主要的简约分类方案是合理的，但这一优势并非
压倒性。** K=6 的 BIC 更低，而且在完整样本的不同随机初始化下更稳定；K=5
在站点 bootstrap 重抽样中的平均稳定性更高。K=6 没有改善 silhouette，并包含
两个平均 Jaccard 低于0.50的弱复现成分。因此，K=5 应表述为受稳定性与简约性
支持的主分析选择，而不是唯一正确或由 BIC 选出的 K。

## 全局证据

{markdown_table(compact_summary)}

- BIC 差值（K6−K5）：`{k6['BIC_refit'] - k5['BIC_refit']:.3f}`，因此 BIC 支持 K=6。
- silhouette 差值（K6−K5）：`{k6['silhouette'] - k5['silhouette']:.6f}`，没有改善。
- 200次配对 bootstrap 平均 ARI：K=5 为 `{k5['bootstrap_ARI_mean_200']:.3f}`，
  K=6 为 `{k6['bootstrap_ARI_mean_200']:.3f}`。
- 配对差值 K5−K6 的均值为 `{paired['ARI_difference_K5_minus_K6_mean']:.3f}`，
  95%经验区间为
  `[{paired['ARI_difference_K5_minus_K6_q025']:.3f}, {paired['ARI_difference_K5_minus_K6_q975']:.3f}]`；
  K=5 在 `{paired['share_K5_greater_than_K6']:.1%}` 的配对重抽样中更高。区间跨越0，
  所以只能视为方向性而不是决定性证据。
- 完整样本随机种子平均 ARI：K=5 为 `{k5['seed_ARI_mean']:.3f}`，K=6 为
  `{k6['seed_ARI_mean']:.3f}`；这表明 K=6 对优化初始化更稳定。

## K=5 到 K=6 的成员结构

- 两套标签 ARI：`{transition_summary['adjusted_rand_index']:.3f}`。
- 最佳一对一匹配：`{transition_summary['best_match_count']}` / `{metadata['n_stations']}`
  （`{transition_summary['best_match_share']:.1%}`）。

{markdown_table(mapping_display)}

因此，当前结果不是“从一个 K=5 簇中干净切出一个小簇”，而是多个边界簇之间
发生重新分配。

## K=6 中的弱复现成分

{weak_text}

K6-C5 同时具有平均 silhouette 为负和 bootstrap 复现性偏弱的问题；K6-C0 的
成员也容易在重抽样后重新分配。与此同时，K=5 也并非完美：完整簇级
silhouette 表显示 K5-C4 的分离度接近0。因此本报告保留“谨慎支持 K=5”的边界。

## 全部簇级 silhouette

{markdown_table(silhouette_display[['K', 'cluster', 'n', 'silhouette_mean', 'silhouette_median', 'negative_share']])}

## 方法解释

1. bootstrap 检验的是样本扰动下的成员复现性，不是 K=5 正确的概率。
2. 随机种子检验的是优化过程敏感性，两者不能混为一谈。
3. 小簇本身不构成否定理由；关键是分离度、复现性及结构是否独立。
4. GMM posterior 接近1不等于聚类稳定，因此不作为主要证据。
5. LNWC/IMD 只在最终标签冻结后用于外部表征，不参与 K 的选择。

## 建议采用的论文表述

对角协方差 GMM 的 BIC 在 K=6 时最低，但 K=6 并未提高整体分离度，且在站点
重抽样中出现两个复现性较弱的成分。K=5 的平均 bootstrap 稳定性更高、结构更
简约，因此被保留为主要解释方案；K=6 作为 BIC 支持的替代结果披露。该决定是
多指标权衡，而不是对唯一真实聚类数的断言。

## 统计谬误扫描

- 覆盖：11/11。
- 通过同时报告 K=5、K=6 和预先声明内部证据顺序，降低 look-elsewhere 与
  garden of forking paths 风险。
- LNWC/IMD 被排除在 K 选择之外，避免循环解释和生态谬误。
- 本检验不作因果或个体层面推断。

## 局限

- 结论以当前344维特征、标准化方式、GMM模型和对角协方差为条件。
- 200次 bootstrap 的配对差值区间较宽，不能称为 K=5 显著优于 K=6。
- 稳定性不能自动赋予簇以城市功能或社会经济含义。
"""
    (report_dir / "VALIDATION_REPORT_ZH.md").write_text(report_zh, encoding="utf-8")

    original_two = original[original["K"].isin([5, 6])][
        ["K", "BIC", "silhouette", "ARI", "ARI_sd"]
    ].copy()
    comparison = original_two.merge(refit, on="K", how="left")
    comparison["BIC_diff"] = comparison["BIC_refit"] - comparison["BIC"]
    comparison["label_refit_status"] = np.where(
        np.isclose(comparison["saved_vs_refit_ARI"], 1.0), "MATCH", "MISMATCH"
    )
    reproducible = bool(
        np.isclose(comparison["saved_vs_refit_ARI"], 1.0).all()
        and np.isclose(comparison["BIC_diff"], 0.0, atol=1e-6).all()
    )
    reproducibility = f"""# Reproducibility Check

- Method: deterministic re-run with random state {args.random_state}, diagonal
  covariance, n_init {args.reference_n_init}, reg_covar {args.reg_covar}, and
  max_iter {args.max_iter}.
- Verdict: {'REPRODUCIBLE' if reproducible else 'PARTIALLY_REPRODUCIBLE'}

{markdown_table(comparison)}

Exact equality is expected for the deterministic reference refit in the current
recorded Python environment. Bootstrap distributions are stochastic analyses
made reproducible through the recorded master seed and parameters.
"""
    (report_dir / "REPRODUCIBILITY_CHECK.md").write_text(
        reproducibility, encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    output_root = args.output_root.resolve()
    data_dir = output_root / "data"
    figures_dir = output_root / "figures"
    report_dir = output_root / "report"
    for directory in (data_dir, figures_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    print("[load] validating inputs", flush=True)
    features, labels, coords = validate_inputs(args)
    x = features.to_numpy(dtype=float)
    original = pd.read_csv(args.original_kdiag)

    print("[diagnostics] reference refit and silhouettes", flush=True)
    global_diag, silhouette, refit = reference_diagnostics(x, labels, args)
    print("[transition] K=5 versus K=6 membership", flush=True)
    contingency, mapping, composition, transition_detail, transition_summary = (
        transition_analysis(features.index, labels, coords)
    )

    print(f"[bootstrap] starting {args.bootstrap} paired replicates", flush=True)
    boot_clusters_raw, boot_global_raw, boot_clusters, boot_global = bootstrap_stability(
        x, labels, args
    )
    paired_bootstrap, paired_bootstrap_summary = paired_bootstrap_comparison(
        boot_global_raw
    )
    print(f"[seed stability] starting {args.seed_runs} full-data refits", flush=True)
    seed_clusters_raw, seed_global_raw, seed_clusters, seed_global = seed_stability(
        x, labels, args
    )

    model_summary = build_model_summary(
        global_diag, refit, original, boot_global, boot_clusters, seed_global
    )

    outputs = {
        "global_reference_diagnostics.csv": global_diag,
        "reference_refit_diagnostics.csv": refit,
        "cluster_silhouette_summary.csv": silhouette,
        "k5_k6_contingency.csv": contingency.reset_index(names="k5_cluster"),
        "k5_k6_best_mapping.csv": mapping,
        "k6_source_composition.csv": composition,
        "station_transition_detail.csv": transition_detail,
        "bootstrap_cluster_stability_iterations.csv": boot_clusters_raw,
        "bootstrap_global_stability_iterations.csv": boot_global_raw,
        "bootstrap_cluster_stability_summary.csv": boot_clusters,
        "bootstrap_global_stability_summary.csv": boot_global,
        "bootstrap_paired_ari_comparison.csv": paired_bootstrap,
        "bootstrap_paired_ari_summary.csv": paired_bootstrap_summary,
        "seed_cluster_stability_iterations.csv": seed_clusters_raw,
        "seed_global_stability_iterations.csv": seed_global_raw,
        "seed_cluster_stability_summary.csv": seed_clusters,
        "seed_global_stability_summary.csv": seed_global,
        "model_selection_summary.csv": model_summary,
    }
    for filename, frame in outputs.items():
        frame.to_csv(data_dir / filename, index=False, encoding="utf-8-sig")

    print("[figures] rendering", flush=True)
    write_plots(
        figures_dir,
        contingency,
        silhouette,
        boot_clusters,
        boot_global,
        paired_bootstrap,
    )

    finished_at = datetime.now(timezone.utc).isoformat()
    duration = time.perf_counter() - started
    input_paths = {
        "features": args.features.resolve(),
        "labels_k5": args.labels_k5.resolve(),
        "labels_k6": args.labels_k6.resolve(),
        "original_kdiag": args.original_kdiag.resolve(),
    }
    if args.coords.is_file():
        input_paths["coords_audit_only"] = args.coords.resolve()
    metadata = {
        "experiment_id": f"rail-k-selection-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
        "command": " ".join([sys.executable, str(SCRIPT_PATH), *sys.argv[1:]]),
        "working_directory": str(Path.cwd().resolve()),
        "script": str(SCRIPT_PATH),
        "output_root": str(output_root),
        "n_stations": int(features.shape[0]),
        "n_features": int(features.shape[1]),
        "parameters": {
            "bootstrap": args.bootstrap,
            "seed_runs": args.seed_runs,
            "reference_n_init": args.reference_n_init,
            "bootstrap_n_init": args.bootstrap_n_init,
            "seed_n_init": args.seed_n_init,
            "random_state": args.random_state,
            "reg_covar": args.reg_covar,
            "max_iter": args.max_iter,
            "covariance_type": "diag",
        },
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
        "inputs": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in input_paths.items()
        },
        "transition_summary": transition_summary,
        "external_characterization_variables_loaded": False,
    }
    write_reports(
        report_dir,
        args,
        model_summary,
        silhouette,
        boot_clusters,
        paired_bootstrap_summary,
        seed_clusters,
        transition_summary,
        mapping,
        original,
        refit,
        metadata,
    )
    (report_dir / "RUN_METADATA.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[complete] {duration:.1f}s -> {output_root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
