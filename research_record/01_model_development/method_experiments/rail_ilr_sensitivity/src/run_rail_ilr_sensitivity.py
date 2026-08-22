#!/usr/bin/env python
"""Run a side-by-side ILR sensitivity analysis for the full-week Rail typology.

The accepted raw-share pipeline is read-only. Entry and exit are treated as
separate 172-part compositions, zero-handled with an empirical prior (alpha=1),
and expressed in standard Helmert ILR coordinates. The primary comparator keeps
the accepted diagonal-covariance GMM family fixed.
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

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow
import scipy
import sklearn
from scipy.linalg import helmert
from scipy.optimize import linear_sum_assignment
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture


SCRIPT_PATH = Path(__file__).resolve()
WORKSPACE = SCRIPT_PATH.parents[1]
FYP_ROOT = WORKSPACE.parent
SOURCE = FYP_ROOT / "cluster_clean_version_fullweek"
GROUPED = FYP_ROOT / "cluster_clean_version_grouped"

FEATURE_INPUT = SOURCE / "outputs" / "features" / "X_rail.parquet"
META_INPUT = SOURCE / "outputs" / "features" / "rail_meta.csv"
RAW_K5_INPUT = SOURCE / "outputs" / "labels" / "rail_k5_labels.csv"
RAW_K6_INPUT = SOURCE / "outputs" / "labels" / "rail_k6_labels.csv"
RAW_KDIAG_INPUT = SOURCE / "outputs" / "diagnostics" / "rail_kdiag.csv"
COORDS_INPUT = GROUPED / "outputs" / "preprocessed" / "rail_coords.csv"

DIRECTIONS = ("entry", "exit")
DIRECTION_TOTAL_COLUMNS = {"entry": "tot_entry", "exit": "tot_exit"}
DAY_LENGTHS = (28, 28, 44, 44, 28)
DAY_NAMES = ("MON", "TWT", "FRI", "SAT", "SUN")
PARTS_PER_DIRECTION = sum(DAY_LENGTHS)
K_RANGE = tuple(range(2, 13))
STABILITY_KS = tuple(range(3, 9))
COVARIANCES = ("spherical", "diag", "tied", "full")
PRIMARY_COVARIANCE = "diag"
ALPHA = 1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rail ILR compositional sensitivity for the full-week typology."
    )
    parser.add_argument("--output-root", type=Path, default=WORKSPACE / "outputs")
    parser.add_argument("--bootstrap", type=int, default=200)
    parser.add_argument("--seed-runs", type=int, default=20)
    parser.add_argument("--n-init", type=int, default=20)
    parser.add_argument("--bootstrap-n-init", type=int, default=3)
    parser.add_argument("--seed-n-init", type=int, default=20)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--reg-covar", type=float, default=1e-6)
    parser.add_argument("--max-iter", type=int, default=300)
    parser.add_argument("--progress-every", type=int, default=10)
    args = parser.parse_args()
    if args.bootstrap < 1 or args.seed_runs < 1:
        parser.error("--bootstrap and --seed-runs must be at least 1")
    if args.n_init < 1 or args.bootstrap_n_init < 1 or args.seed_n_init < 1:
        parser.error("all n_init values must be at least 1")
    return args


def make_dirs(output_root: Path) -> dict[str, Path]:
    result = {
        "root": output_root.resolve(),
        "features": output_root.resolve() / "features",
        "diagnostics": output_root.resolve() / "diagnostics",
        "labels": output_root.resolve() / "labels",
        "data": output_root.resolve() / "data",
        "figures": output_root.resolve() / "figures",
        "report": output_root.resolve() / "report",
        "models": output_root.resolve() / "models",
    }
    for path in result.values():
        path.mkdir(parents=True, exist_ok=True)
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    if frame.empty:
        return "No rows."
    shown = frame.copy()
    for column in shown.columns:
        if pd.api.types.is_float_dtype(shown[column]):
            shown[column] = shown[column].map(
                lambda value: "" if pd.isna(value) else f"{value:.{digits}f}"
            )
    headers = [str(column) for column in shown.columns]
    rows = [[str(value) for value in row] for row in shown.itertuples(index=False, name=None)]
    widths = [
        max(len(headers[i]), max((len(row[i]) for row in rows), default=0))
        for i in range(len(headers))
    ]

    def render(row: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) + " |"

    return "\n".join(
        [render(headers), render(["-" * width for width in widths]), *[render(row) for row in rows]]
    )


def summarize(values: pd.Series, prefix: str) -> dict[str, float]:
    return {
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_sd": float(values.std(ddof=0)),
        f"{prefix}_median": float(values.median()),
        f"{prefix}_q025": float(values.quantile(0.025)),
        f"{prefix}_q975": float(values.quantile(0.975)),
        f"{prefix}_min": float(values.min()),
        f"{prefix}_max": float(values.max()),
    }


def gmm_parameter_count(k: int, p: int, covariance: str) -> int:
    means = k * p
    weights = k - 1
    covariance_parameters = {
        "spherical": k,
        "diag": k * p,
        "tied": p * (p + 1) // 2,
        "full": k * p * (p + 1) // 2,
    }[covariance]
    return means + weights + covariance_parameters


def fit_gmm(
    x: np.ndarray,
    k: int,
    covariance: str,
    seed: int,
    n_init: int,
    reg_covar: float,
    max_iter: int,
) -> tuple[GaussianMixture, int]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model = GaussianMixture(
            n_components=k,
            covariance_type=covariance,
            n_init=n_init,
            reg_covar=reg_covar,
            max_iter=max_iter,
            random_state=seed,
        ).fit(x)
    count = sum(issubclass(item.category, ConvergenceWarning) for item in caught)
    return model, count


def load_label(path: Path, expected_k: int, units: pd.Index) -> np.ndarray:
    frame = pd.read_csv(path)
    if {"unit", "cluster"}.difference(frame.columns):
        raise ValueError(f"{path} must contain unit and cluster")
    frame["unit"] = frame["unit"].astype(str)
    if frame["unit"].duplicated().any():
        raise ValueError(f"duplicate unit IDs in {path}")
    aligned = frame.set_index("unit").reindex(units)
    if aligned["cluster"].isna().any():
        raise ValueError(f"{path} does not cover the ILR sample")
    labels = aligned["cluster"].to_numpy(dtype=int)
    if sorted(np.unique(labels).tolist()) != list(range(expected_k)):
        raise ValueError(f"{path} does not contain labels 0..{expected_k - 1}")
    return labels


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, dict[int, np.ndarray], pd.DataFrame]:
    required = [
        FEATURE_INPUT,
        META_INPUT,
        RAW_K5_INPUT,
        RAW_K6_INPUT,
        RAW_KDIAG_INPUT,
    ]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)

    raw = pd.read_parquet(FEATURE_INPUT)
    raw.index = raw.index.astype(str)
    if raw.empty or raw.index.duplicated().any():
        raise ValueError("raw Rail feature matrix is empty or has duplicate stations")
    if raw.shape[1] != 2 * PARTS_PER_DIRECTION:
        raise ValueError(f"expected 344 raw features, found {raw.shape[1]}")
    if not np.isfinite(raw.to_numpy(dtype=float)).all() or (raw < 0).any().any():
        raise ValueError("raw Rail feature matrix contains invalid values")

    meta = pd.read_csv(META_INPUT, dtype={"NLC": str}).set_index("NLC").reindex(raw.index)
    if meta[list(DIRECTION_TOTAL_COLUMNS.values())].isna().any().any():
        raise ValueError("rail_meta.csv does not cover every feature row")
    if (meta[list(DIRECTION_TOTAL_COLUMNS.values())] <= 0).any().any():
        raise ValueError("every Rail station must have positive entry and exit totals")

    for direction in DIRECTIONS:
        columns = [column for column in raw.columns if column.startswith(direction + "_")]
        if len(columns) != PARTS_PER_DIRECTION:
            raise ValueError(f"{direction} has {len(columns)} columns, expected 172")
        if not np.allclose(raw[columns].sum(axis=1), 1.0, atol=1e-9):
            raise ValueError(f"{direction} raw shares do not close to 1")
        if (raw[columns].sum(axis=0) <= 0).any():
            raise ValueError(f"{direction} includes an all-zero temporal bin")

    labels = {
        5: load_label(RAW_K5_INPUT, 5, raw.index),
        6: load_label(RAW_K6_INPUT, 6, raw.index),
    }
    if COORDS_INPUT.is_file():
        coords = pd.read_csv(COORDS_INPUT, encoding="utf-8-sig", dtype={"NLC": str})
        keep = [column for column in ["NLC", "Station", "Fare Zone", "lon", "lat"] if column in coords]
        coords = coords[keep].drop_duplicates("NLC").set_index("NLC")
    else:
        coords = pd.DataFrame(index=raw.index)
    return raw, meta, labels, coords


def write_manifest(dirs: dict[str, Path]) -> pd.DataFrame:
    paths = {
        "raw_share_features": FEATURE_INPUT,
        "direction_totals": META_INPUT,
        "raw_k5_labels": RAW_K5_INPUT,
        "raw_k6_labels": RAW_K6_INPUT,
        "raw_k_diagnostics": RAW_KDIAG_INPUT,
        "station_identifiers_optional": COORDS_INPUT,
        "analysis_script": SCRIPT_PATH,
    }
    rows = []
    for role, path in paths.items():
        exists = path.is_file()
        rows.append(
            {
                "role": role,
                "path": str(path.resolve()),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else np.nan,
                "sha256": sha256_file(path) if exists else "",
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(dirs["root"] / "input_manifest.csv", index=False, encoding="utf-8-sig")
    return result


def build_ilr_features(
    raw: pd.DataFrame,
    meta: pd.DataFrame,
    dirs: dict[str, Path],
    seed: int,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    basis = helmert(PARTS_PER_DIRECTION, full=False)
    if basis.shape != (PARTS_PER_DIRECTION - 1, PARTS_PER_DIRECTION):
        raise ValueError(f"unexpected Helmert basis shape: {basis.shape}")
    if not np.allclose(basis @ basis.T, np.eye(PARTS_PER_DIRECTION - 1), atol=1e-12):
        raise ValueError("Helmert rows are not orthonormal")
    if not np.allclose(basis @ np.ones(PARTS_PER_DIRECTION), 0.0, atol=1e-12):
        raise ValueError("Helmert basis is not orthogonal to closure")
    pd.DataFrame(
        basis,
        index=[f"balance_{i:03d}" for i in range(1, PARTS_PER_DIRECTION)],
        columns=[f"part_{i:03d}" for i in range(1, PARTS_PER_DIRECTION + 1)],
    ).to_csv(dirs["data"] / "helmert_ilr_basis_172.csv", encoding="utf-8-sig")

    ilr_blocks: list[pd.DataFrame] = []
    clr_blocks: list[np.ndarray] = []
    closure_errors: list[float] = []
    raw_recovery_errors: list[float] = []
    minimum_posterior = np.inf
    zero_cells = 0
    for direction in DIRECTIONS:
        columns = [column for column in raw.columns if column.startswith(direction + "_")]
        shares = raw[columns].to_numpy(dtype=float)
        totals = meta[DIRECTION_TOTAL_COLUMNS[direction]].to_numpy(dtype=float)
        counts = shares * totals[:, None]
        prior = counts.sum(axis=0) / counts.sum()
        posterior = (counts + ALPHA * prior) / (totals[:, None] + ALPHA)
        if not np.all(posterior > 0):
            raise ValueError(f"non-positive posterior share in {direction}")
        logp = np.log(posterior)
        clr = logp - logp.mean(axis=1, keepdims=True)
        ilr = logp @ basis.T
        ilr_blocks.append(
            pd.DataFrame(
                ilr,
                index=raw.index,
                columns=[f"{direction}_ilr_{i:03d}" for i in range(1, PARTS_PER_DIRECTION)],
            )
        )
        clr_blocks.append(clr)
        closure_errors.append(float(np.max(np.abs(posterior.sum(axis=1) - 1.0))))
        recovered = counts / totals[:, None]
        raw_recovery_errors.append(float(np.max(np.abs(recovered - shares))))
        minimum_posterior = min(minimum_posterior, float(posterior.min()))
        zero_cells += int((shares == 0).sum())

    ilr_frame = pd.concat(ilr_blocks, axis=1)
    ilr_frame.to_parquet(dirs["features"] / "X_rail_fullweek_ilr342.parquet")

    ilr_values = ilr_frame.to_numpy(dtype=float)
    clr_values = np.concatenate(clr_blocks, axis=1)
    rng = np.random.default_rng(seed)
    left = rng.integers(0, len(raw), size=20_000)
    right = rng.integers(0, len(raw), size=20_000)
    clr_distance = np.linalg.norm(clr_values[left] - clr_values[right], axis=1)
    ilr_distance = np.linalg.norm(ilr_values[left] - ilr_values[right], axis=1)
    centered_rank = int(np.linalg.matrix_rank(ilr_values - ilr_values.mean(axis=0, keepdims=True)))
    audit: dict[str, float | int] = {
        "n_stations": int(raw.shape[0]),
        "raw_share_columns": int(raw.shape[1]),
        "parts_per_direction": PARTS_PER_DIRECTION,
        "ilr_columns": int(ilr_frame.shape[1]),
        "centered_sample_rank": centered_rank,
        "pseudocount_alpha": ALPHA,
        "raw_zero_cell_count": zero_cells,
        "minimum_posterior_share": minimum_posterior,
        "max_closure_error": max(closure_errors),
        "max_raw_share_recovery_error": max(raw_recovery_errors),
        "max_sampled_distance_error_clr_vs_ilr": float(
            np.max(np.abs(clr_distance - ilr_distance))
        ),
    }
    if audit["max_sampled_distance_error_clr_vs_ilr"] > 1e-9:
        raise ValueError(f"ILR distance preservation failed: {audit}")
    (dirs["diagnostics"] / "ilr_coordinate_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    return ilr_frame, audit


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
    for left in range(reference_k):
        left_mask = reference == left
        for right in range(candidate_k):
            right_mask = candidate == right
            intersection = int(np.logical_and(left_mask, right_mask).sum())
            union = int(np.logical_or(left_mask, right_mask).sum())
            counts[left, right] = intersection
            jaccard[left, right] = intersection / union if union else 0.0
            recall[left, right] = intersection / left_mask.sum() if left_mask.sum() else 0.0
            precision[left, right] = intersection / right_mask.sum() if right_mask.sum() else 0.0
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
    row_index, column_index = linear_sum_assignment(-score)
    rows = []
    for left, right in zip(row_index, column_index, strict=True):
        rows.append(
            {
                "reference_cluster": int(left),
                "matched_candidate_cluster": int(right),
                "intersection": int(counts[left, right]),
                "reference_size": int((reference == left).sum()),
                "candidate_size": int((candidate == right).sum()),
                "jaccard": float(jaccard[left, right]),
                "recall": float(recall[left, right]),
                "precision": float(precision[left, right]),
            }
        )
    return pd.DataFrame(rows).sort_values("reference_cluster"), counts


def run_bic_grid(
    x: np.ndarray,
    args: argparse.Namespace,
    dirs: dict[str, Path],
) -> pd.DataFrame:
    rows = []
    p = x.shape[1]
    for covariance in COVARIANCES:
        for k in K_RANGE:
            started = time.perf_counter()
            try:
                model, warning_count = fit_gmm(
                    x,
                    k,
                    covariance,
                    args.random_state,
                    args.n_init,
                    args.reg_covar,
                    args.max_iter,
                )
                labels = model.predict(x)
                sizes = np.bincount(labels, minlength=k)
                error = ""
                bic = float(model.bic(x))
                aic = float(model.aic(x))
                converged = bool(model.converged_)
                n_iter = int(model.n_iter_)
                min_cluster_n = int(sizes.min())
            except Exception as exc:  # preserve failed grid cells for audit
                warning_count = 0
                error = f"{type(exc).__name__}: {exc}"
                bic = np.nan
                aic = np.nan
                converged = False
                n_iter = 0
                min_cluster_n = 0
            parameter_count = gmm_parameter_count(k, p, covariance)
            rows.append(
                {
                    "covariance": covariance,
                    "K": k,
                    "BIC": bic,
                    "AIC": aic,
                    "converged": converged,
                    "n_iter": n_iter,
                    "convergence_warnings": warning_count,
                    "fit_seconds": time.perf_counter() - started,
                    "min_cluster_n": min_cluster_n,
                    "min_cluster_share": min_cluster_n / len(x),
                    "parameter_count": parameter_count,
                    "parameters_per_station": parameter_count / len(x),
                    "full_covariance_underidentified": bool(
                        covariance == "full" and min_cluster_n <= p
                    ),
                    "error": error,
                }
            )
            partial = pd.DataFrame(rows)
            partial.to_csv(
                dirs["diagnostics"] / "ilr_bic_grid.partial.csv",
                index=False,
                encoding="utf-8-sig",
            )
            print(
                f"[grid] {covariance:9s} K={k:2d} BIC={bic:.1f} "
                f"min_n={min_cluster_n} time={rows[-1]['fit_seconds']:.1f}s",
                flush=True,
            )
    result = pd.DataFrame(rows)
    result.to_csv(dirs["diagnostics"] / "ilr_bic_grid.csv", index=False, encoding="utf-8-sig")
    return result


def fit_primary_models(
    x: np.ndarray,
    units: pd.Index,
    args: argparse.Namespace,
    dirs: dict[str, Path],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[int, np.ndarray]]:
    rows = []
    cluster_rows = []
    labels_by_k: dict[int, np.ndarray] = {}
    for k in K_RANGE:
        model, warning_count = fit_gmm(
            x,
            k,
            PRIMARY_COVARIANCE,
            args.random_state,
            args.n_init,
            args.reg_covar,
            args.max_iter,
        )
        labels = model.predict(x)
        posterior = model.predict_proba(x)
        labels_by_k[k] = labels
        sizes = np.bincount(labels, minlength=k)
        sil_samples = silhouette_samples(x, labels)
        rows.append(
            {
                "K": k,
                "covariance": PRIMARY_COVARIANCE,
                "BIC": float(model.bic(x)),
                "AIC": float(model.aic(x)),
                "silhouette": float(silhouette_score(x, labels)),
                "calinski_harabasz": float(calinski_harabasz_score(x, labels)),
                "davies_bouldin": float(davies_bouldin_score(x, labels)),
                "min_cluster_n": int(sizes.min()),
                "max_cluster_n": int(sizes.max()),
                "min_cluster_share": float(sizes.min() / len(x)),
                "converged": bool(model.converged_),
                "n_iter": int(model.n_iter_),
                "convergence_warnings": warning_count,
            }
        )
        for cluster in range(k):
            values = pd.Series(sil_samples[labels == cluster])
            cluster_rows.append(
                {
                    "K": k,
                    "cluster": cluster,
                    "n": int(len(values)),
                    **summarize(values, "silhouette"),
                    "negative_silhouette_share": float((values < 0).mean()),
                }
            )
        entropy = -np.where(posterior > 0, posterior * np.log(posterior), 0.0).sum(axis=1)
        pd.DataFrame(
            {
                "unit": units,
                "cluster": labels,
                "max_posterior": posterior.max(axis=1),
                "entropy": entropy,
            }
        ).to_csv(dirs["labels"] / f"ilr_k{k}_labels.csv", index=False, encoding="utf-8-sig")
        print(
            f"[primary] K={k:2d} sil={rows[-1]['silhouette']:.3f} "
            f"DB={rows[-1]['davies_bouldin']:.3f} min_n={sizes.min()}",
            flush=True,
        )
    diagnostics = pd.DataFrame(rows)
    diagnostics["delta_BIC_within_diag"] = diagnostics["BIC"] - diagnostics["BIC"].min()
    clusters = pd.DataFrame(cluster_rows)
    diagnostics.to_csv(dirs["diagnostics"] / "ilr_kdiag_internal.csv", index=False, encoding="utf-8-sig")
    clusters.to_csv(dirs["diagnostics"] / "cluster_silhouette_summary.csv", index=False, encoding="utf-8-sig")
    return diagnostics, clusters, labels_by_k


def bootstrap_stability(
    x: np.ndarray,
    labels_by_k: dict[int, np.ndarray],
    args: argparse.Namespace,
    dirs: dict[str, Path],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(args.random_state)
    plan = [
        (
            rng.choice(len(x), len(x), replace=True),
            int(rng.integers(0, 2**31 - 1)),
        )
        for _ in range(args.bootstrap)
    ]
    global_rows = []
    cluster_rows = []
    for iteration, (sample_index, base_seed) in enumerate(plan, start=1):
        for k in STABILITY_KS:
            model, warning_count = fit_gmm(
                x[sample_index],
                k,
                PRIMARY_COVARIANCE,
                base_seed + k,
                args.bootstrap_n_init,
                args.reg_covar,
                args.max_iter,
            )
            predicted = model.predict(x)
            mapping, _ = match_clusters(labels_by_k[k], predicted, k, k, objective="jaccard")
            global_rows.append(
                {
                    "iteration": iteration,
                    "K": k,
                    "sample_unique_n": int(np.unique(sample_index).size),
                    "model_seed": base_seed + k,
                    "ARI": float(adjusted_rand_score(labels_by_k[k], predicted)),
                    "converged": bool(model.converged_),
                    "n_iter": int(model.n_iter_),
                    "convergence_warnings": warning_count,
                }
            )
            for row in mapping.itertuples(index=False):
                cluster_rows.append(
                    {
                        "iteration": iteration,
                        "K": k,
                        "reference_cluster": row.reference_cluster,
                        "matched_candidate_cluster": row.matched_candidate_cluster,
                        "jaccard": row.jaccard,
                        "recall": row.recall,
                        "precision": row.precision,
                    }
                )
        if iteration % args.progress_every == 0 or iteration == args.bootstrap:
            pd.DataFrame(global_rows).to_csv(
                dirs["diagnostics"] / "bootstrap_global_iterations.partial.csv",
                index=False,
                encoding="utf-8-sig",
            )
            print(f"[bootstrap] {iteration}/{args.bootstrap}", flush=True)

    globals_frame = pd.DataFrame(global_rows)
    clusters_frame = pd.DataFrame(cluster_rows)
    global_summary_rows = []
    for k, group in globals_frame.groupby("K", sort=True):
        global_summary_rows.append(
            {
                "K": int(k),
                "replicates": int(len(group)),
                **summarize(group["ARI"], "ARI"),
                "convergence_rate": float(group["converged"].mean()),
                "total_convergence_warnings": int(group["convergence_warnings"].sum()),
            }
        )
    cluster_summary_rows = []
    for (k, cluster), group in clusters_frame.groupby(["K", "reference_cluster"], sort=True):
        cluster_summary_rows.append(
            {
                "K": int(k),
                "reference_cluster": int(cluster),
                "replicates": int(len(group)),
                **summarize(group["jaccard"], "jaccard"),
                **summarize(group["recall"], "recall"),
                **summarize(group["precision"], "precision"),
                "share_jaccard_below_0_50": float((group["jaccard"] < 0.50).mean()),
                "share_jaccard_at_least_0_75": float((group["jaccard"] >= 0.75).mean()),
            }
        )
    global_summary = pd.DataFrame(global_summary_rows)
    cluster_summary = pd.DataFrame(cluster_summary_rows)
    globals_frame.to_csv(dirs["diagnostics"] / "bootstrap_global_iterations.csv", index=False, encoding="utf-8-sig")
    clusters_frame.to_csv(dirs["diagnostics"] / "bootstrap_cluster_iterations.csv", index=False, encoding="utf-8-sig")
    global_summary.to_csv(dirs["diagnostics"] / "bootstrap_global_summary.csv", index=False, encoding="utf-8-sig")
    cluster_summary.to_csv(dirs["diagnostics"] / "bootstrap_cluster_summary.csv", index=False, encoding="utf-8-sig")
    return globals_frame, clusters_frame, global_summary, cluster_summary


def seed_stability(
    x: np.ndarray,
    labels_by_k: dict[int, np.ndarray],
    args: argparse.Namespace,
    dirs: dict[str, Path],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for run in range(1, args.seed_runs + 1):
        seed = args.random_state + 10_000 + run
        for k in STABILITY_KS:
            model, warning_count = fit_gmm(
                x,
                k,
                PRIMARY_COVARIANCE,
                seed,
                args.seed_n_init,
                args.reg_covar,
                args.max_iter,
            )
            predicted = model.predict(x)
            mapping, _ = match_clusters(labels_by_k[k], predicted, k, k, objective="jaccard")
            rows.append(
                {
                    "run": run,
                    "seed": seed,
                    "K": k,
                    "ARI": float(adjusted_rand_score(labels_by_k[k], predicted)),
                    "minimum_matched_cluster_jaccard": float(mapping["jaccard"].min()),
                    "BIC": float(model.bic(x)),
                    "converged": bool(model.converged_),
                    "n_iter": int(model.n_iter_),
                    "convergence_warnings": warning_count,
                }
            )
        if run % max(1, min(args.progress_every, 5)) == 0 or run == args.seed_runs:
            print(f"[seed stability] {run}/{args.seed_runs}", flush=True)

    detail = pd.DataFrame(rows)
    summary_rows = []
    for k, group in detail.groupby("K", sort=True):
        summary_rows.append(
            {
                "K": int(k),
                "runs": int(len(group)),
                **summarize(group["ARI"], "ARI"),
                **summarize(group["minimum_matched_cluster_jaccard"], "min_jaccard"),
                **summarize(group["BIC"], "BIC"),
                "convergence_rate": float(group["converged"].mean()),
                "total_convergence_warnings": int(group["convergence_warnings"].sum()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    detail.to_csv(dirs["diagnostics"] / "seed_stability_iterations.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(dirs["diagnostics"] / "seed_stability_summary.csv", index=False, encoding="utf-8-sig")
    return detail, summary


def compare_raw_references(
    units: pd.Index,
    raw_labels: dict[int, np.ndarray],
    labels_by_k: dict[int, np.ndarray],
    coords: pd.DataFrame,
    dirs: dict[str, Path],
) -> tuple[pd.DataFrame, dict[int, pd.DataFrame], dict[int, np.ndarray], pd.DataFrame]:
    rows = []
    for raw_k, raw_values in raw_labels.items():
        for ilr_k, ilr_values in labels_by_k.items():
            row = {
                "raw_K": raw_k,
                "ilr_K": ilr_k,
                "ARI": float(adjusted_rand_score(raw_values, ilr_values)),
                "NMI": float(normalized_mutual_info_score(raw_values, ilr_values)),
            }
            if raw_k == ilr_k:
                mapping, _ = match_clusters(raw_values, ilr_values, raw_k, ilr_k, objective="counts")
                row["best_match_count"] = int(mapping["intersection"].sum())
                row["best_match_share"] = float(mapping["intersection"].sum() / len(units))
                row["weakest_matched_cluster_jaccard"] = float(mapping["jaccard"].min())
            rows.append(row)
    comparison = pd.DataFrame(rows)
    comparison.to_csv(dirs["diagnostics"] / "raw_reference_comparison.csv", index=False, encoding="utf-8-sig")

    mappings: dict[int, pd.DataFrame] = {}
    contingencies: dict[int, np.ndarray] = {}
    for k in (5, 6):
        mapping, contingency = match_clusters(
            raw_labels[k], labels_by_k[k], k, k, objective="counts"
        )
        mappings[k] = mapping
        contingencies[k] = contingency
        mapping.to_csv(dirs["data"] / f"raw_vs_ilr_k{k}_best_mapping.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(
            contingency,
            index=[f"raw_C{i}" for i in range(k)],
            columns=[f"ilr_C{i}" for i in range(k)],
        ).reset_index(names="raw_cluster").to_csv(
            dirs["data"] / f"raw_vs_ilr_k{k}_contingency.csv", index=False, encoding="utf-8-sig"
        )

    map_k5 = dict(
        zip(
            mappings[5]["reference_cluster"],
            mappings[5]["matched_candidate_cluster"],
            strict=True,
        )
    )
    transition = pd.DataFrame(
        {
            "unit": units,
            "raw_k5": raw_labels[5],
            "ilr_k5": labels_by_k[5],
            "raw_k6": raw_labels[6],
            "ilr_k6": labels_by_k[6],
        }
    ).set_index("unit")
    transition = transition.join(coords, how="left")
    transition["best_matched_ilr_for_raw_k5"] = transition["raw_k5"].map(map_k5)
    transition["follows_k5_best_match"] = (
        transition["ilr_k5"] == transition["best_matched_ilr_for_raw_k5"]
    )
    transition = transition.reset_index()
    transition.to_csv(dirs["data"] / "station_transition_detail.csv", index=False, encoding="utf-8-sig")
    return comparison, mappings, contingencies, transition


def merge_diagnostics(
    internal: pd.DataFrame,
    bootstrap_global: pd.DataFrame,
    bootstrap_cluster: pd.DataFrame,
    seed_summary: pd.DataFrame,
    dirs: dict[str, Path],
) -> pd.DataFrame:
    weakest = (
        bootstrap_cluster.groupby("K", as_index=False)["jaccard_mean"]
        .min()
        .rename(columns={"jaccard_mean": "bootstrap_weakest_cluster_jaccard"})
    )
    result = internal.merge(
        bootstrap_global[["K", "ARI_mean", "ARI_q025", "ARI_q975"]].rename(
            columns={
                "ARI_mean": "bootstrap_ARI_mean",
                "ARI_q025": "bootstrap_ARI_q025",
                "ARI_q975": "bootstrap_ARI_q975",
            }
        ),
        on="K",
        how="left",
    ).merge(weakest, on="K", how="left")
    result = result.merge(
        seed_summary[["K", "ARI_mean", "ARI_min", "min_jaccard_mean"]].rename(
            columns={
                "ARI_mean": "seed_ARI_mean",
                "ARI_min": "seed_ARI_min",
                "min_jaccard_mean": "seed_min_jaccard_mean",
            }
        ),
        on="K",
        how="left",
    )
    result.to_csv(dirs["diagnostics"] / "ilr_kdiag.csv", index=False, encoding="utf-8-sig")
    return result


def plot_profiles(raw: pd.DataFrame, labels: np.ndarray, k: int, output: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    colors = plt.cm.tab10(np.linspace(0, 1, k))
    boundaries = np.cumsum((0, *DAY_LENGTHS))
    centers = [(boundaries[i] + boundaries[i + 1] - 1) / 2 for i in range(len(DAY_NAMES))]
    for axis, direction in zip(axes, DIRECTIONS, strict=True):
        columns = [column for column in raw.columns if column.startswith(direction + "_")]
        values = raw[columns].to_numpy(dtype=float)
        for cluster in range(k):
            axis.plot(values[labels == cluster].mean(axis=0), color=colors[cluster], label=f"C{cluster}")
        for boundary in boundaries[1:-1]:
            axis.axvline(boundary - 0.5, color="#999999", linewidth=0.8, alpha=0.6)
        axis.set_ylabel("Mean weekly share")
        axis.set_title(direction.capitalize())
        axis.grid(alpha=0.2)
        axis.legend(ncol=min(k, 6), fontsize=8)
    axes[-1].set_xticks(centers, DAY_NAMES)
    axes[-1].set_xlabel("Native day-type blocks; profiles shown in original share space")
    fig.suptitle(f"Rail ILR K={k}: mean raw temporal profiles")
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)


def write_plots(
    raw: pd.DataFrame,
    grid: pd.DataFrame,
    diagnostics: pd.DataFrame,
    bootstrap_global: pd.DataFrame,
    labels_by_k: dict[int, np.ndarray],
    contingencies: dict[int, np.ndarray],
    dirs: dict[str, Path],
) -> None:
    fig, axis = plt.subplots(figsize=(9, 5.5))
    for covariance in COVARIANCES:
        part = grid[(grid["covariance"] == covariance) & grid["BIC"].notna()]
        axis.plot(part["K"], part["BIC"], marker="o", label=covariance)
    axis.set(xlabel="K", ylabel="BIC", title="Rail ILR: covariance-family BIC grid")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(dirs["figures"] / "ilr_bic_grid.png", dpi=220)
    plt.close(fig)

    subset = diagnostics[diagnostics["K"].isin(STABILITY_KS)].copy()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].plot(subset["K"], subset["BIC"], marker="o")
    axes[0, 0].set_title("Diagonal GMM BIC")
    axes[0, 1].plot(subset["K"], subset["silhouette"], marker="o", label="silhouette")
    axes[0, 1].set_title("Silhouette")
    axes[1, 0].plot(subset["K"], subset["bootstrap_ARI_mean"], marker="o")
    axes[1, 0].set_title("Bootstrap mean ARI")
    axes[1, 1].plot(subset["K"], subset["bootstrap_weakest_cluster_jaccard"], marker="o")
    axes[1, 1].axhline(0.5, color="#9A3D3D", linestyle="--", linewidth=1)
    axes[1, 1].set_title("Weakest cluster mean Jaccard")
    for axis in axes.ravel():
        axis.set_xlabel("K")
        axis.grid(alpha=0.25)
    fig.suptitle("Rail ILR internal diagnostics (primary diagonal family)")
    fig.tight_layout()
    fig.savefig(dirs["figures"] / "ilr_k_diagnostics.png", dpi=220)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8, 5))
    axis.bar(bootstrap_global["K"].astype(str), bootstrap_global["ARI_mean"], color="#500778")
    lower = bootstrap_global["ARI_mean"] - bootstrap_global["ARI_q025"]
    upper = bootstrap_global["ARI_q975"] - bootstrap_global["ARI_mean"]
    axis.errorbar(
        bootstrap_global["K"].astype(str),
        bootstrap_global["ARI_mean"],
        yerr=np.vstack([lower, upper]),
        fmt="none",
        ecolor="black",
        capsize=3,
    )
    axis.set(xlabel="K", ylabel="ARI", title="Rail ILR station-bootstrap stability")
    axis.set_ylim(0, 1)
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(dirs["figures"] / "bootstrap_global_stability.png", dpi=220)
    plt.close(fig)

    for k in (5, 6):
        counts = contingencies[k]
        fig, axis = plt.subplots(figsize=(6.5, 5.5))
        image = axis.imshow(counts, cmap="Purples")
        for row in range(k):
            for column in range(k):
                axis.text(column, row, str(counts[row, column]), ha="center", va="center")
        axis.set_xticks(range(k), [f"ILR C{i}" for i in range(k)], rotation=45, ha="right")
        axis.set_yticks(range(k), [f"Raw C{i}" for i in range(k)])
        axis.set_title(f"Raw-share versus ILR K={k}")
        fig.colorbar(image, ax=axis, label="Stations")
        fig.tight_layout()
        fig.savefig(dirs["figures"] / f"raw_vs_ilr_k{k}_heatmap.png", dpi=220)
        plt.close(fig)
        plot_profiles(raw, labels_by_k[k], k, dirs["figures"] / f"ilr_k{k}_raw_profiles.png")


def family_bic_summary(grid: pd.DataFrame) -> pd.DataFrame:
    valid = grid.dropna(subset=["BIC"])
    rows = []
    for covariance, group in valid.groupby("covariance", sort=False):
        best = group.loc[group["BIC"].idxmin()]
        rows.append(
            {
                "covariance": covariance,
                "best_K": int(best["K"]),
                "best_BIC": float(best["BIC"]),
                "min_cluster_n": int(best["min_cluster_n"]),
                "parameters_per_station": float(best["parameters_per_station"]),
                "full_covariance_underidentified": bool(best["full_covariance_underidentified"]),
            }
        )
    return pd.DataFrame(rows)


def write_reports(
    dirs: dict[str, Path],
    finished_at: str,
    audit: dict[str, float | int],
    grid: pd.DataFrame,
    diagnostics: pd.DataFrame,
    bootstrap_cluster: pd.DataFrame,
    seed_summary: pd.DataFrame,
    comparison: pd.DataFrame,
    mappings: dict[int, pd.DataFrame],
) -> dict[str, str | float | int | bool]:
    same_k = comparison[
        ((comparison["raw_K"] == 5) & (comparison["ilr_K"] == 5))
        | ((comparison["raw_K"] == 6) & (comparison["ilr_K"] == 6))
    ].copy()
    k5_compare = same_k[(same_k["raw_K"] == 5) & (same_k["ilr_K"] == 5)].iloc[0]
    k5_diag = diagnostics.set_index("K").loc[5]
    k5_clusters = bootstrap_cluster[bootstrap_cluster["K"] == 5]
    weakest_bootstrap = float(k5_clusters["jaccard_mean"].min())
    strong_agreement = bool(
        k5_compare["ARI"] >= 0.80
        and k5_compare["NMI"] >= 0.80
        and k5_compare["best_match_share"] >= 0.85
        and k5_compare["weakest_matched_cluster_jaccard"] >= 0.50
    )
    partial_agreement = bool(k5_compare["ARI"] >= 0.65)
    acceptable_recurrence = bool(
        k5_diag["bootstrap_ARI_mean"] >= 0.60 and weakest_bootstrap >= 0.50
    )
    if strong_agreement and acceptable_recurrence:
        status = "SUPPORTED"
        verdict_en = (
            "The Rail K=5 typology is robust to the prespecified ILR compositional "
            "sensitivity under the fixed diagonal-GMM comparison."
        )
        verdict_zh = (
            "在预设的 diagonal-GMM 对照下，Rail K=5 分类对 ILR 组成数据处理具有较强稳健性。"
        )
    elif partial_agreement and acceptable_recurrence:
        status = "PARTIALLY_SUPPORTED"
        verdict_en = (
            "The ILR result partially supports the Rail K=5 typology: the solution "
            "recurs internally, but membership agreement with the raw-share K=5 is not strong."
        )
        verdict_zh = (
            "ILR 结果对 Rail K=5 提供部分支持：内部复现性可接受，但与原始比例 K=5 的成员一致性未达到强稳健标准。"
        )
    else:
        status = "CHALLENGED"
        verdict_en = (
            "The current Rail K=5 typology is materially sensitive to the ILR "
            "compositional treatment and should not yet be frozen for downstream interpretation."
        )
        verdict_zh = (
            "当前 Rail K=5 对 ILR 组成数据处理存在实质敏感性，在进入下游解释前不应直接冻结标签。"
        )

    family_summary = family_bic_summary(grid)
    display_diag = diagnostics[diagnostics["K"].isin(STABILITY_KS)][
        [
            "K",
            "BIC",
            "delta_BIC_within_diag",
            "silhouette",
            "davies_bouldin",
            "min_cluster_n",
            "bootstrap_ARI_mean",
            "bootstrap_ARI_q025",
            "bootstrap_ARI_q975",
            "bootstrap_weakest_cluster_jaccard",
            "seed_ARI_mean",
        ]
    ]
    k5_cluster_display = k5_clusters[
        [
            "reference_cluster",
            "jaccard_mean",
            "jaccard_q025",
            "jaccard_q975",
            "share_jaccard_below_0_50",
        ]
    ]
    mapping_display = mappings[5][
        [
            "reference_cluster",
            "matched_candidate_cluster",
            "intersection",
            "reference_size",
            "candidate_size",
            "jaccard",
            "recall",
            "precision",
        ]
    ].rename(
        columns={
            "reference_cluster": "raw_cluster",
            "matched_candidate_cluster": "ilr_cluster",
        }
    )
    best_diag_k = int(diagnostics.loc[diagnostics["BIC"].idxmin(), "K"])
    best_silhouette_k = int(
        diagnostics[diagnostics["K"].isin(STABILITY_KS)].loc[
            diagnostics[diagnostics["K"].isin(STABILITY_KS)]["silhouette"].idxmax(), "K"
        ]
    )
    best_bootstrap_k = int(
        diagnostics.dropna(subset=["bootstrap_ARI_mean"]).loc[
            diagnostics.dropna(subset=["bootstrap_ARI_mean"])["bootstrap_ARI_mean"].idxmax(), "K"
        ]
    )
    result_summary: dict[str, str | float | int | bool] = {
        "verdict_status": status,
        "raw_vs_ilr_k5_ARI": float(k5_compare["ARI"]),
        "raw_vs_ilr_k5_NMI": float(k5_compare["NMI"]),
        "raw_vs_ilr_k5_best_match_share": float(k5_compare["best_match_share"]),
        "raw_vs_ilr_k5_weakest_jaccard": float(k5_compare["weakest_matched_cluster_jaccard"]),
        "ilr_k5_bootstrap_ARI_mean": float(k5_diag["bootstrap_ARI_mean"]),
        "ilr_k5_bootstrap_weakest_cluster_jaccard": weakest_bootstrap,
        "strong_label_agreement": strong_agreement,
        "acceptable_internal_recurrence": acceptable_recurrence,
        "diag_BIC_best_K": best_diag_k,
        "stability_range_best_silhouette_K": best_silhouette_k,
        "stability_range_best_bootstrap_ARI_K": best_bootstrap_k,
    }

    report_en = f"""## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run + validate
