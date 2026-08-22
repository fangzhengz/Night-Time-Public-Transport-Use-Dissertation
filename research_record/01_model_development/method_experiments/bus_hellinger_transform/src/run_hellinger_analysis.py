"""Run the zero-preserving Hellinger bus-clustering sensitivity.

The official hub-first raw-share feature matrix is the only clustering input.
Each 36-cell direction block already sums to one; this script applies sqrt(p)
without pseudo-counts, then repeats the existing GMM/K/bootstrap diagnostics.
It also writes raw-share temporal profiles and LSOA maps for K=2..8 so the
figure set aligns with the official raw-share output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent
RAW_ROOT = FYP / "巴士聚类错误修改"
CLR_ROOT = FYP / "rq1_bus_clr_transform"

RAW_SHARE_X = RAW_ROOT / "outputs" / "features" / "X_bus_fullweek_alpha0.parquet"
RAW_METRICS = CLR_ROOT / "outputs" / "features" / "raw_metrics.csv"
RAW_KDIAG = RAW_ROOT / "outputs" / "diagnostics" / "bus_fullweek_kdiag.csv"
CLR_KDIAG = CLR_ROOT / "outputs" / "diagnostics" / "clr_kdiag_full.csv"
LSOA_GEOJSON = FYP / "map" / "London_LSOA_2021_Boundaries.geojson"
LSOA_LAD_LOOKUP = FYP / "IMDdata" / "ons_lsoa11_lsoa21_lad22_london_lookup.csv"

OUT = ROOT / "outputs"
FEATURES = OUT / "features"
DIAGNOSTICS = OUT / "diagnostics"
LABELS = OUT / "labels"
FIGURES = OUT / "figures"
DATA = OUT / "data"
REPORT = OUT / "report"
for directory in (OUT, FEATURES, DIAGNOSTICS, LABELS, FIGURES, DATA, REPORT):
    directory.mkdir(parents=True, exist_ok=True)

DAY_TYPES = ["Weekday", "Saturday", "Sunday"]
DIRECTIONS = ["boardings", "alightings"]
K_RANGE = list(range(2, 13))
PLOT_K_RANGE = list(range(2, 9))
COVARIANCES = ["spherical", "diag", "tied", "full"]
N_INIT = 20
BOOTSTRAP_N_INIT = 3
REG_COVAR = 1e-6
MAX_ITER = 300
SEED = 42
TIMING_METRICS = ["post_midnight_share", "deep_night_share", "post_midnight_persistence"]

MIN_CLUSTER_SHARE_GATE = 0.05
BOOTSTRAP_ARI_GATE = 0.70
MIN_JACCARD_GATE = 0.50
ZERO_ETA_REDUCTION_GATE = 0.25
TIMING_RETENTION_GATE = 0.85

TARGET_LADS = {
    "E09000033": "Westminster",
    "E09000007": "Camden",
    "E09000021": "Kingston upon Thames",
    "E09000027": "Richmond upon Thames",
}


def log(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fit_gmm(X: np.ndarray, k: int, covariance: str, seed: int, n_init: int) -> GaussianMixture:
    return GaussianMixture(
        n_components=k,
        covariance_type=covariance,
        n_init=n_init,
        reg_covar=REG_COVAR,
        max_iter=MAX_ITER,
        random_state=seed,
    ).fit(X)


def eta_squared(values: pd.Series, labels: np.ndarray) -> float:
    y = values.to_numpy(dtype=float)
    grand = float(y.mean())
    total = float(np.square(y - grand).sum())
    if total <= 0:
        return float("nan")
    between = sum(
        int((labels == cluster).sum()) * (float(y[labels == cluster].mean()) - grand) ** 2
        for cluster in np.unique(labels)
    )
    return float(between / total)


def kw_epsilon_squared(values: pd.Series, labels: np.ndarray) -> tuple[float, float]:
    groups = [values.to_numpy(dtype=float)[labels == cluster] for cluster in np.unique(labels)]
    stat, pvalue = stats.kruskal(*groups)
    n = len(values)
    k = len(groups)
    epsilon = max(0.0, float((stat - k + 1) / (n - k))) if n > k else float("nan")
    return epsilon, float(pvalue)


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


def read_labels(path: Path, index: pd.Index) -> np.ndarray:
    frame = pd.read_csv(path)
    frame["unit"] = frame["unit"].astype(str)
    return frame.set_index("unit").loc[index, "cluster"].to_numpy(dtype=int)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    X_raw = pd.read_parquet(RAW_SHARE_X)
    X_raw.index = pd.Index(X_raw.index.astype(str), name="lsoa")
    if X_raw.shape != (3365, 72):
        raise ValueError(f"Expected official (3365, 72) matrix, got {X_raw.shape}")
    if X_raw.index.has_duplicates:
        raise ValueError("Raw-share feature index contains duplicate LSOAs")
    values = X_raw.to_numpy(dtype=float)
    if not np.isfinite(values).all() or values.min() < 0:
        raise ValueError("Raw-share matrix contains non-finite or negative values")
    for direction in DIRECTIONS:
        columns = [column for column in X_raw.columns if column.startswith(f"{direction}_")]
        sums = X_raw[columns].sum(axis=1)
        if len(columns) != 36 or not np.allclose(sums, 1.0, atol=1e-10):
            raise ValueError(f"{direction} block is not a valid 36-part composition")

    metrics = pd.read_csv(RAW_METRICS, index_col=0)
    metrics.index = pd.Index(metrics.index.astype(str), name="lsoa")
    metrics = metrics.loc[X_raw.index].copy()
    zero = X_raw.eq(0.0)
    hours = np.array([int(column.rsplit("_", 1)[1]) for column in X_raw.columns])
    metrics["zero_bin_count"] = zero.sum(axis=1)
    metrics["zero_bin_share"] = metrics["zero_bin_count"] / X_raw.shape[1]
    metrics["evening_zero_bin_count"] = zero.loc[:, hours < 1440].sum(axis=1)
    metrics["post_midnight_zero_bin_count"] = zero.loc[:, hours >= 1440].sum(axis=1)
    metrics["deep_night_zero_bin_count"] = zero.loc[:, hours >= 1620].sum(axis=1)
    metrics.to_csv(FEATURES / "raw_metrics_with_zeros.csv")
    return X_raw, metrics


def build_hellinger_features(X_raw: pd.DataFrame) -> pd.DataFrame:
    X = np.sqrt(X_raw)
    X.index = X_raw.index
    X.columns = X_raw.columns
    for direction in DIRECTIONS:
        columns = [column for column in X.columns if column.startswith(f"{direction}_")]
        squared_norm = np.square(X[columns]).sum(axis=1)
        if not np.allclose(squared_norm, 1.0, atol=1e-10):
            raise ValueError(f"{direction} Hellinger block does not have unit squared norm")
    if int(X.eq(0.0).sum().sum()) != int(X_raw.eq(0.0).sum().sum()):
        raise ValueError("Hellinger transform did not preserve the exact-zero pattern")
    X.to_parquet(FEATURES / "X_bus_fullweek_hellinger.parquet")
    return X


def run_bic_grid(Xv: np.ndarray) -> tuple[pd.DataFrame, str, int, str]:
    rows: list[dict] = []
    log("[3/10] BIC grid: 4 covariance families x K=2..12")
    for covariance in COVARIANCES:
        for k in K_RANGE:
            started = time.perf_counter()
            model = fit_gmm(Xv, k, covariance, SEED, N_INIT)
            labels = model.predict(Xv)
            sizes = np.bincount(labels, minlength=k)
            rows.append(
                {
                    "covariance": covariance,
                    "K": k,
                    "BIC": float(model.bic(Xv)),
                    "AIC": float(model.aic(Xv)),
                    "converged": bool(model.converged_),
                    "n_iter": int(model.n_iter_),
                    "fit_seconds": time.perf_counter() - started,
                    "min_cluster_n": int(sizes.min()),
                    "min_cluster_share": float(sizes.min() / sizes.sum()),
                }
            )
            log(f"  {covariance:9s} K={k:2d} BIC={rows[-1]['BIC']:.1f} min_n={sizes.min():4d}")
    grid = pd.DataFrame(rows)
    grid.to_csv(DIAGNOSTICS / "hellinger_bic_grid.csv", index=False)
    best = grid.loc[grid["BIC"].idxmin()]
    global_covariance, global_k = str(best["covariance"]), int(best["K"])
    if global_covariance != "full" and int(best["min_cluster_n"]) <= 3:
        note = (
            f"Global BIC minimum covariance={global_covariance}, K={global_k} was degenerate "
            f"(min_cluster_n={int(best['min_cluster_n'])}); reporting family overridden to full."
        )
        return grid, "full", global_k, note
    return grid, global_covariance, global_k, "Global BIC family retained; no degeneracy override."


def label_diagnostics(metrics: pd.DataFrame, labels: np.ndarray) -> dict[str, float]:
    row: dict[str, float] = {}
    for metric in ["log_total_activity", "zero_bin_count"] + TIMING_METRICS + ["direction_balance", "weekend_ratio"]:
        values = metrics[metric]
        mask = values.notna()
        row[f"{metric}_eta2"] = eta_squared(values[mask], labels[mask.to_numpy()])
    row["activity_eta2"] = row["log_total_activity_eta2"]
    row["timing_mean_eta2"] = float(np.mean([row[f"{metric}_eta2"] for metric in TIMING_METRICS]))
    row["zero_bin_eta2"] = row["zero_bin_count_eta2"]
    activity_epsilon, activity_p = kw_epsilon_squared(metrics["log_total_activity"], labels)
    zero_epsilon, zero_p = kw_epsilon_squared(metrics["zero_bin_count"], labels)
    row["activity_kw_epsilon2"] = activity_epsilon
    row["activity_kw_p"] = activity_p
    row["zero_bin_kw_epsilon2"] = zero_epsilon
    row["zero_bin_kw_p"] = zero_p
    return row


def run_k_diagnostics(X: pd.DataFrame, metrics: pd.DataFrame, family: str) -> tuple[pd.DataFrame, dict[int, np.ndarray]]:
    Xv = X.to_numpy(dtype=float)
    rows: list[dict] = []
    labels_by_k: dict[int, np.ndarray] = {}
    log(f"[4/10] K diagnostics at covariance={family}")
    for k in K_RANGE:
        model = fit_gmm(Xv, k, family, SEED, N_INIT)
        labels = model.predict(Xv)
        labels_by_k[k] = labels
        sizes = np.bincount(labels, minlength=k)
        row = {
            "K": k,
            "covariance": family,
            "BIC": float(model.bic(Xv)),
            "AIC": float(model.aic(Xv)),
            "silhouette": float(silhouette_score(Xv, labels)),
            "calinski_harabasz": float(calinski_harabasz_score(Xv, labels)),
            "davies_bouldin": float(davies_bouldin_score(Xv, labels)),
            "converged": bool(model.converged_),
            "n_iter": int(model.n_iter_),
            "min_cluster_n": int(sizes.min()),
            "min_cluster_share": float(sizes.min() / sizes.sum()),
            "max_cluster_n": int(sizes.max()),
            "max_cluster_share": float(sizes.max() / sizes.sum()),
        }
        row.update(label_diagnostics(metrics, labels))
        rows.append(row)
        pd.DataFrame({"unit": X.index, "cluster": labels}).to_csv(
            LABELS / f"hellinger_k{k}_labels.csv", index=False
        )
        log(
            f"  K={k:2d} sil={row['silhouette']:.3f} zero_eta2={row['zero_bin_eta2']:.3f} "
            f"activity_eta2={row['activity_eta2']:.3f} timing_eta2={row['timing_mean_eta2']:.3f}"
        )
    return pd.DataFrame(rows), labels_by_k


def run_bootstrap(Xv: np.ndarray, labels_by_k: dict[int, np.ndarray], family: str, n_bootstrap: int) -> pd.DataFrame:
    log(f"[5/10] Bootstrap K=2..8, n={n_bootstrap}")
    rng = np.random.default_rng(SEED)
    rows: list[dict] = []
    for k in PLOT_K_RANGE:
        base = labels_by_k[k]
        for replicate in range(1, n_bootstrap + 1):
            idx = rng.choice(len(Xv), size=len(Xv), replace=True)
            seed = int(rng.integers(1, 2**31 - 1))
            model = fit_gmm(Xv[idx], k, family, seed, BOOTSTRAP_N_INIT)
            other = model.predict(Xv)
            matched = matched_jaccard(base, other, k)
            rows.append(
                {
                    "K": k,
                    "replicate": replicate,
                    "ARI": float(adjusted_rand_score(base, other)),
                    "mean_matched_cluster_jaccard": float(matched.mean()),
                    "min_matched_cluster_jaccard": float(matched.min()),
                }
            )
        sub = pd.DataFrame(rows)
        sub = sub[sub["K"] == k]
        log(f"  K={k}: ARI={sub['ARI'].mean():.3f}; min Jaccard={sub['min_matched_cluster_jaccard'].mean():.3f}")
    bootstrap = pd.DataFrame(rows)
    bootstrap.to_csv(DIAGNOSTICS / "hellinger_bootstrap.csv", index=False)
    return bootstrap


def add_comparators(kdiag: pd.DataFrame, metrics: pd.DataFrame, index: pd.Index) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_diag = pd.read_csv(RAW_KDIAG)
    clr_diag = pd.read_csv(CLR_KDIAG)
    comparison_rows: list[dict] = []
    ari_rows: list[dict] = []
    for k in K_RANGE:
        h_labels = read_labels(LABELS / f"hellinger_k{k}_labels.csv", index)
        raw_labels = read_labels(RAW_ROOT / "outputs" / "labels" / f"bus_fullweek_k{k}_labels.csv", index)
        clr_labels = read_labels(CLR_ROOT / "outputs" / "labels" / f"clr_k{k}_labels.csv", index)
        ari_rows.append(
            {
                "K": k,
                "hellinger_vs_raw_ARI": float(adjusted_rand_score(h_labels, raw_labels)),
                "hellinger_vs_clr_ARI": float(adjusted_rand_score(h_labels, clr_labels)),
                "raw_vs_clr_ARI": float(adjusted_rand_score(raw_labels, clr_labels)),
            }
        )
        for transform, labels in [("raw_share", raw_labels), ("CLR", clr_labels), ("Hellinger", h_labels)]:
            values = label_diagnostics(metrics, labels)
            source = kdiag if transform == "Hellinger" else raw_diag if transform == "raw_share" else clr_diag
            source_row = source[source["K"] == k].iloc[0]
            comparison_rows.append(
                {
                    "K": k,
                    "transform": transform,
                    "zero_bin_eta2": values["zero_bin_eta2"],
                    "activity_eta2": values["activity_eta2"],
                    "timing_mean_eta2": values["timing_mean_eta2"],
                    "silhouette_within_transform": float(source_row["silhouette"]),
                    "min_cluster_share": float(source_row["min_cluster_share"]),
                    "bootstrap_ari_mean": float(source_row.get("bootstrap_ari_mean", np.nan)),
                    "bootstrap_min_cluster_jaccard_mean": float(
                        source_row.get("bootstrap_min_cluster_jaccard_mean", np.nan)
                    ),
                }
            )
    comparison = pd.DataFrame(comparison_rows)
    aris = pd.DataFrame(ari_rows)
    comparison.to_csv(DIAGNOSTICS / "transform_comparison_by_k.csv", index=False)
    aris.to_csv(DIAGNOSTICS / "cross_transform_label_ari.csv", index=False)
    return comparison, aris


def select_reporting_k(kdiag: pd.DataFrame, comparison: pd.DataFrame) -> tuple[int, pd.DataFrame, dict]:
    screened = kdiag[kdiag["K"].isin(PLOT_K_RANGE)].copy()
    screened["size_pass"] = screened["min_cluster_share"] >= MIN_CLUSTER_SHARE_GATE
    screened["stability_pass"] = screened["bootstrap_ari_mean"] >= BOOTSTRAP_ARI_GATE
    screened["jaccard_pass"] = screened["bootstrap_min_cluster_jaccard_mean"] >= MIN_JACCARD_GATE
    screened["structural_screen_pass"] = screened[["size_pass", "stability_pass", "jaccard_pass"]].all(axis=1)
    candidates = screened[screened["structural_screen_pass"]]
    if len(candidates):
        selected = int(candidates.loc[candidates["BIC"].idxmin(), "K"])
        selection_basis = "lowest within-Hellinger BIC among pre-screened stable/non-tiny K=2..8 solutions"
    else:
        eligible = screened[screened["size_pass"]]
        if eligible.empty:
            eligible = screened
        selected = int(eligible.loc[eligible["bootstrap_ari_mean"].idxmax(), "K"])
        selection_basis = "fallback diagnostic reference: no K passed all structural screens"

    selected_h = screened[screened["K"] == selected].iloc[0]
    selected_c = comparison[(comparison["K"] == selected) & (comparison["transform"] == "CLR")].iloc[0]
    zero_reduction = 1.0 - float(selected_h["zero_bin_eta2"] / selected_c["zero_bin_eta2"])
    timing_retention = float(selected_h["timing_mean_eta2"] / selected_c["timing_mean_eta2"])
    zero_pass = zero_reduction >= ZERO_ETA_REDUCTION_GATE
    timing_pass = timing_retention >= TIMING_RETENTION_GATE
    transform_pass = bool(selected_h["structural_screen_pass"] and zero_pass and timing_pass)
    screened["selected"] = screened["K"] == selected
    screened.to_csv(DIAGNOSTICS / "hellinger_k_selection_screen.csv", index=False)
    selection = {
        "selected_k": selected,
        "selection_basis": selection_basis,
        "structural_screen_pass": bool(selected_h["structural_screen_pass"]),
        "zero_eta2_reduction_vs_clr": zero_reduction,
        "zero_reduction_gate": ZERO_ETA_REDUCTION_GATE,
        "zero_gate_pass": bool(zero_pass),
        "timing_eta2_retention_vs_clr": timing_retention,
        "timing_retention_gate": TIMING_RETENTION_GATE,
        "timing_gate_pass": bool(timing_pass),
        "transform_acceptance_pass": transform_pass,
    }
    (DIAGNOSTICS / "hellinger_selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
    return selected, screened, selection


def write_cluster_summaries(Xv: np.ndarray, metrics: pd.DataFrame, labels_by_k: dict[int, np.ndarray]) -> tuple[pd.DataFrame, pd.DataFrame]:
    grand_centroid = Xv.mean(axis=0)
    grand_distance = float(np.linalg.norm(Xv - grand_centroid, axis=1).mean())
    homogeneity_rows: list[dict] = []
    signature_rows: list[dict] = []
    for k in PLOT_K_RANGE:
        labels = labels_by_k[k]
        sil = silhouette_samples(Xv, labels)
        for cluster in range(k):
            mask = labels == cluster
            members = Xv[mask]
            centroid = members.mean(axis=0)
            distances = np.linalg.norm(members - centroid, axis=1)
            homogeneity_rows.append(
                {
                    "K": k,
                    "cluster": cluster,
                    "n": int(mask.sum()),
                    "share": float(mask.mean()),
                    "mean_silhouette": float(sil[mask].mean()),
                    "relative_compactness_vs_sample": float(distances.mean() / grand_distance),
                }
            )
            row = {"K": k, "cluster": cluster, "n": int(mask.sum())}
            for metric in [
                "log_total_activity",
                "direction_balance",
                "post_midnight_share",
                "deep_night_share",
                "post_midnight_persistence",
                "weekend_ratio",
                "zero_bin_count",
                "post_midnight_zero_bin_count",
            ]:
                values = metrics.loc[mask, metric].dropna()
                row[f"{metric}_mean"] = float(values.mean())
                row[f"{metric}_median"] = float(values.median())
            signature_rows.append(row)
    homogeneity = pd.DataFrame(homogeneity_rows)
    signatures = pd.DataFrame(signature_rows)
    homogeneity.to_csv(DIAGNOSTICS / "hellinger_cluster_homogeneity.csv", index=False)
    signatures.to_csv(DIAGNOSTICS / "hellinger_cluster_signatures.csv", index=False)
    return homogeneity, signatures


def plot_k_diagnostics(grid: pd.DataFrame, kdiag: pd.DataFrame, bootstrap: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for covariance in COVARIANCES:
        sub = grid[grid["covariance"] == covariance]
        ax.plot(sub["K"], sub["BIC"], marker="o", label=covariance)
    ax.set(xlabel="K", ylabel="BIC", title="Hellinger features: BIC grid")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "hellinger_bic_grid.png", dpi=180)
    plt.close(fig)

    boot_summary = bootstrap.groupby("K")["ARI"].agg(ARI_mean="mean", ARI_sd="std").reset_index()
    d = kdiag.merge(boot_summary, on="K", how="left")
    d.to_csv(DIAGNOSTICS / "hellinger_kdiag_full.csv", index=False)
    purple, green, red = "#500778", "#2F6B4F", "#9A3D3D"
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    panels = [
        ("silhouette", "Silhouette (higher=better)", purple),
        ("calinski_harabasz", "Calinski-Harabasz (higher=better)", green),
        ("davies_bouldin", "Davies-Bouldin (lower=better)", red),
        ("BIC", "BIC (lower=better)", purple),
    ]
    for axis, (column, title, color) in zip(axes.flat[:4], panels):
        axis.plot(d["K"], d[column], "-o", color=color)
        axis.set_title(title)
    axes.flat[4].errorbar(d["K"], d["ARI_mean"], yerr=d["ARI_sd"], fmt="-o", color=purple, capsize=3)
    axes.flat[4].set_title("Bootstrap stability ARI (higher=better)")
    axes.flat[4].set_ylim(0, 1.02)
    axes.flat[5].axis("off")
    for axis in axes.flat:
        if axis.has_data():
            axis.set_xlabel("K")
            axis.set_xticks(K_RANGE)
            axis.grid(color="#eeeeee")
            axis.spines[["top", "right"]].set_visible(False)
    fig.suptitle("bus (full week, Hellinger-transformed) – K-diagnostics (GMM)", fontsize=14, y=1.0)
    fig.tight_layout()
    fig.savefig(FIGURES / "hellinger_kdiag_full.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].plot(kdiag["K"], kdiag["activity_eta2"], marker="o", label="activity eta2")
    axes[0].plot(kdiag["K"], kdiag["timing_mean_eta2"], marker="s", label="timing mean eta2")
    axes[0].legend()
    axes[0].set_title("Activity versus timing")
    axes[1].plot(kdiag["K"], kdiag["zero_bin_eta2"], marker="o", color=red)
    axes[1].set_title("Zero-bin eta2")
    axes[2].plot(kdiag["K"], kdiag["bootstrap_ari_mean"], marker="o", label="ARI")
    axes[2].plot(kdiag["K"], kdiag["bootstrap_min_cluster_jaccard_mean"], marker="s", label="min Jaccard")
    axes[2].legend()
    axes[2].set_title("Bootstrap recovery")
    for axis in axes:
        axis.set_xlabel("K")
        axis.set_xticks(K_RANGE)
        axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "hellinger_construct_diagnostics.png", dpi=180)
    plt.close(fig)


def plot_profiles(X_raw: pd.DataFrame, labels_by_k: dict[int, np.ndarray], selected_k: int) -> None:
    labels_index = X_raw.index
    for k in PLOT_K_RANGE:
        labels = labels_by_k[k]
        sizes = np.bincount(labels, minlength=k)
        fig, axes = plt.subplots(k, 3, figsize=(13, max(4, 2.15 * k)), sharex=True, sharey=True)
        axes = np.atleast_2d(axes)
        for cluster in range(k):
            means = X_raw.loc[labels_index[labels == cluster]].mean(axis=0)
            for column, day_type in enumerate(DAY_TYPES):
                axis = axes[cluster, column]
                for direction, color in [("boardings", "#4C78A8"), ("alightings", "#F58518")]:
                    columns = [name for name in X_raw.columns if name.startswith(f"{direction}_{day_type}_")]
                    hours = sorted(int(name.rsplit("_", 1)[1]) for name in columns)
                    values = [means[f"{direction}_{day_type}_{hour}"] for hour in hours]
                    axis.plot(range(12), values, marker="o", markersize=2, color=color, label=direction)
                if cluster == 0:
                    axis.set_title(day_type)
                if column == 0:
                    axis.set_ylabel(f"C{cluster} (n={int(sizes[cluster])})")
                axis.grid(alpha=0.2)
        for axis in axes[-1, :]:
            axis.set_xticks(range(12), ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"], rotation=45)
        axes[0, -1].legend(loc="upper right", fontsize=8)
        fig.suptitle(
            f"Hellinger-derived bus clusters, K={k}\nprofiles shown as mean raw direction shares",
            y=1.01,
        )
        fig.tight_layout()
        out = FIGURES / f"hellinger_profiles_k{k}.png"
        fig.savefig(out, dpi=160, bbox_inches="tight")
        if k == selected_k:
            fig.savefig(FIGURES / "hellinger_selected_profiles.png", dpi=180, bbox_inches="tight")
        plt.close(fig)


def cluster_distribution(frame: pd.DataFrame, group: str, k: int) -> np.ndarray:
    counts = frame.loc[frame["area_group"] == group, "cluster"].value_counts()
    values = np.array([counts.get(cluster, 0) for cluster in range(k)], dtype=float)
    return values / values.sum() if values.sum() else values


def plot_maps_and_geography(index: pd.Index, labels_by_k: dict[int, np.ndarray], selected_k: int) -> pd.DataFrame:
    import geopandas as gpd

    boundaries = gpd.read_file(LSOA_GEOJSON)
    code_column = next(column for column in boundaries.columns if column.lower() == "lsoa21cd")
    boundaries = boundaries[[code_column, "geometry"]].rename(columns={code_column: "LSOA21CD"})
    lookup = pd.read_csv(LSOA_LAD_LOOKUP, usecols=["LSOA21CD", "LAD22CD"])
    lookup["LSOA21CD"] = lookup["LSOA21CD"].astype(str)
    lookup["borough"] = lookup["LAD22CD"].map(TARGET_LADS)
    summaries: list[dict] = []
    borough_rows: list[pd.DataFrame] = []
    for k in PLOT_K_RANGE:
        labels = labels_by_k[k]
        label_frame = pd.DataFrame({"LSOA21CD": index, "cluster": labels})
        mapped = boundaries.merge(label_frame, on="LSOA21CD", how="left")
        fig, axis = plt.subplots(figsize=(8, 8))
        mapped[mapped["cluster"].isna()].plot(ax=axis, color="#e0e0e0", linewidth=0.0)
        mapped[mapped["cluster"].notna()].plot(
            ax=axis, column="cluster", categorical=True, cmap="tab10", linewidth=0.0, legend=True
        )
        axis.set_axis_off()
        axis.set_title(f"Hellinger-derived bus clusters, K={k}\ngrey = outside retained 3,365-LSOA sample")
        fig.tight_layout()
        fig.savefig(FIGURES / f"hellinger_map_k{k}.png", dpi=180)
        if k == selected_k:
            fig.savefig(FIGURES / "hellinger_selected_map.png", dpi=200)
        plt.close(fig)

        target = label_frame.merge(lookup[["LSOA21CD", "borough"]], on="LSOA21CD", how="left")
        target = target[target["borough"].notna()].copy()
        target["area_group"] = np.where(target["borough"].isin(["Westminster", "Camden"]), "central", "outer")
        central = cluster_distribution(target, "central", k)
        outer = cluster_distribution(target, "outer", k)
        summaries.append(
            {
                "K": k,
                "n_matched": len(target),
                "central_outer_total_variation": 0.5 * float(np.abs(central - outer).sum()),
                "central_outer_same_cluster_probability": float(np.dot(central, outer)),
            }
        )
        shares = target.groupby("borough")["cluster"].value_counts(normalize=True).rename("share").reset_index()
        shares["K"] = k
        borough_rows.append(shares)
    summary = pd.DataFrame(summaries)
    summary.to_csv(DATA / "hellinger_howard_central_outer.csv", index=False)
    pd.concat(borough_rows, ignore_index=True).to_csv(DATA / "hellinger_borough_cluster_shares.csv", index=False)
    return summary


def plot_selected_feature_heatmap(signatures: pd.DataFrame, selected_k: int) -> None:
    columns = [
        "log_total_activity_mean",
        "direction_balance_mean",
        "post_midnight_share_mean",
        "deep_night_share_mean",
        "post_midnight_persistence_mean",
        "weekend_ratio_mean",
        "zero_bin_count_mean",
    ]
    labels = ["Activity", "Direction balance", "Post-midnight", "Deep-night", "Persistence", "Weekend ratio", "Zero bins"]
    frame = signatures[signatures["K"] == selected_k].set_index("cluster")[columns]
    standardised = (frame - frame.mean(axis=0)) / frame.std(axis=0, ddof=0).replace(0, np.nan)
    fig, axis = plt.subplots(figsize=(10, max(3.5, 0.75 * selected_k + 1.5)))
    image = axis.imshow(standardised.to_numpy(), cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
    axis.set_xticks(range(len(labels)), labels, rotation=35, ha="right")
    axis.set_yticks(range(selected_k), [f"C{cluster}" for cluster in standardised.index])
    for row in range(standardised.shape[0]):
        for column in range(standardised.shape[1]):
            value = standardised.iloc[row, column]
            axis.text(column, row, f"{value:.2f}", ha="center", va="center", fontsize=8)
    axis.set_title(f"Selected Hellinger cluster characteristics, K={selected_k}\ncolumn-standardised cluster means")
    fig.colorbar(image, ax=axis, label="z-score across clusters")
    fig.tight_layout()
    fig.savefig(FIGURES / "hellinger_selected_feature_heatmap.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_reports(
    n: int,
    grid: pd.DataFrame,
    family: str,
    family_note: str,
    kdiag: pd.DataFrame,
    screen: pd.DataFrame,
    selection: dict,
    comparison: pd.DataFrame,
    aris: pd.DataFrame,
    geography: pd.DataFrame,
    signatures: pd.DataFrame,
    bootstrap_n: int,
) -> None:
    selected_k = selection["selected_k"]
    best_by_cov = (
        grid.sort_values("BIC").groupby("covariance", as_index=False).first()[
            ["covariance", "K", "BIC", "min_cluster_n", "min_cluster_share"]
        ]
    )
    selected_comparison = comparison[comparison["K"] == selected_k]
    selected_aris = aris[aris["K"] == selected_k]
    selected_signatures = signatures[signatures["K"] == selected_k]
    acceptance = "PASS" if selection["transform_acceptance_pass"] else "FAIL"
    report = f"""## Material Passport

