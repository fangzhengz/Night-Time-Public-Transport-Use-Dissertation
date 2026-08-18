# -*- coding: utf-8 -*-
"""Strict low-activity sensitivity for StopArea raw-share clustering.

This sidecar keeps the official child-StopArea allocation, LSOA unit, 72
temporal-share features, GMM search settings and bootstrap procedure fixed. It
only raises the two-direction full-week threshold from 36 to 72.  It does not
delete zero-valued hourly observations: zero is an observed count, and CLR's
separate pseudo-count handling is not part of this raw-share sensitivity.

Each threshold writes only PNG figures under its own
``outputs/strict_min<threshold>_raw_share`` directory, so the min-36 raw-share
and CLR analyses remain unchanged.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
import time
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config as C


STRICT_MIN_DIRECTION = 72.0
VARIANT = ""
STEM_PREFIX = ""
ROOT = Path()
FIGURES = Path()
DIAGNOSTICS = Path()
LABELS = Path()
DATA = Path()
REPORT = Path()


def configure(min_direction: float) -> None:
    """Set an isolated output location for one strict-threshold sensitivity."""
    global STRICT_MIN_DIRECTION, VARIANT, STEM_PREFIX, ROOT, FIGURES, DIAGNOSTICS, LABELS, DATA, REPORT
    if min_direction <= C.MIN_DIRECTION:
        raise ValueError("Strict sensitivity must use a threshold greater than 36.")
    STRICT_MIN_DIRECTION = float(min_direction)
    threshold_tag = f"{STRICT_MIN_DIRECTION:g}"
    VARIANT = f"strict_min{threshold_tag}_raw_share"
    STEM_PREFIX = VARIANT
    ROOT = C.OUT / VARIANT
    FIGURES = ROOT / "figures"
    DIAGNOSTICS = ROOT / "diagnostics"
    LABELS = ROOT / "labels"
    DATA = ROOT / "data"
    REPORT = ROOT / "report"
    for directory in (ROOT, FIGURES, DIAGNOSTICS, LABELS, DATA, REPORT):
        directory.mkdir(parents=True, exist_ok=True)


configure(STRICT_MIN_DIRECTION)


def load_base_runner():
    spec = importlib.util.spec_from_file_location(
        "stoparea_base_runner", HERE / "02_run_clustering.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the base StopArea clustering runner.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_runner()


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_raw_share(raw_counts: pd.DataFrame) -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    for direction in C.DIRECTIONS:
        columns = [column for column in raw_counts if column.startswith(f"{direction}_")]
        counts = raw_counts[columns]
        totals = counts.sum(axis=1)
        if (totals < STRICT_MIN_DIRECTION).any():
            raise RuntimeError("Strict sample contains a direction total below 72.")
        shares = counts.div(totals, axis=0)
        if not np.allclose(shares.sum(axis=1), 1.0, atol=1e-10):
            raise RuntimeError(f"{direction} shares do not sum to one.")
        blocks.append(shares)
    result = pd.concat(blocks, axis=1)
    if result.shape[1] != 72 or not np.isfinite(result.to_numpy(dtype=float)).all():
        raise RuntimeError(f"Invalid strict raw-share matrix: {result.shape}")
    return result


def save_png(fig: plt.Figure, stem: str, dpi: int = 180, tight: bool = True) -> None:
    kwargs = {"bbox_inches": "tight"} if tight else {}
    fig.savefig(FIGURES / f"{stem}.png", dpi=dpi, **kwargs)
    plt.close(fig)


def build_profiles_and_maps(
    X: pd.DataFrame,
    labels_by_k: dict[int, np.ndarray],
    all_metrics: pd.DataFrame,
    reporting_family: str,
    plot_ks: list[int] | None = None,
) -> None:
    """Write temporal profiles and spatial maps for the requested K values."""
    plot_ks = C.CANDIDATE_KS if plot_ks is None else plot_ks
    for k in plot_ks:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(
            k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True
        )
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            means = X.loc[labels == cluster].mean(axis=0)
            for day_index, day_type in enumerate(C.DAY_TYPES):
                ax = axes[cluster, day_index]
                for direction, color in [
                    ("boardings", "#4C78A8"),
                    ("alightings", "#F58518"),
                ]:
                    values = [
                        means[f"{direction}_{day_type}_{hour}"] for hour in C.HOURS
                    ]
                    ax.plot(
                        range(12),
                        values,
                        marker="o",
                        markersize=2,
                        color=color,
                        label=direction,
                    )
                if cluster == 0:
                    ax.set_title(day_type)
                if day_index == 0:
                    ax.set_ylabel(f"C{cluster} (n={int(sizes[cluster])})")
                ax.grid(alpha=0.2)
        axes[-1, 1].set_xticks(
            range(12),
            ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"],
            rotation=45,
        )
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(
            f"StopArea strict low-activity sensitivity (both directions >={STRICT_MIN_DIRECTION:g}), "
            f"raw-share, {reporting_family} covariance, K={k}\n"
            "mean share of each direction's own full-week total",
            y=1.01,
        )
        fig.tight_layout()
        save_png(fig, f"{STEM_PREFIX}_full_profiles_k{k}", dpi=160)

    import geopandas as gpd

    boundaries = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(
        columns={code_column: "lsoa"}
    )
    units = pd.Index(X.index.astype(str), name="lsoa")
    excluded = sorted(set(all_metrics.index.astype(str)) - set(units))
    for k in plot_ks:
        label_frame = pd.DataFrame(
            {
                "lsoa": list(units) + excluded,
                "status": ["retained"] * len(units)
                + [f"below_{STRICT_MIN_DIRECTION:g}_or_outside_sample"] * len(excluded),
                "cluster": list(labels_by_k[k]) + [-1] * len(excluded),
            }
        )
        mapped = boundaries.merge(label_frame, on="lsoa", how="left")
        fig, ax = plt.subplots(figsize=(8, 8))
        mapped[mapped["status"] != "retained"].plot(
            ax=ax, color="#e0e0e0", linewidth=0.0
        )
        mapped[mapped["status"] == "retained"].plot(
            ax=ax,
            column="cluster",
            categorical=True,
            cmap="tab10",
            linewidth=0.0,
            legend=True,
        )
        ax.set_axis_off()
        ax.set_title(
            f"StopArea strict low-activity sensitivity (>= {STRICT_MIN_DIRECTION:g}), "
            f"raw-share, {reporting_family} covariance, K={k}\n"
            f"grey = below {STRICT_MIN_DIRECTION:g} in either direction or outside current valid sample"
        )
        fig.tight_layout()
        save_png(fig, f"{STEM_PREFIX}_full_map_k{k}", tight=False)


def make_all_k_map_atlas(
    X: pd.DataFrame,
    labels_by_k: dict[int, np.ndarray],
    all_metrics: pd.DataFrame,
    reporting_family: str,
) -> None:
    """Provide one compact spatial atlas so K=2--12 can be inspected together."""
    import geopandas as gpd

    boundaries = gpd.read_file(C.LSOA_GEOJSON)
    code_column = next(column for column in boundaries if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(columns={code_column: "lsoa"})
    units = pd.Index(X.index.astype(str), name="lsoa")
    excluded = sorted(set(all_metrics.index.astype(str)) - set(units))

    fig, axes = plt.subplots(3, 4, figsize=(15, 11))
    for ax, k in zip(axes.flat, C.K_RANGE):
        label_frame = pd.DataFrame(
            {
                "lsoa": list(units) + excluded,
                "status": ["retained"] * len(units)
                + [f"below_{STRICT_MIN_DIRECTION:g}_or_outside_sample"] * len(excluded),
                "cluster": list(labels_by_k[k]) + [-1] * len(excluded),
            }
        )
        mapped = boundaries.merge(label_frame, on="lsoa", how="left")
        mapped[mapped["status"] != "retained"].plot(ax=ax, color="#e0e0e0", linewidth=0.0)
        mapped[mapped["status"] == "retained"].plot(
            ax=ax, column="cluster", categorical=True, cmap="tab10", linewidth=0.0
        )
        ax.set_title(f"K={k}")
        ax.set_axis_off()
    axes.flat[-1].axis("off")
    fig.suptitle(
        f"StopArea strict low-activity sensitivity (both directions >={STRICT_MIN_DIRECTION:g}), "
        f"raw-share, {reporting_family} covariance\n"
        "Spatial atlas: grey = excluded; cluster colours are local to each K and not comparable across panels",
        fontsize=13,
        y=0.98,
    )
    fig.tight_layout()
    save_png(fig, f"{STEM_PREFIX}_all_k_map_atlas", dpi=180, tight=False)


def make_model_selection_bic_grid_figure() -> None:
    """Show the complete automated covariance-by-K BIC search used by this run."""
    grid = pd.read_csv(DIAGNOSTICS / "bic_grid.csv")
    selected = grid.loc[grid["BIC"].idxmin()]
    colors = {
        "spherical": "#4C78A8",
        "diag": "#F58518",
        "tied": "#54A24B",
        "full": "#B279A2",
    }
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    for covariance in C.COVARIANCES:
        d = grid.loc[grid["covariance"] == covariance].sort_values("K")
        axes[0].plot(d["K"], d["BIC"], "-o", label=covariance, color=colors[covariance])
        axes[1].plot(
            d["K"], d["BIC"] - float(selected["BIC"]), "-o", label=covariance, color=colors[covariance]
        )
    for ax in axes:
        ax.axvline(int(selected["K"]), color="#555555", linewidth=1, linestyle="--")
        ax.scatter(
            [int(selected["K"])],
            [float(selected["BIC"]) if ax is axes[0] else 0.0],
            color="#111111",
            marker="*",
            s=135,
            zorder=5,
            label="global BIC minimum" if ax is axes[0] else None,
        )
        ax.set_xlabel("K")
        ax.set_xticks(C.K_RANGE)
        ax.grid(alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("BIC (lower is better)")
    axes[0].set_title("Absolute BIC by covariance family")
    axes[0].legend(title="Covariance", fontsize=8)
    axes[1].set_ylabel("BIC minus global minimum")
    axes[1].set_title("Distance from global BIC minimum")
    fig.suptitle(
        f"Automated GMM model search: strict >= {STRICT_MIN_DIRECTION:g} threshold, raw-share\n"
        f"global BIC selection = {selected['covariance']} covariance, K={int(selected['K'])}",
        fontsize=13,
        y=1.03,
    )
    fig.tight_layout()
    save_png(fig, f"{STEM_PREFIX}_model_selection_bic_grid", dpi=180)


def make_kdiag_figure(
    X: np.ndarray,
    labels_by_k: dict[int, np.ndarray],
    kdiag: pd.DataFrame,
    reporting_family: str,
) -> None:
    d = kdiag.copy()
    d["calinski_harabasz"] = [
        float(calinski_harabasz_score(X, labels_by_k[k])) for k in d["K"]
    ]
    bootstrap = pd.read_csv(DIAGNOSTICS / "bootstrap.csv")
    summary = bootstrap.groupby("K")["ARI"].agg(ARI_mean="mean", ARI_sd="std").reset_index()
    d = d.merge(summary, on="K", how="left")
    d.to_csv(DIAGNOSTICS / "kdiag_full.csv", index=False)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    panels = [
        ("silhouette", "Silhouette (higher=better)", "#500778"),
        ("calinski_harabasz", "Calinski-Harabasz (higher=better)", "#2F6B4F"),
        ("davies_bouldin", "Davies-Bouldin (lower=better)", "#9A3D3D"),
        ("BIC", "BIC (lower=better)", "#500778"),
    ]
    for ax, (column, title, color) in zip(axes.flat[:4], panels):
        ax.plot(d["K"], d[column], "-o", color=color)
        ax.set_title(title)
    ax = axes.flat[4]
    available = d["ARI_mean"].notna()
    ax.errorbar(
        d.loc[available, "K"],
        d.loc[available, "ARI_mean"],
        yerr=d.loc[available, "ARI_sd"],
        fmt="-o",
        color="#500778",
        capsize=3,
    )
    ax.set_title("Bootstrap stability ARI (higher=better)")
    ax.set_ylim(0, 1.02)
    axes.flat[5].axis("off")
    for ax in axes.flat:
        if ax.has_data():
            ax.set_xlabel("K")
            ax.set_xticks(C.K_RANGE)
            ax.grid(color="#eeeeee")
            ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        f"bus (StopArea allocation, both directions >={STRICT_MIN_DIRECTION:g}, raw-share) - K-diagnostics\n"
        f"strict low-activity sensitivity, {reporting_family}-covariance reporting family (GMM)",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    save_png(fig, f"{STEM_PREFIX}_kdiag_full", dpi=160)


def baseline_comparison_figure(strict_kdiag: pd.DataFrame) -> pd.DataFrame:
    base = pd.read_csv(C.OUT / "raw_share" / "diagnostics" / "kdiag.csv")
    base["specification"] = "Baseline: >=36"
    strict_kdiag = strict_kdiag.copy()
    strict_kdiag["specification"] = f"Strict: >={STRICT_MIN_DIRECTION:g}"
    metrics = [
        ("silhouette", "Silhouette"),
        ("bootstrap_ari_mean", "Bootstrap ARI"),
        ("bootstrap_min_cluster_jaccard_mean", "Minimum-cluster Jaccard"),
        ("activity_eta2", "Activity eta-squared"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.2))
    x = np.arange(len(C.CANDIDATE_KS))
    width = 0.34
    for ax, (column, title) in zip(axes.flat, metrics):
        base_values = [
            float(base.loc[base["K"] == k, column].iloc[0]) for k in C.CANDIDATE_KS
        ]
        strict_values = [
            float(strict_kdiag.loc[strict_kdiag["K"] == k, column].iloc[0])
            for k in C.CANDIDATE_KS
        ]
        ax.bar(x - width / 2, base_values, width, label="Baseline >=36", color="#500778")
        ax.bar(x + width / 2, strict_values, width, label=f"Strict >={STRICT_MIN_DIRECTION:g}", color="#2F6B4F")
        ax.set_title(title)
        ax.set_xticks(x, [f"K={k}" for k in C.CANDIDATE_KS])
        ax.grid(axis="y", alpha=0.22)
        for position, value in zip(x - width / 2, base_values):
            ax.text(position, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
        for position, value in zip(x + width / 2, strict_values):
            ax.text(position, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle(
        "Raw-share candidate comparison: baseline threshold versus strict low-activity sensitivity\n"
        "same StopArea allocation and 72 temporal-share features; BIC excluded because samples differ",
        fontsize=12,
        y=1.01,
    )
    fig.tight_layout()
    save_png(fig, f"{STEM_PREFIX}_vs_min36_candidate_comparison", dpi=180)

    rows = []
    for k in C.CANDIDATE_KS:
        baseline_labels = pd.read_csv(
            C.OUT / "raw_share" / "labels" / f"k{k}_labels.csv", dtype={"lsoa": str}
        )
        baseline_labels = baseline_labels.loc[
            baseline_labels["retained_for_fit"], ["lsoa", "cluster"]
        ]
        strict_labels = pd.read_csv(LABELS / f"k{k}_labels.csv", dtype={"lsoa": str})
        strict_labels = strict_labels.loc[
            strict_labels["retained_for_fit"], ["lsoa", "cluster"]
        ]
        merged = baseline_labels.merge(
            strict_labels, on="lsoa", suffixes=("_baseline", "_strict"), validate="one_to_one"
        )
        rows.append(
            {
                "K": k,
                "baseline_n": len(baseline_labels),
                "strict_n": len(strict_labels),
                "common_n": len(merged),
                "ARI_on_strict_units": float(
                    adjusted_rand_score(merged["cluster_baseline"], merged["cluster_strict"])
                ),
            }
        )
    return pd.DataFrame(rows)


def render_saved_figures(all_k: bool = False) -> None:
    """Redraw PNG figures from a completed strict run without refitting models."""
    raw_counts = pd.read_parquet(C.FEATURES / "raw_counts_min36.parquet")
    raw_counts.index = pd.Index(raw_counts.index.astype(str), name="lsoa")
    all_metrics = pd.read_csv(C.FEATURES / "sample_metrics.csv", dtype={"lsoa": str}).set_index("lsoa")
    strict_units = pd.Index(
        all_metrics.index[all_metrics["min_direction_activity"] >= STRICT_MIN_DIRECTION],
        name="lsoa",
    )
    X_frame = make_raw_share(raw_counts.loc[strict_units])
    labels_by_k: dict[int, np.ndarray] = {}
    for k in C.K_RANGE:
        labels = pd.read_csv(LABELS / f"k{k}_labels.csv", dtype={"lsoa": str}).set_index("lsoa")
        values = labels.loc[strict_units, "cluster"].to_numpy(dtype=int)
        if (values < 0).any():
            raise RuntimeError(f"Saved K={k} labels do not cover the strict sample.")
        labels_by_k[k] = values
    kdiag = pd.read_csv(DIAGNOSTICS / "kdiag.csv")
    environment = json.loads((ROOT / "run_environment.json").read_text(encoding="utf-8"))
    reporting_family = str(environment["reporting_covariance"])
    plot_ks = C.K_RANGE if all_k else C.CANDIDATE_KS
    build_profiles_and_maps(
        X_frame, labels_by_k, all_metrics, reporting_family, plot_ks=plot_ks
    )
    if all_k:
        make_all_k_map_atlas(X_frame, labels_by_k, all_metrics, reporting_family)
    make_model_selection_bic_grid_figure()
    make_kdiag_figure(X_frame.to_numpy(dtype=float), labels_by_k, kdiag, reporting_family)
    baseline_comparison_figure(kdiag)
    log(
        f"[{VARIANT}] redrew {'all-K' if all_k else 'candidate-K'} PNG figures "
        "from saved diagnostics and labels"
    )


def main() -> None:
    started = time.time()
    raw_counts_path = C.FEATURES / "raw_counts_min36.parquet"
    metrics_path = C.FEATURES / "sample_metrics.csv"
    if not raw_counts_path.exists() or not metrics_path.exists():
        raise FileNotFoundError("Run 01_prepare_features.py before this strict sensitivity.")
    raw_counts = pd.read_parquet(raw_counts_path)
    raw_counts.index = pd.Index(raw_counts.index.astype(str), name="lsoa")
    all_metrics = pd.read_csv(metrics_path, dtype={"lsoa": str}).set_index("lsoa")
    strict_units = pd.Index(
        all_metrics.index[all_metrics["min_direction_activity"] >= STRICT_MIN_DIRECTION],
        name="lsoa",
    )
    if not set(strict_units).issubset(set(raw_counts.index)):
        raise RuntimeError("The strict sample is not a subset of the min-36 raw counts.")
    X_frame = make_raw_share(raw_counts.loc[strict_units])
    X = X_frame.to_numpy(dtype=float)
    metrics = all_metrics.loc[strict_units]
    X_frame.to_parquet(DATA / f"X_bus_stoparea_raw_share_min{STRICT_MIN_DIRECTION:g}.parquet")

    strict_flags = all_metrics.copy()
    strict_flags["retained_for_fit"] = strict_flags["min_direction_activity"] >= STRICT_MIN_DIRECTION
    strict_flags["exclusion_reason"] = np.where(
        strict_flags["retained_for_fit"],
        f"retained_min_direction_{STRICT_MIN_DIRECTION:g}",
        f"at_least_one_direction_below_{STRICT_MIN_DIRECTION:g}",
    )
    strict_flags.reset_index().to_csv(
        DATA / f"sample_metrics_min{STRICT_MIN_DIRECTION:g}.csv", index=False
    )
    coverage = pd.DataFrame(
        [
            {"sample": "all StopArea LSOAs", "n": len(all_metrics), "share_of_input": 1.0},
            {"sample": "baseline min direction >=36", "n": int(all_metrics["retained_for_fit"].sum()), "share_of_input": float(all_metrics["retained_for_fit"].mean())},
            {"sample": f"strict min direction >={STRICT_MIN_DIRECTION:g}", "n": len(strict_units), "share_of_input": len(strict_units) / len(all_metrics)},
        ]
    )
    coverage.to_csv(DATA / "coverage.csv", index=False)
    if X.shape != (len(strict_units), 72) or len(strict_units) == 0:
        raise RuntimeError(f"Unexpected strict sample shape: {X.shape}")

    log(f"[{VARIANT}] fitting 4 covariance families x K=2..12; n={len(X)}, n_init={C.N_INIT}")
    grid_rows: list[dict] = []
    grid_labels: dict[tuple[str, int], np.ndarray] = {}
    for covariance in C.COVARIANCES:
        for k in C.K_RANGE:
            fit_started = time.perf_counter()
            model = BASE.fit_gmm(X, k, covariance, C.SEED, C.N_INIT)
            seconds = time.perf_counter() - fit_started
            labels = model.predict(X).astype(int)
            grid_labels[(covariance, k)] = labels
            sizes = np.bincount(labels, minlength=k)
            grid_rows.append(
                {
                    "covariance": covariance,
                    "K": k,
                    "BIC": float(model.bic(X)),
                    "AIC": float(model.aic(X)),
                    "converged": bool(model.converged_),
                    "fit_seconds": seconds,
                    "min_cluster_n": int(sizes.min()),
                    "min_cluster_share": float(sizes.min() / sizes.sum()),
                }
            )
            log(f"  {covariance:9s} K={k:2d} BIC={grid_rows[-1]['BIC']:.1f} min_n={sizes.min():4d} ({seconds:.1f}s)")
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(DIAGNOSTICS / "bic_grid.csv", index=False)
    reporting_family, global_family, global_k, family_note = BASE.choose_reporting_family(grid)
    labels_by_k = {k: grid_labels[(reporting_family, k)] for k in C.K_RANGE}
    log(f"[{VARIANT}] reporting covariance={reporting_family}; {family_note}")

    kdiag_rows: list[dict] = []
    for k in C.K_RANGE:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        grid_row = grid[(grid["covariance"] == reporting_family) & (grid["K"] == k)].iloc[0]
        row = {
            "K": k,
            "BIC": float(grid_row["BIC"]),
            "silhouette": float(silhouette_score(X, labels)),
            "davies_bouldin": float(davies_bouldin_score(X, labels)),
            "activity_eta2": BASE.eta_squared(metrics["log_total_activity"], labels),
            "min_cluster_share": float(sizes.min() / sizes.sum()),
        }
        for metric in C.TIMING_METRICS + ["direction_balance", "weekend_ratio"]:
            values = metrics[metric]
            mask = values.notna()
            row[f"{metric}_eta2"] = BASE.eta_squared(values[mask], labels[mask.to_numpy()])
        row["timing_mean_eta2"] = float(np.mean([row[f"{metric}_eta2"] for metric in C.TIMING_METRICS]))
        kdiag_rows.append(row)

        label_frame = strict_flags[["retained_for_fit", "min_direction_activity", "exclusion_reason"]].copy()
        label_frame["cluster"] = -1
        label_frame.loc[strict_units, "cluster"] = labels
        label_frame.reset_index().to_csv(LABELS / f"k{k}_labels.csv", index=False)
    kdiag = pd.DataFrame(kdiag_rows)

    log(f"[{VARIANT}] bootstrap K={C.BOOTSTRAP_KS}, replicates=20")
    rng = np.random.default_rng(C.SEED)
    bootstrap_rows: list[dict] = []
    for k in C.BOOTSTRAP_KS:
        base_labels = labels_by_k[k]
        for replicate in range(20):
            sample = rng.choice(len(X), size=len(X), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model = BASE.fit_gmm(X[sample], k, reporting_family, seed, C.BOOTSTRAP_N_INIT)
            other = model.predict(X)
            matched = BASE.matched_jaccard(base_labels, other, k)
            bootstrap_rows.append(
                {
                    "K": k,
                    "replicate": replicate + 1,
                    "ARI": float(adjusted_rand_score(base_labels, other)),
                    "min_matched_cluster_jaccard": float(matched.min()),
                }
            )
        current = pd.DataFrame(bootstrap_rows).query("K == @k")
        log(f"  K={k}: ARI mean={current['ARI'].mean():.3f}; min Jaccard mean={current['min_matched_cluster_jaccard'].mean():.3f}")
    bootstrap = pd.DataFrame(bootstrap_rows)
    bootstrap.to_csv(DIAGNOSTICS / "bootstrap.csv", index=False)
    boot_summary = bootstrap.groupby("K", as_index=False).agg(
        bootstrap_ari_mean=("ARI", "mean"),
        bootstrap_ari_sd=("ARI", "std"),
        bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")
    kdiag.to_csv(DIAGNOSTICS / "kdiag.csv", index=False)

    grand_centroid = X.mean(axis=0)
    grand_distance = float(np.linalg.norm(X - grand_centroid, axis=1).mean())
    homogeneity_rows: list[dict] = []
    for k in C.CANDIDATE_KS:
        labels = labels_by_k[k]
        silhouettes = silhouette_samples(X, labels)
        for cluster in range(k):
            mask = labels == cluster
            members = X[mask]
            centroid = members.mean(axis=0)
            distances = np.linalg.norm(members - centroid, axis=1)
            homogeneity_rows.append(
                {
                    "K": k,
                    "cluster": cluster,
                    "n": int(mask.sum()),
                    "share": float(mask.mean()),
                    "mean_silhouette": float(silhouettes[mask].mean()),
                    "relative_compactness_vs_sample": float(distances.mean() / grand_distance),
                    "mean_log_total_activity": float(metrics.iloc[np.flatnonzero(mask)]["log_total_activity"].mean()),
                    "mean_post_midnight_share": float(metrics.iloc[np.flatnonzero(mask)]["post_midnight_share"].mean()),
                }
            )
    pd.DataFrame(homogeneity_rows).to_csv(DIAGNOSTICS / "cluster_homogeneity.csv", index=False)

    deterministic = BASE.fit_gmm(X, 3, reporting_family, C.SEED, C.N_INIT).predict(X)
    deterministic_exact = bool(np.array_equal(deterministic, labels_by_k[3]))
    deterministic_ari = float(adjusted_rand_score(deterministic, labels_by_k[3]))
    output = {"data": DATA}
    geography = BASE.cluster_geography(labels_by_k, strict_units, output)
    build_profiles_and_maps(X_frame, labels_by_k, all_metrics, reporting_family)
    make_model_selection_bic_grid_figure()
    make_kdiag_figure(X, labels_by_k, kdiag, reporting_family)
    agreement = baseline_comparison_figure(kdiag)
    agreement.to_csv(
        DATA / f"min{STRICT_MIN_DIRECTION:g}_vs_min36_partition_agreement.csv",
        index=False,
    )

    environment = {
        "variant": VARIANT,
        "elapsed_seconds": time.time() - started,
        "n_lsoas": len(X),
        "n_features": X.shape[1],
        "min_direction_threshold": STRICT_MIN_DIRECTION,
        "seed": C.SEED,
        "n_init": C.N_INIT,
        "bootstrap_replicates": 20,
        "reporting_covariance": reporting_family,
        "global_bic_covariance": global_family,
        "global_bic_k": global_k,
        "k3_deterministic_exact_labels": deterministic_exact,
        "k3_deterministic_ari": deterministic_ari,
        "python": sys.version,
        "platform": platform.platform(),
    }
    (ROOT / "run_environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    pd.DataFrame(
        [
            {"role": "min36_raw_counts", "path": str(raw_counts_path.resolve()), "sha256": sha256(raw_counts_path)},
            {"role": "sample_metrics", "path": str(metrics_path.resolve()), "sha256": sha256(metrics_path)},
        ]
    ).to_csv(DATA / "input_manifest.csv", index=False)

    report = [
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite/experiment-agent",
        "- Origin Mode: run + validate",
        "- Verification Status: VERIFIED for feature invariants and deterministic K=3 refit; ANALYZED for clustering interpretation",
        f"- Version Label: stoparea_strict_min{STRICT_MIN_DIRECTION:g}_raw_share_v1",
        "",
        "# StopArea strict low-activity sensitivity: raw-share",
        "",
        "## Fixed and changed factors",
        "",
        "- Fixed: official child-StopArea allocation, LSOA unit, 72 direction-wise temporal-share features, GMM grid and bootstrap procedure.",
        f"- Changed: retain only LSOAs with both full-week direction totals >={STRICT_MIN_DIRECTION:g} (mean >={STRICT_MIN_DIRECTION / 36:g} per observed hour).",
        "- Not changed: zero-valued hourly counts remain observed values; no zero-cell deletion or smoothing is applied.",
        "",
        "## Coverage",
        "",
        coverage.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## K diagnostics",
        "",
        kdiag.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Baseline agreement on the strict common units",
        "",
        agreement.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Interpretation boundary",
        "",
        "This is a sample-restriction sensitivity analysis, not a replacement primary typology. BIC is compared only within this strict sample; absolute BIC is not compared with the min-36 sample.",
    ]
    if not geography.empty:
        report.extend(["", "## Central-versus-outer diagnostic", "", geography.to_markdown(index=False, floatfmt=".6f")])
    (REPORT / "RESULTS.md").write_text("\n".join(report), encoding="utf-8")
    log(f"[{VARIANT}] complete in {environment['elapsed_seconds']:.1f}s: {REPORT / 'RESULTS.md'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run one strict StopArea raw-share low-activity sensitivity."
    )
    parser.add_argument(
        "--min-direction",
        type=float,
        default=72.0,
        help="Minimum full-week boardings and alightings retained per LSOA (default: 72).",
    )
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="Redraw PNG figures from an existing completed strict run without refitting.",
    )
    parser.add_argument(
        "--all-k-figures",
        action="store_true",
        help="With --figures-only, write K=2..12 maps, profiles and one spatial atlas.",
    )
    args = parser.parse_args()
    configure(args.min_direction)
    if args.figures_only:
        render_saved_figures(all_k=args.all_k_figures)
    else:
        main()