- Origin Date: {finished_at}
- Verification Status: ANALYZED
- Version Label: rail_ilr_sensitivity_v1

# Rail ILR compositional sensitivity

## Verdict

**{verdict_en}**

This is a bounded sensitivity judgment, not evidence that K=5 is a true natural
number of station types.

## Coordinate audit

The same 270 stations and 344 raw-share columns were used. Entry and exit were
handled as separate 172-part compositions with empirical-prior alpha=1, yielding
342 Helmert ILR coordinates. The centered sample rank is
`{audit['centered_sample_rank']}`. The maximum sampled CLR-versus-ILR distance
error is `{audit['max_sampled_distance_error_clr_vs_ilr']:.3e}`.

## Direct raw versus ILR label agreement

{markdown_table(same_k[['raw_K', 'ilr_K', 'ARI', 'NMI', 'best_match_share', 'weakest_matched_cluster_jaccard']])}

### Raw K=5 to ILR K=5 matching

{markdown_table(mapping_display)}

## Internal ILR diagnostics: fixed diagonal family

{markdown_table(display_diag)}

Within the ILR diagonal family, BIC is lowest at K={best_diag_k}. Within K=3-8,
silhouette is highest at K={best_silhouette_k}, and bootstrap mean ARI is highest
at K={best_bootstrap_k}. These metrics answer different questions and are not
collapsed into a claim of one true K.