- Origin Skill: academic-research-suite/experiment-agent
- Origin Mode: run + validate
- Verification Status: ANALYZED
- Version Label: bus_hellinger_transform_v1

# Hellinger-transformed bus clustering: results

## Fixed design

- n={n:,} LSOAs; exact official hub-first raw-share sample.
- Two independent 36-cell direction compositions; transform `sqrt(p)`.
- Exact zeros preserved; no pseudo-count or alpha shrinkage.
- GMM covariance grid={COVARIANCES}; K=2..12; n_init={N_INIT}; seed={SEED}.
- Bootstrap K=2..8; {bootstrap_n} replicates; bootstrap n_init={BOOTSTRAP_N_INIT}.
- Absolute BIC is used only within the Hellinger feature space.

## BIC minima by covariance

{best_by_cov.to_markdown(index=False, floatfmt='.4f')}

{family_note}

Reporting covariance family: **{family}**.

## K diagnostics

{kdiag[["K", "BIC", "silhouette", "davies_bouldin", "zero_bin_eta2", "activity_eta2", "timing_mean_eta2", "min_cluster_share", "bootstrap_ari_mean", "bootstrap_min_cluster_jaccard_mean"]].to_markdown(index=False, floatfmt='.4f')}

## Pre-declared selection screen

{screen[["K", "BIC", "min_cluster_share", "bootstrap_ari_mean", "bootstrap_min_cluster_jaccard_mean", "size_pass", "stability_pass", "jaccard_pass", "structural_screen_pass", "selected"]].to_markdown(index=False, floatfmt='.4f')}

