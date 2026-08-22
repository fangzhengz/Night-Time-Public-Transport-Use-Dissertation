from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn import __version__ as sklearn_version
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fit_gmm(
    X: np.ndarray,
    k: int,
    covariance: str,
    seed: int,
    n_init: int,
) -> tuple[GaussianMixture, list[str], float]:
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model = GaussianMixture(
            n_components=k,
            covariance_type=covariance,
            n_init=n_init,
            reg_covar=C.REG_COVAR,
            max_iter=C.MAX_ITER,
            random_state=seed,
        ).fit(X)
    messages = [str(item.message) for item in caught]
    return model, messages, time.perf_counter() - started


def input_manifest(paths: list[tuple[str, Path]]) -> pd.DataFrame:
    rows = []
    for role, path in paths:
        rows.append(
            {
                "role": role,
                "path": str(path.resolve()),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else np.nan,
                "sha256": sha256(path) if path.exists() else "",
                "modified": path.stat().st_mtime if path.exists() else np.nan,
            }
        )
    return pd.DataFrame(rows)


def validate_long(long: pd.DataFrame) -> None:
    required = {"day_type", "direction", "lsoa", "hour_bin", "count"}
    missing = required.difference(long.columns)
    if missing:
        raise ValueError(f"Long input is missing columns: {sorted(missing)}")
    bad_days = set(long["day_type"].dropna().unique()).difference(C.DAY_TYPES)
    bad_directions = set(long["direction"].dropna().unique()).difference(C.DIRECTIONS)
    bad_hours = set(long["hour_bin"].dropna().astype(int).unique()).difference(C.HOURS)
    if bad_days or bad_directions or bad_hours:
        raise ValueError(
            f"Unexpected domains: day_types={bad_days}, directions={bad_directions}, hours={bad_hours}"
        )
    if long["count"].isna().any() or (long["count"] < 0).any():
        raise ValueError("Counts contain missing or negative values")