## ILR K=5 cluster recurrence

{markdown_table(k5_cluster_display)}

The ILR K=5 mean global bootstrap ARI is
`{k5_diag['bootstrap_ARI_mean']:.3f}` with empirical 95% interval
`[{k5_diag['bootstrap_ARI_q025']:.3f}, {k5_diag['bootstrap_ARI_q975']:.3f}]`.

## Secondary covariance-family BIC grid

{markdown_table(family_summary)}

The diagonal family remains primary because it holds the accepted Rail GMM
assumption fixed. Full-covariance fits are structurally under-identified here
when component size does not exceed the 342 fitted dimensions, even though
regularization can return a numerical fit.

## Interpretation boundaries

1. Absolute BIC values are not compared against the 344-column raw-share fit.
2. ILR changes geometry and zero handling but adds no new passenger information.
3. LNWC, IMD, geography, station volume, and service variables were excluded.
4. Stability and label agreement do not establish functional or causal meaning.

## Fallacy scan

- Coverage: 11/11 checked.
- Garden of forking paths and look-elsewhere risk are reduced by the prespecified
  K range, fixed primary covariance, explicit thresholds, and complete K=3-8
  stability reporting.
- Ecological fallacy is not used because no area or individual inference is made.
- No causal or reverse-causal claim is made.
- Simpson's paradox, Berkson's paradox, collider bias, base-rate neglect,
  regression to the mean, and survivorship bias were not triggered by this
  clustering sensitivity design.