Selected reporting K: **{selected_k}** ({selection['selection_basis']}).

## Transform acceptance verdict: **{acceptance}**

- Zero-bin eta2 reduction versus CLR at K={selected_k}: {selection['zero_eta2_reduction_vs_clr']:.1%}
  (gate >= {selection['zero_reduction_gate']:.0%}; pass={selection['zero_gate_pass']}).
- Timing eta2 retention versus CLR: {selection['timing_eta2_retention_vs_clr']:.1%}
  (gate >= {selection['timing_retention_gate']:.0%}; pass={selection['timing_gate_pass']}).
- Structural size/stability/Jaccard screen pass={selection['structural_screen_pass']}.

Passing this screen means Hellinger is a defensible zero-preserving replacement
candidate under the declared diagnostics. It does not prove that remaining zeros
represent demand rather than service availability.

## Same-K transform comparison (selected K)

{selected_comparison.to_markdown(index=False, floatfmt='.4f')}

Silhouette values are reported for completeness but are not directly comparable
across transformed coordinate spaces. Raw-metric eta2 and label ARI are directly
comparable because they use the same LSOAs and external metrics.

{selected_aris.to_markdown(index=False, floatfmt='.4f')}

## Selected cluster signatures

{selected_signatures.to_markdown(index=False, floatfmt='.4f')}