def build_features(alpha: float, min_total: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    log("[1/7] Reading and validating hub-first long table")
    long = pd.read_parquet(C.LONG_INPUT)
    validate_long(long)
    long = long.copy()
    long["lsoa"] = long["lsoa"].astype(str)
    long["hour_bin"] = long["hour_bin"].astype(int)

    exceptions = pd.read_csv(C.EXCEPTION_INPUT)
    exception_lsoas = set(exceptions["lsoa"].astype(str).unique())
    full_totals = long.groupby("lsoa", observed=True)["count"].sum().rename("total_activity")
    eligible_before_exception = set(full_totals.index[full_totals >= min_total].astype(str))
    keep = sorted(eligible_before_exception.difference(exception_lsoas))
    if not keep:
        raise ValueError("No LSOAs remain after filtering")

    grouped = (
        long.groupby(["lsoa", "day_type", "direction", "hour_bin"], as_index=False, observed=True)["count"]
        .sum()
    )
    features: list[pd.DataFrame] = []
    meta = pd.DataFrame(index=pd.Index(keep, name="lsoa"))
    meta["total_activity"] = full_totals.reindex(keep).astype(float)
    audits = []

    for direction in C.DIRECTIONS:
        day_parts = []
        for day_type in C.DAY_TYPES:
            sub = grouped[
                (grouped["day_type"] == day_type) & (grouped["direction"] == direction)
            ]
            wide = sub.pivot_table(
                index="lsoa", columns="hour_bin", values="count", aggfunc="sum", fill_value=0.0
            )
            wide = wide.reindex(index=keep, columns=C.HOURS, fill_value=0.0).astype(float)
            day_total = wide.sum(axis=1)
            meta[f"tot_{direction}_{day_type}"] = day_total
            wide.columns = pd.MultiIndex.from_product([[day_type], C.HOURS], names=["day_type", "hour_bin"])
            day_parts.append(wide)

        weekly_counts = pd.concat(day_parts, axis=1)
        direction_total = weekly_counts.sum(axis=1)
        grand_total = float(direction_total.sum())
        if grand_total <= 0:
            raise ValueError(f"Direction {direction} has no activity")
        prior = weekly_counts.sum(axis=0) / grand_total
        if not np.isclose(float(prior.sum()), 1.0, atol=1e-12):
            raise ValueError(f"Full-week prior does not sum to one for {direction}")
        posterior = weekly_counts.add(alpha * prior, axis=1).div(direction_total + alpha, axis=0)
        posterior.columns = [
            f"{direction}_{day_type}_{int(hour)}" for day_type, hour in posterior.columns
        ]
        if not np.allclose(posterior.sum(axis=1).to_numpy(), 1.0, atol=1e-10):
            raise ValueError(f"Posterior full-week vector does not sum to one: {direction}")

        raw_share = weekly_counts.div(direction_total.replace(0, np.nan), axis=0)
        tv = 0.5 * np.abs(raw_share.to_numpy() - posterior.to_numpy()).sum(axis=1)
        tv[direction_total.to_numpy() == 0] = np.nan
        peak_day, peak_hour = prior.idxmax()
        meta[f"tot_{direction}"] = direction_total
        meta[f"tv_{direction}"] = tv
        features.append(posterior)
        audits.append(
            {
                "direction": direction,
                "n_lsoa": len(keep),
                "n_raw_zero_total": int((direction_total == 0).sum()),
                "prior_peak_day": str(peak_day),
                "prior_peak_hour": int(peak_hour),
                "prior_peak_share": float(prior.max()),
                "median_raw_total": float(direction_total.median()),
                "p05_raw_total": float(direction_total.quantile(0.05)),
                "median_tv_nonzero": float(np.nanmedian(tv)),
                "p95_tv_nonzero": float(np.nanquantile(tv, 0.95)),
            }
        )

    X = pd.concat(features, axis=1)
    if X.shape[1] != 72:
        raise ValueError(f"Expected 72 features, got {X.shape[1]}")
    if not np.isfinite(X.to_numpy()).all():
        raise ValueError("Feature matrix contains non-finite values")
    if not np.allclose(X.sum(axis=1).to_numpy(), 2.0, atol=1e-10):
        raise ValueError("Every full-week row must sum to two separately-normalised directions")

    excluded = pd.DataFrame(
        {
            "lsoa": sorted(set(full_totals.index.astype(str)).difference(keep)),
        }
    )
    excluded["total_activity"] = excluded["lsoa"].map(full_totals)
    excluded["is_exception_union"] = excluded["lsoa"].isin(exception_lsoas)
    excluded["below_fullweek_min_total"] = excluded["total_activity"] < min_total
    excluded["reason"] = np.select(
        [
            excluded["is_exception_union"] & excluded["below_fullweek_min_total"],
            excluded["is_exception_union"],
            excluded["below_fullweek_min_total"],
        ],
        ["exception_and_below_min_total", "one_direction_exception", "below_min_total"],
        default="not_eligible",
    )

    summary = {
        "alpha": alpha,
        "min_total": min_total,
        "n_input_lsoas": int(long["lsoa"].nunique()),
        "n_fullweek_total_ge_min": len(eligible_before_exception),
        "n_exception_union": len(exception_lsoas),
        "n_exception_union_ge_min": len(exception_lsoas.intersection(eligible_before_exception)),
        "n_retained": len(keep),
        "n_features": X.shape[1],
        "feature_row_sum_min": float(X.sum(axis=1).min()),
        "feature_row_sum_max": float(X.sum(axis=1).max()),
    }
    pd.DataFrame(audits).to_csv(C.DIAGNOSTICS / "feature_block_audit.csv", index=False)
    X.to_parquet(C.FEATURES / "X_bus_fullweek_alpha5.parquet")
    meta.to_csv(C.FEATURES / "bus_fullweek_meta_alpha5.csv")
    excluded.to_csv(C.FEATURES / "excluded_lsoas.csv", index=False)
    (C.FEATURES / "feature_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    log(f"      Built X={X.shape}; retained={len(keep)}; row sum=2; exceptions kept out")
    return X, meta, pd.DataFrame(audits), summary


def cluster_size_metrics(labels: np.ndarray, k: int) -> dict:
    counts = np.bincount(labels, minlength=k)
    return {
        "min_cluster_n": int(counts.min()),
        "min_cluster_share": float(counts.min() / counts.sum()),
        "max_cluster_n": int(counts.max()),
        "max_cluster_share": float(counts.max() / counts.sum()),
        "sizes_desc": json.dumps(sorted(counts.tolist(), reverse=True)),
    }


def run_bic_grid(X: np.ndarray) -> tuple[pd.DataFrame, str, int]:
    log("[2/7] Running one full-week GMM BIC grid (4 covariance families x K=2..12)")
    rows = []
    for covariance in C.COVARIANCES:
        for k in C.K_RANGE:
            row = {"covariance": covariance, "K": k}
            try:
                model, warning_messages, seconds = fit_gmm(
                    X, k, covariance, C.RANDOM_STATE, C.N_INIT
                )
                labels = model.predict(X)
                row.update(
                    {
                        "BIC": float(model.bic(X)),
                        "AIC": float(model.aic(X)),
                        "converged": bool(model.converged_),
                        "n_iter": int(model.n_iter_),
                        "fit_seconds": seconds,
                        "warnings": " | ".join(warning_messages),
                        "error": "",
                        **cluster_size_metrics(labels, k),
                    }
                )
                log(
                    f"      {covariance:9s} K={k:2d} BIC={row['BIC']:.1f} "
                    f"min_n={row['min_cluster_n']:4d} converged={row['converged']} ({seconds:.1f}s)"
                )
            except Exception as exc:
                row.update(
                    {
                        "BIC": np.nan,
                        "AIC": np.nan,
                        "converged": False,
                        "n_iter": np.nan,
                        "fit_seconds": np.nan,
                        "warnings": "",
                        "error": repr(exc),
                        "min_cluster_n": np.nan,
                        "min_cluster_share": np.nan,
                        "max_cluster_n": np.nan,
                        "max_cluster_share": np.nan,
                        "sizes_desc": "",
                    }
                )
                log(f"      FAILED {covariance} K={k}: {exc!r}")
            rows.append(row)
            pd.DataFrame(rows).to_csv(C.DIAGNOSTICS / "bus_fullweek_bic_grid.partial.csv", index=False)

    grid = pd.DataFrame(rows)
    grid.to_csv(C.DIAGNOSTICS / "bus_fullweek_bic_grid.csv", index=False)
    ok = grid.dropna(subset=["BIC"])
    if ok.empty:
        raise RuntimeError("Every GMM in the BIC grid failed")
    best = ok.loc[ok["BIC"].idxmin()]
    return grid, str(best["covariance"]), int(best["K"])


def matched_jaccard(base: np.ndarray, other: np.ndarray, k: int) -> np.ndarray:
    contingency = np.zeros((k, k), dtype=int)
    for left, right in zip(base, other):
        contingency[int(left), int(right)] += 1
    base_sizes = contingency.sum(axis=1, keepdims=True)
    other_sizes = contingency.sum(axis=0, keepdims=True)
    union = base_sizes + other_sizes - contingency
    scores = np.divide(contingency, union, out=np.zeros_like(contingency, dtype=float), where=union > 0)
    rows, cols = linear_sum_assignment(-scores)
    matched = np.zeros(k, dtype=float)
    matched[rows] = scores[rows, cols]
    return matched


def run_k_diagnostics(
    X_df: pd.DataFrame,
    meta: pd.DataFrame,
    best_covariance: str,
    bootstrap_n: int,
) -> tuple[pd.DataFrame, dict[int, np.ndarray], dict[int, GaussianMixture], pd.DataFrame]:
    log(f"[3/7] Refitting K diagnostics at BIC-best covariance={best_covariance}")
    X = X_df.to_numpy(dtype=float)
    rng = np.random.default_rng(C.RANDOM_STATE)
    sample_idx = rng.choice(len(X), size=min(2000, len(X)), replace=False)
    rows = []
    labels_by_k: dict[int, np.ndarray] = {}
    models_by_k: dict[int, GaussianMixture] = {}
    profile_rows = []
    summary_rows = []

    for k in C.K_RANGE:
        model, warning_messages, seconds = fit_gmm(X, k, best_covariance, C.RANDOM_STATE, C.N_INIT)
        labels = model.predict(X)
        posterior = model.predict_proba(X)
        log_posterior = np.zeros_like(posterior)
        np.log(posterior, out=log_posterior, where=posterior > 0)
        entropy = -(posterior * log_posterior).sum(axis=1)
        size_metrics = cluster_size_metrics(labels, k)
        row = {
            "K": k,
            "covariance": best_covariance,
            "BIC": float(model.bic(X)),
            "AIC": float(model.aic(X)),
            "silhouette": float(silhouette_score(X[sample_idx], labels[sample_idx])),
            "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
            "davies_bouldin": float(davies_bouldin_score(X, labels)),
            "median_max_posterior": float(np.median(posterior.max(axis=1))),
            "p10_max_posterior": float(np.quantile(posterior.max(axis=1), 0.10)),
            "median_normalized_entropy": float(np.median(entropy / math.log(k))),
            "converged": bool(model.converged_),
            "n_iter": int(model.n_iter_),
            "fit_seconds": seconds,
            "warnings": " | ".join(warning_messages),
            **size_metrics,
        }
        rows.append(row)
        labels_by_k[k] = labels
        if k in C.PROFILE_K:
            models_by_k[k] = model
        pd.DataFrame(
            {
                "unit": X_df.index.astype(str),
                "cluster": labels,
                "max_posterior": posterior.max(axis=1),
                "normalized_entropy": entropy / math.log(k),
            }
        ).to_csv(C.LABELS / f"bus_fullweek_k{k}_labels.csv", index=False)

        for cluster in range(k):
            mask = labels == cluster
            means = X_df.loc[mask].mean(axis=0)
            for feature, value in means.items():
                stem, hour = feature.rsplit("_", 1)
                direction, day_type = stem.split("_", 1)
                profile_rows.append(
                    {
                        "K": k,
                        "cluster": cluster,
                        "day_type": day_type,
                        "direction": direction,
                        "hour_bin": int(hour),
                        "mean_share": float(value),
                    }
                )
            summary_rows.append(
                {
                    "K": k,
                    "cluster": cluster,
                    "n": int(mask.sum()),
                    "share": float(mask.mean()),
                    "median_total_activity": float(meta.loc[mask, "total_activity"].median()),
                    "median_max_posterior": float(np.median(posterior[mask].max(axis=1))),
                }
            )
        log(
            f"      K={k:2d} sil={row['silhouette']:.3f} min_n={row['min_cluster_n']:4d} "
            f"median_p={row['median_max_posterior']:.3f} ({seconds:.1f}s)"
        )

    kdiag = pd.DataFrame(rows)
    profiles = pd.DataFrame(profile_rows)
    cluster_summary = pd.DataFrame(summary_rows)
    kdiag.to_csv(C.DIAGNOSTICS / "bus_fullweek_kdiag_prebootstrap.csv", index=False)
    profiles.to_csv(C.DIAGNOSTICS / "bus_fullweek_cluster_profiles.csv", index=False)
    cluster_summary.to_csv(C.DIAGNOSTICS / "bus_fullweek_cluster_summary.csv", index=False)

    log(f"[4/7] Bootstrap stability for K={C.PROFILE_K} with {bootstrap_n} resamples")
    bootstrap_rows = []
    cluster_recovery_rows = []
    for k in C.PROFILE_K:
        base = labels_by_k[k]
        for replicate in range(bootstrap_n):
            idx = rng.choice(len(X), size=len(X), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model, warning_messages, seconds = fit_gmm(
                X[idx], k, best_covariance, seed, C.BOOTSTRAP_N_INIT
            )
            other = model.predict(X)
            matched = matched_jaccard(base, other, k)
            bootstrap_rows.append(
                {
                    "K": k,
                    "replicate": replicate + 1,
                    "seed": seed,
                    "ARI": float(adjusted_rand_score(base, other)),
                    "mean_matched_cluster_jaccard": float(matched.mean()),
                    "min_matched_cluster_jaccard": float(matched.min()),
                    "fit_seconds": seconds,
                    "converged": bool(model.converged_),
                    "warnings": " | ".join(warning_messages),
                }
            )
            for cluster, score in enumerate(matched):
                cluster_recovery_rows.append(
                    {
                        "K": k,
                        "replicate": replicate + 1,
                        "base_cluster": cluster,
                        "matched_jaccard": float(score),
                    }
                )
        done = pd.DataFrame(bootstrap_rows)
        sub = done[done["K"] == k]
        log(
            f"      K={k}: ARI mean={sub['ARI'].mean():.3f}; "
            f"minimum-cluster Jaccard mean={sub['min_matched_cluster_jaccard'].mean():.3f}"
        )
        done.to_csv(C.DIAGNOSTICS / "bus_fullweek_bootstrap.partial.csv", index=False)

    bootstrap = pd.DataFrame(bootstrap_rows)
    recovery = pd.DataFrame(cluster_recovery_rows)
    bootstrap.to_csv(C.DIAGNOSTICS / "bus_fullweek_bootstrap.csv", index=False)
    recovery.to_csv(C.DIAGNOSTICS / "bus_fullweek_bootstrap_cluster_recovery.csv", index=False)
    boot_summary = (
        bootstrap.groupby("K", as_index=False)
        .agg(
            bootstrap_ari_mean=("ARI", "mean"),
            bootstrap_ari_sd=("ARI", "std"),
            bootstrap_ari_p05=("ARI", lambda x: x.quantile(0.05)),
            bootstrap_mean_cluster_jaccard=("mean_matched_cluster_jaccard", "mean"),
            bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
            bootstrap_min_cluster_jaccard_p05=("min_matched_cluster_jaccard", lambda x: x.quantile(0.05)),
        )
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")
    kdiag.to_csv(C.DIAGNOSTICS / "bus_fullweek_kdiag.csv", index=False)
    return kdiag, labels_by_k, models_by_k, profiles


def adjacent_k_diagnostic(labels_by_k: dict[int, np.ndarray]) -> pd.DataFrame:
    rows = []
    for k in C.K_RANGE[:-1]:
        parent = labels_by_k[k]
        child = labels_by_k[k + 1]
        table = pd.crosstab(pd.Series(parent, name="parent"), pd.Series(child, name="child"))
        assigned_parent = table.idxmax(axis=0)
        weighted_child_purity = float(table.max(axis=0).sum() / table.to_numpy().sum())
        child_sizes = table.sum(axis=0)
        assigned_counts = assigned_parent.value_counts()
        rows.append(
            {
                "K_parent": k,
                "K_child": k + 1,
                "ARI_adjacent": float(adjusted_rand_score(parent, child)),
                "weighted_child_to_parent_purity": weighted_child_purity,
                "n_parent_clusters_receiving_multiple_children": int((assigned_counts > 1).sum()),
                "smallest_child_n": int(child_sizes.min()),
                "smallest_child_share": float(child_sizes.min() / child_sizes.sum()),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(C.DIAGNOSTICS / "bus_fullweek_adjacent_k.csv", index=False)
    return out


def compare_old(labels_by_k: dict[int, np.ndarray], units: pd.Index) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for k in C.PROFILE_K:
        old_path = C.OLD_FULLWEEK / "outputs" / "labels" / f"bus_k{k}_labels.csv"
        if not old_path.exists():
            continue
        old = pd.read_csv(old_path).set_index("unit")
        old.index = old.index.astype(str)
        new = pd.Series(labels_by_k[k], index=units.astype(str), name="new_cluster")
        common = old.index.intersection(new.index)
        rows.append(
            {
                "K": k,
                "n_old": len(old),
                "n_new": len(new),
                "n_common": len(common),
                "old_new_ARI_on_common": float(
                    adjusted_rand_score(old.loc[common, "cluster"], new.loc[common])
                ),
            }
        )
    comparison = pd.DataFrame(rows)
    comparison.to_csv(C.DIAGNOSTICS / "old_vs_new_same_k.csv", index=False)

    summaries = []
    old_grid_path = C.OLD_FULLWEEK / "outputs" / "diagnostics" / "bus_bic_grid.csv"
    if old_grid_path.exists():
        old_grid = pd.read_csv(old_grid_path).dropna(subset=["BIC"])
        old_best = old_grid.loc[old_grid["BIC"].idxmin()]
        summaries.append(
            {
                "version": "old_fullweek_direct_lsoa_raw_share",
                "n_lsoa": int(pd.read_parquet(C.OLD_FULLWEEK / "outputs" / "features" / "X_bus.parquet").shape[0]),
                "n_features": 72,
                "BIC_best_covariance": old_best["covariance"],
                "BIC_best_K": int(old_best["K"]),
                "BIC": float(old_best["BIC"]),
            }
        )
    summary = pd.DataFrame(summaries)
    return comparison, summary


def make_figures(
    grid: pd.DataFrame,
    kdiag: pd.DataFrame,
    profiles: pd.DataFrame,
    labels_by_k: dict[int, np.ndarray],
    units: pd.Index,
) -> None:
    log("[5/7] Writing diagnostic figures, profiles, and maps")
    fig, ax = plt.subplots(figsize=(8, 5))
    for covariance in C.COVARIANCES:
        sub = grid[grid["covariance"] == covariance]
        ax.plot(sub["K"], sub["BIC"], marker="o", label=covariance)
    ax.set(xlabel="K", ylabel="BIC (lower is better)", title="Hub-first full-week bus GMM: BIC grid")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(C.FIGURES / "bic_grid.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    panels = [
        ("silhouette", "Silhouette", "higher is better"),
        ("min_cluster_share", "Smallest cluster share", "avoid tiny-cluster solutions"),
        ("bootstrap_ari_mean", "Bootstrap ARI", "global stability"),
        ("bootstrap_min_cluster_jaccard_mean", "Minimum-cluster Jaccard", "small-cluster recovery"),
    ]
    for ax, (column, title, subtitle) in zip(axes.flat, panels):
        ax.plot(kdiag["K"], kdiag[column], marker="o")
        ax.set_title(f"{title}\n{subtitle}")
        ax.set_xlabel("K")
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(C.FIGURES / "k_diagnostics.png", dpi=180)
    plt.close(fig)

    for k in C.PROFILE_K:
        sub = profiles[profiles["K"] == k]
        sizes = pd.read_csv(C.DIAGNOSTICS / "bus_fullweek_cluster_summary.csv")
        sizes = sizes[sizes["K"] == k].set_index("cluster")["n"]
        fig, axes = plt.subplots(k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True)
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            for column, day_type in enumerate(C.DAY_TYPES):
                ax = axes[cluster, column]
                cell = sub[(sub["cluster"] == cluster) & (sub["day_type"] == day_type)]
                for direction, color in [("boardings", "#4C78A8"), ("alightings", "#F58518")]:
                    line = cell[cell["direction"] == direction].sort_values("hour_bin")
                    ax.plot(range(12), line["mean_share"], marker="o", markersize=2, color=color, label=direction)
                if cluster == 0:
                    ax.set_title(day_type)
                if column == 0:
                    ax.set_ylabel(f"C{cluster} (n={int(sizes.loc[cluster])})")
                ax.grid(alpha=0.2)
        axes[-1, 1].set_xticks(range(12), ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"], rotation=45)
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(f"Hub-first full-week bus mean temporal profiles, K={k}", y=1.002)
        fig.tight_layout()
        fig.savefig(C.FIGURES / f"profiles_k{k}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    try:
        import geopandas as gpd

        boundaries = gpd.read_file(C.LSOA_GEOJSON)[["LSOA21CD", "geometry"]]
        for k in C.PROFILE_K:
            label_frame = pd.DataFrame(
                {"LSOA21CD": units.astype(str), "cluster": labels_by_k[k].astype(int)}
            )
            mapped = boundaries.merge(label_frame, on="LSOA21CD", how="left")
            fig, ax = plt.subplots(figsize=(8, 8))
            mapped.plot(ax=ax, column="cluster", categorical=True, cmap="tab20", linewidth=0.0, missing_kwds={"color": "#eeeeee"})
            ax.set_axis_off()
            ax.set_title(f"Hub-first full-week bus clusters, K={k}")
            fig.tight_layout()
            fig.savefig(C.FIGURES / f"map_k{k}.png", dpi=180)
            plt.close(fig)
    except Exception as exc:
        (C.FIGURES / "MAP_ERROR.txt").write_text(repr(exc), encoding="utf-8")


def write_report(
    feature_summary: dict,
    block_audit: pd.DataFrame,
    grid: pd.DataFrame,
    best_covariance: str,
    best_k: int,
    kdiag: pd.DataFrame,
    adjacent: pd.DataFrame,
    old_compare: pd.DataFrame,
    old_summary: pd.DataFrame,
    bootstrap_n: int,
) -> None:
    best_by_cov = (
        grid.dropna(subset=["BIC"])
        .sort_values("BIC")
        .groupby("covariance", as_index=False)
        .first()[["covariance", "K", "BIC", "min_cluster_n", "min_cluster_share", "converged"]]
    )
    selected = kdiag[kdiag["K"] == best_k].iloc[0]
    flags = []
    if selected["min_cluster_share"] < 0.01:
        flags.append("The BIC-best solution contains a cluster below 1% of the retained sample.")
    if selected["silhouette"] < 0.05:
        flags.append("The BIC-best silhouette is below 0.05, indicating weak geometric separation.")
    if pd.notna(selected.get("bootstrap_ari_mean")) and selected["bootstrap_ari_mean"] >= 0.8 and selected["bootstrap_min_cluster_jaccard_mean"] < 0.6:
        flags.append("Global bootstrap ARI is high while the weakest cluster has low Jaccard recovery: pseudo-reliability warning.")
    if not flags:
        flags.append("No automatic red flag threshold was crossed; this still does not select a final K by itself.")

    old_text = old_summary.to_markdown(index=False) if not old_summary.empty else "Historical summary unavailable."
    compare_text = old_compare.to_markdown(index=False) if not old_compare.empty else "Historical like-K labels unavailable."
    report = f"""# First-pass results: hub-first full-week bus reclustering

## Verdict scope

This run fits **one full-week bus GMM**, not separate weekday/weekend models. It
preserves the historical 72-feature structure and GMM/BIC family while changing
the spatial assembly, exception handling, and low-flow treatment. The BIC minimum
reported below is a candidate, not a final substantive choice of K.

## Frozen inputs and sample

- Input LSOAs: {feature_summary['n_input_lsoas']}
- Full-week activity >= {feature_summary['min_total']}: {feature_summary['n_fullweek_total_ge_min']}
- Union of documented group-level one-direction exception LSOAs: {feature_summary['n_exception_union']}
- Exceptions that otherwise met the full-week threshold: {feature_summary['n_exception_union_ge_min']}
- Retained for clustering: **{feature_summary['n_retained']}**
- Features: {feature_summary['n_features']} (two separately normalised 36-bin full-week directions)
- Empirical shrinkage alpha: {feature_summary['alpha']}
- Feature row-sum check: {feature_summary['feature_row_sum_min']:.6f} to {feature_summary['feature_row_sum_max']:.6f} (expected 2)

### Block audit

{block_audit.to_markdown(index=False)}

## GMM/BIC result

Global BIC minimum: **covariance={best_covariance}, K={best_k}**.

{best_by_cov.to_markdown(index=False)}

## K diagnostics at covariance={best_covariance}

Bootstrap uses {bootstrap_n} full-size resamples. `bootstrap_ari_mean` measures
global agreement; `bootstrap_min_cluster_jaccard_mean` measures recovery of the
weakest matched cluster and is the safeguard against pseudo-reliability.

{kdiag[['K','BIC','silhouette','davies_bouldin','min_cluster_n','min_cluster_share','median_max_posterior','bootstrap_ari_mean','bootstrap_min_cluster_jaccard_mean']].to_markdown(index=False)}

## Automatic warnings

{chr(10).join('- ' + item for item in flags)}

## Adjacent-K structure

High child-to-parent purity means K+1 is largely splitting clusters already
present at K. A tiny smallest child is evidence against treating the new piece
as a robust new type without substantive support.

{adjacent.to_markdown(index=False)}

## Historical full-week comparison

The BIC magnitudes are not directly comparable across the two feature matrices;
the table is included only to document model-selection movement.

{old_text}

The following ARI compares old and new labels for the same K on shared LSOAs.
It measures sensitivity to the combined pipeline changes and cannot attribute
the change separately to hub assembly, exclusion, or shrinkage.

{compare_text}

## Interpretation boundary and next decision

This first pass can identify plausible candidate K values and detect tiny or
unstable clusters. It does not yet prove that alpha=5 is uniquely preferable.
The final K should be frozen only after reviewing BIC, small-cluster recovery,
adjacent-K splits, temporal profiles, and spatial maps together. If this result
is materially improved, the minimum sensitivity set is alpha=0 versus alpha=5
on the same retained sample, followed by a fixed-sample bootstrap comparison.
"""
    (C.REPORT / "FIRST_PASS_RESULTS.md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha", type=float, default=5.0)
    parser.add_argument("--min-total", type=float, default=50.0)
    parser.add_argument("--bootstrap", type=int, default=20)
    args = parser.parse_args()
    if args.alpha <= 0 or args.min_total < 0 or args.bootstrap < 1:
        raise ValueError("alpha and bootstrap must be positive; min-total must be non-negative")

    started = time.time()
    manifest = input_manifest(
        [
            ("hub_first_fullweek_long", C.LONG_INPUT),
            ("one_direction_exception_register", C.EXCEPTION_INPUT),
            ("lsoa_boundaries", C.LSOA_GEOJSON),
            ("historical_fullweek_bic_grid", C.OLD_FULLWEEK / "outputs" / "diagnostics" / "bus_bic_grid.csv"),
        ]
    )
    if not manifest.loc[manifest["role"].isin(["hub_first_fullweek_long", "one_direction_exception_register"]), "exists"].all():
        raise FileNotFoundError("A required primary input is missing; see the manifest")
    manifest.to_csv(C.OUT / "input_manifest.csv", index=False)

    X_df, meta, block_audit, feature_summary = build_features(args.alpha, args.min_total)
    grid, best_covariance, best_k = run_bic_grid(X_df.to_numpy(dtype=float))
    kdiag, labels_by_k, models_by_k, profiles = run_k_diagnostics(
        X_df, meta, best_covariance, args.bootstrap
    )
    adjacent = adjacent_k_diagnostic(labels_by_k)
    old_compare, old_summary = compare_old(labels_by_k, X_df.index)
    new_best = grid.loc[grid["BIC"].idxmin()]
    new_row = pd.DataFrame(
        [
            {
                "version": "new_hub_first_fullweek_alpha5",
                "n_lsoa": len(X_df),
                "n_features": X_df.shape[1],
                "BIC_best_covariance": best_covariance,
                "BIC_best_K": best_k,
                "BIC": float(new_best["BIC"]),
            }
        ]
    )
    pd.concat([old_summary, new_row], ignore_index=True).to_csv(
        C.DIAGNOSTICS / "old_vs_new_model_summary.csv", index=False
    )

    selected_model = models_by_k.get(best_k)
    if selected_model is None:
        selected_model, _, _ = fit_gmm(
            X_df.to_numpy(dtype=float), best_k, best_covariance, C.RANDOM_STATE, C.N_INIT
        )
    joblib.dump(selected_model, C.MODELS / "bus_fullweek_bic_best.joblib")
    repeat, _, _ = fit_gmm(
        X_df.to_numpy(dtype=float), best_k, best_covariance, C.RANDOM_STATE, C.N_INIT
    )
    deterministic = {
        "same_seed": C.RANDOM_STATE,
        "label_ari": float(
            adjusted_rand_score(
                selected_model.predict(X_df.to_numpy(dtype=float)),
                repeat.predict(X_df.to_numpy(dtype=float)),
            )
        ),
        "bic_absolute_difference": float(
            abs(
                selected_model.bic(X_df.to_numpy(dtype=float))
                - repeat.bic(X_df.to_numpy(dtype=float))
            )
        ),
    }
    (C.DIAGNOSTICS / "determinism_check.json").write_text(
        json.dumps(deterministic, indent=2), encoding="utf-8"
    )
    make_figures(grid, kdiag, profiles, labels_by_k, X_df.index)
    write_report(
        feature_summary,
        block_audit,
        grid,
        best_covariance,
        best_k,
        kdiag,
        adjacent,
        old_compare,
        old_summary,
        args.bootstrap,
    )

    environment = {
        "command": "python -u src\\run_fullweek_first_pass.py --alpha 5 --min-total 50 --bootstrap 20",
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn_version,
        "seed": C.RANDOM_STATE,
        "n_init": C.N_INIT,
        "bootstrap_n_init": C.BOOTSTRAP_N_INIT,
        "reg_covar": C.REG_COVAR,
        "max_iter": C.MAX_ITER,
        "elapsed_seconds": time.time() - started,
    }
    (C.OUT / "run_environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )
    log(f"[6/7] Selected BIC candidate: covariance={best_covariance}, K={best_k}")
    log(f"[7/7] Complete. Report: {C.REPORT / 'FIRST_PASS_RESULTS.md'}")


if __name__ == "__main__":
    main()