## Reproducibility status

The run is seed-controlled and records input hashes, package versions, and all
parameters in `RUN_METADATA.json`. A separate deterministic re-run comparison is
required before changing the Material Passport status from ANALYZED to VERIFIED.
"""
    (dirs["report"] / "VALIDATION_REPORT.md").write_text(report_en, encoding="utf-8")

    report_zh = f"""## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run + validate
- Origin Date: {finished_at}
- Verification Status: ANALYZED
- Version Label: rail_ilr_sensitivity_v1_zh

# Rail ILR 组成数据敏感性检验

## 核心结论

**{verdict_zh}**

这是一项有边界的敏感性判断，并不意味着 K=5 是唯一真实或自然存在的站点类型数。

## 坐标与样本核验

- 样本保持为同一批 270 个 Underground 站点；
- 原始特征仍对应 344 个全周比例变量，entry 与 exit 各 172 个；
- 两个方向分别使用经验先验 `alpha=1` 处理零值，再各转为 171 个标准 Helmert ILR 坐标；
- 最终拟合维度为 342，中心化样本秩为 `{audit['centered_sample_rank']}`；
- CLR/Aitchison 距离与 ILR 欧氏距离的最大抽样误差为 `{audit['max_sampled_distance_error_clr_vs_ilr']:.3e}`；
- 原始零值单元格共 `{audit['raw_zero_cell_count']}` 个，处理后最小比例为 `{audit['minimum_posterior_share']:.3e}`。