## Spatial diagnostic

{geography[geography['K'] == selected_k].to_markdown(index=False, floatfmt='.4f')}

## Figure inventory

- K diagnostics: `outputs/figures/hellinger_kdiag_full.png`.
- Construct diagnostics: `outputs/figures/hellinger_construct_diagnostics.png`.
- Profiles: `hellinger_profiles_k2.png` through `hellinger_profiles_k8.png`.
- Maps: `hellinger_map_k2.png` through `hellinger_map_k8.png`.
- Selected outputs: `hellinger_selected_profiles.png`,
  `hellinger_selected_map.png`, `hellinger_selected_feature_heatmap.png`.
"""
    (REPORT / "HELLINGER_RESULTS.md").write_text(report, encoding="utf-8")

    geo_report = f"""# Hellinger-derived clusters: temporal profiles and spatial characteristics

Selected reporting K: **{selected_k}**.

{geography.to_markdown(index=False, floatfmt='.4f')}

The temporal profile panels show mean raw direction shares for interpretability;
the labels are fitted only in Hellinger space. The maps show all retained LSOAs
and use grey for London LSOAs outside the retained sample.

Selected figures:

- `outputs/figures/hellinger_selected_profiles.png`
- `outputs/figures/hellinger_selected_map.png`
- `outputs/figures/hellinger_selected_feature_heatmap.png`
"""
    (REPORT / "HELLINGER_PROFILES_MAPS_GEOGRAPHIC.md").write_text(geo_report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", type=int, default=20)
    args = parser.parse_args()
    started = time.time()

    log("[1/10] Loading and validating official raw-share inputs")
    X_raw, metrics = load_inputs()
    log(f"  n={len(X_raw)}, features={X_raw.shape[1]}, exact zeros={int(X_raw.eq(0).sum().sum())}")

    log("[2/10] Applying zero-preserving sqrt(p) transform")
    X = build_hellinger_features(X_raw)
    Xv = X.to_numpy(dtype=float)

    grid, family, global_best_k, family_note = run_bic_grid(Xv)
    log(f"  global BIC K={global_best_k}; reporting family={family}; {family_note}")
    kdiag, labels_by_k = run_k_diagnostics(X, metrics, family)
    bootstrap = run_bootstrap(Xv, labels_by_k, family, args.bootstrap)
    boot_summary = bootstrap.groupby("K", as_index=False).agg(
        bootstrap_ari_mean=("ARI", "mean"),
        bootstrap_ari_sd=("ARI", "std"),
        bootstrap_min_cluster_jaccard_mean=("min_matched_cluster_jaccard", "mean"),
    )
    kdiag = kdiag.merge(boot_summary, on="K", how="left")
    kdiag.to_csv(DIAGNOSTICS / "hellinger_kdiag.csv", index=False)

    log("[6/10] Same-K raw/CLR/Hellinger comparisons and reporting-K screen")
    comparison, aris = add_comparators(kdiag, metrics, X.index)
    selected_k, screen, selection = select_reporting_k(kdiag, comparison)
    log(f"  selected K={selected_k}; transform acceptance={selection['transform_acceptance_pass']}")

    log("[7/10] Cluster homogeneity and raw-metric signatures")
    _, signatures = write_cluster_summaries(Xv, metrics, labels_by_k)

    log("[8/10] K diagnostics, temporal profiles, and spatial figures")
    plot_k_diagnostics(grid, kdiag, bootstrap)
    plot_profiles(X_raw, labels_by_k, selected_k)
    geography = plot_maps_and_geography(X.index, labels_by_k, selected_k)
    plot_selected_feature_heatmap(signatures, selected_k)

    log("[9/10] Reports and provenance")
    write_reports(
        len(X), grid, family, family_note, kdiag, screen, selection,
        comparison, aris, geography, signatures, args.bootstrap,
    )
    elapsed = time.time() - started
    manifest = pd.DataFrame(
        [
            {"role": "clustering_input", "path": str(RAW_SHARE_X), "sha256": sha256(RAW_SHARE_X)},
            {"role": "raw_metrics", "path": str(RAW_METRICS), "sha256": sha256(RAW_METRICS)},
            {"role": "boundary_input", "path": str(LSOA_GEOJSON), "sha256": sha256(LSOA_GEOJSON)},
            {"role": "geographic_lookup", "path": str(LSOA_LAD_LOOKUP), "sha256": sha256(LSOA_LAD_LOOKUP)},
        ]
    )
    manifest.to_csv(OUT / "input_manifest.csv", index=False)
    (OUT / "run_environment.json").write_text(
        json.dumps(
            {
                "elapsed_seconds": elapsed,
                "seed": SEED,
                "n_init": N_INIT,
                "bootstrap_replicates": args.bootstrap,
                "transform": "sqrt(direction_normalised_share)",
                "zero_replacement": None,
                "python": sys.version,
                "platform": platform.platform(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log(f"[10/10] Complete in {elapsed:.1f}s: {REPORT / 'HELLINGER_RESULTS.md'}")


if __name__ == "__main__":
    main()