## 原始比例标签与 ILR 标签的直接一致性

{markdown_table(same_k[['raw_K', 'ilr_K', 'ARI', 'NMI', 'best_match_share', 'weakest_matched_cluster_jaccard']])}

### raw K=5 与 ILR K=5 的最佳簇匹配

{markdown_table(mapping_display)}

强稳健性的预设标准要求 ARI、NMI、最佳匹配比例分别至少为 0.80、0.80、0.85，
且最弱匹配簇 Jaccard 不低于 0.50。本次标签一致性判定为：
`{'达到强稳健标准' if strong_agreement else '未达到强稳健标准'}`。

## ILR 内部诊断：固定 diagonal 协方差

{markdown_table(display_diag)}

- ILR diagonal 家族内 BIC 最低的是 K={best_diag_k}；
- K=3-8 范围内 silhouette 最高的是 K={best_silhouette_k}；
- K=3-8 范围内 bootstrap 平均 ARI 最高的是 K={best_bootstrap_k}。

这些指标分别回答模型拟合、几何分离和重抽样复现问题，不能合并解释为发现了唯一真实 K。

## ILR K=5 的逐簇 bootstrap 复现性

{markdown_table(k5_cluster_display)}

ILR K=5 的全局 bootstrap 平均 ARI 为 `{k5_diag['bootstrap_ARI_mean']:.3f}`，
95%经验区间为 `[{k5_diag['bootstrap_ARI_q025']:.3f}, {k5_diag['bootstrap_ARI_q975']:.3f}]`；
最弱簇平均 Jaccard 为 `{weakest_bootstrap:.3f}`。按照预设规则，内部复现性
`{'达到可接受标准' if acceptable_recurrence else '未达到可接受标准'}`。

## 四类协方差 BIC 网格（次级诊断）

{markdown_table(family_summary)}

diagonal 仍作为主检验，是因为它固定了当前 Rail 分析的协方差假设。342 维特征下，
如果 full-covariance 成分的成员数不超过特征维度，其协方差在结构上无法由该成分样本
充分识别；即使正则化使模型数值上可拟合，也不应仅凭其 BIC 替换主检验。

## 对论文论述的边界

1. 不比较 raw-share 344 维拟合与 ILR 342 维拟合的绝对 BIC。
2. ILR 改变了比例数据的几何表达和零值处理，但没有加入新的乘客信息。
3. LNWC、IMD、地理位置、客流规模及服务供给均未参与模型选择。
4. 标签一致性与 bootstrap 稳定性不能自动赋予簇以功能、社会经济或因果含义。

## 统计谬误扫描

- 覆盖：11/11。
- 通过预先固定 K 范围、主协方差、判据和完整披露 K=3-8，降低了 look-elsewhere 与 garden of forking paths 风险。
- 未进行面积到个体的推断，因此没有使用生态谬误式解释。
- 本检验不提出因果或反向因果结论。
- Simpson's paradox、Berkson's paradox、collider bias、base-rate neglect、
  regression to the mean 与 survivorship bias 未被本聚类敏感性设计触发。

## 可复现性状态

本次运行固定随机种子，并在 `RUN_METADATA.json` 中记录输入哈希、软件版本与参数。
在完成独立输出目录下的确定性复跑比较前，本报告状态保持为 `ANALYZED`。
"""
    (dirs["report"] / "VALIDATION_REPORT_ZH.md").write_text(report_zh, encoding="utf-8")
    return result_summary


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    dirs = make_dirs(args.output_root)
    log_path = dirs["root"] / "run.log"
    log_path.write_text("", encoding="utf-8")

    def log(message: str) -> None:
        print(message, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    log("[1/9] Loading fixed Rail inputs")
    raw, meta, raw_labels, coords = load_inputs()
    manifest = write_manifest(dirs)
    log(f"      stations={len(raw)}, raw_features={raw.shape[1]}")

    log("[2/9] Building empirical-prior Helmert ILR coordinates")
    ilr, audit = build_ilr_features(raw, meta, dirs, args.random_state)
    x = ilr.to_numpy(dtype=float)
    log(
        f"      ILR shape={ilr.shape}, centered_rank={audit['centered_sample_rank']}, "
        f"distance_error={audit['max_sampled_distance_error_clr_vs_ilr']:.3e}"
    )

    log("[3/9] Running four-covariance BIC grid")
    grid = run_bic_grid(x, args, dirs)

    log("[4/9] Fitting primary diagonal-GMM K=2..12")
    internal, cluster_silhouette, labels_by_k = fit_primary_models(
        x, ilr.index, args, dirs
    )

    log(f"[5/9] Running {args.bootstrap} paired station bootstraps for K=3..8")
    _, _, bootstrap_global, bootstrap_cluster = bootstrap_stability(
        x, labels_by_k, args, dirs
    )

    log(f"[6/9] Running {args.seed_runs} full-data seed refits for K=3..8")
    _, seed_summary = seed_stability(x, labels_by_k, args, dirs)

    log("[7/9] Comparing raw-share and ILR labels")
    comparison, mappings, contingencies, transition = compare_raw_references(
        ilr.index, raw_labels, labels_by_k, coords, dirs
    )
    diagnostics = merge_diagnostics(
        internal, bootstrap_global, bootstrap_cluster, seed_summary, dirs
    )

    log("[8/9] Rendering figures and validation reports")
    write_plots(
        raw,
        grid,
        diagnostics,
        bootstrap_global,
        labels_by_k,
        contingencies,
        dirs,
    )
    finished_at = datetime.now(timezone.utc).isoformat()
    result_summary = write_reports(
        dirs,
        finished_at,
        audit,
        grid,
        diagnostics,
        bootstrap_cluster,
        seed_summary,
        comparison,
        mappings,
    )

    duration = time.perf_counter() - started
    metadata = {
        "experiment_id": f"rail-ilr-sensitivity-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
        "command": " ".join([sys.executable, str(SCRIPT_PATH), *sys.argv[1:]]),
        "working_directory": str(Path.cwd().resolve()),
        "script": str(SCRIPT_PATH),
        "output_root": str(dirs["root"]),
        "parameters": {
            "bootstrap": args.bootstrap,
            "seed_runs": args.seed_runs,
            "n_init": args.n_init,
            "bootstrap_n_init": args.bootstrap_n_init,
            "seed_n_init": args.seed_n_init,
            "random_state": args.random_state,
            "reg_covar": args.reg_covar,
            "max_iter": args.max_iter,
            "primary_covariance": PRIMARY_COVARIANCE,
            "covariance_grid": list(COVARIANCES),
            "K_range": list(K_RANGE),
            "stability_Ks": list(STABILITY_KS),
            "empirical_prior_alpha": ALPHA,
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
            row.role: {
                "path": row.path,
                "sha256": row.sha256,
                "size_bytes": None if pd.isna(row.size_bytes) else int(row.size_bytes),
            }
            for row in manifest.itertuples(index=False)
            if row.exists
        },
        "coordinate_audit": audit,
        "result_summary": result_summary,
        "external_characterization_variables_loaded": False,
        "raw_pipeline_modified": False,
    }
    (dirs["report"] / "RUN_METADATA.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"[9/9] Complete in {duration:.1f}s -> {dirs['root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
