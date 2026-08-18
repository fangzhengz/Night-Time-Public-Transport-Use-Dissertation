"""Within-cluster homogeneity check for the bottom-20%-excluded K=3/K=4
candidates from 02b_bottom20_full_covariance_kdiag.py and
03_bottom20_k3_k4_profiles_and_maps.py, computed the same way as the
official-folder version (巴士聚类错误修改/src/03_cluster_homogeneity.py) so the
two thresholds are directly comparable.

Reuses the labels already saved by 03_bottom20_k3_k4_profiles_and_maps.py and
the raw metrics already computed in
rq1_bus_hub_first_alpha_grid_screen/outputs/data/hub_first_raw_metrics.csv
(same 3,593-LSOA hub-first sample this whole folder has used throughout).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_samples

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FYP = ROOT.parent

X_INPUT = (
    FYP / "rq1_bus_hub_first_reclustering_alpha_sensitivity" / "outputs" / "features"
    / "X_bus_fullweek_alpha0_fixed_sample.parquet"
)
META_INPUT = FYP / "rq1_bus_hub_first_reclustering" / "outputs" / "features" / "bus_fullweek_meta_alpha5.csv"
METRICS_INPUT = FYP / "rq1_bus_hub_first_alpha_grid_screen" / "outputs" / "data" / "hub_first_raw_metrics.csv"

OUT = ROOT / "outputs"
DIAGNOSTICS = OUT / "diagnostics"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
LABELS = OUT / "labels"

EXCLUDE_QUANTILE = 0.20
CANDIDATE_KS = [3, 4]
RAW_METRIC_COLUMNS = [
    "log_total_activity",
    "direction_balance",
    "post_midnight_share",
    "deep_night_share",
    "post_midnight_persistence",
    "weekend_ratio",
]


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    X = pd.read_parquet(X_INPUT)
    X.index = pd.Index(X.index.astype(str), name="lsoa")
    meta = pd.read_csv(META_INPUT)
    meta["lsoa"] = meta["lsoa"].astype(str)
    meta = meta.set_index("lsoa").reindex(X.index)
    metrics = pd.read_csv(METRICS_INPUT)
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    metrics = metrics.set_index("lsoa").reindex(X.index)

    cutoff = float(meta["total_activity"].quantile(EXCLUDE_QUANTILE))
    keep_mask = meta["total_activity"].to_numpy(dtype=float) >= cutoff
    core_units = X.index[keep_mask]
    X_core = X.loc[core_units]
    metrics_core = metrics.loc[core_units]
    Xv = X_core.to_numpy(dtype=float)
    grand_centroid = Xv.mean(axis=0)
    grand_mean_distance = float(np.linalg.norm(Xv - grand_centroid, axis=1).mean())
    log(f"n_core={len(Xv)} (cutoff={cutoff:.2f}); grand-mean distance to overall centroid={grand_mean_distance:.4f}")

    all_rows = []
    dispersion_rows = []
    for k in CANDIDATE_KS:
        label_path = LABELS / f"bottom20_full_k{k}_labels.csv"
        if not label_path.exists():
            raise FileNotFoundError(f"Missing {label_path}; run 03_bottom20_k3_k4_profiles_and_maps.py first")
        labels_df = pd.read_csv(label_path)
        labels_df["lsoa"] = labels_df["lsoa"].astype(str)
        labels_df = labels_df.set_index("lsoa").reindex(core_units)
        labels = labels_df["cluster"].to_numpy(dtype=int)

        sil_samples = silhouette_samples(Xv, labels)
        log(f"K={k}: overall silhouette mean={sil_samples.mean():.4f}")

        for cluster in range(k):
            mask = labels == cluster
            members = Xv[mask]
            centroid = members.mean(axis=0)
            dist_to_own_centroid = np.linalg.norm(members - centroid, axis=1)
            row = {
                "K": k,
                "cluster": cluster,
                "n": int(mask.sum()),
                "share": float(mask.mean()),
                "mean_silhouette": float(sil_samples[mask].mean()),
                "median_silhouette": float(np.median(sil_samples[mask])),
                "mean_dist_to_own_centroid": float(dist_to_own_centroid.mean()),
                "relative_compactness_vs_sample": float(dist_to_own_centroid.mean() / grand_mean_distance),
            }
            for column in RAW_METRIC_COLUMNS:
                values = metrics_core.loc[mask, column].dropna()
                mean = float(values.mean())
                std = float(values.std())
                row[f"{column}_mean"] = mean
                row[f"{column}_std"] = std
                row[f"{column}_cv"] = float(std / abs(mean)) if mean != 0 else float("nan")
                row[f"{column}_iqr"] = float(values.quantile(0.75) - values.quantile(0.25))
            all_rows.append(row)
            for column in RAW_METRIC_COLUMNS:
                for value in metrics_core.loc[mask, column].dropna().to_numpy():
                    dispersion_rows.append({"K": k, "cluster": cluster, "metric": column, "value": value})

        log(
            "  relative compactness by cluster: "
            + ", ".join(f"C{row['cluster']}={row['relative_compactness_vs_sample']:.3f}" for row in all_rows if row["K"] == k)
        )
        log(
            "  silhouette by cluster: "
            + ", ".join(f"C{row['cluster']}={row['mean_silhouette']:.3f}" for row in all_rows if row["K"] == k)
        )

    homogeneity = pd.DataFrame(all_rows)
    homogeneity.to_csv(DIAGNOSTICS / "bottom20_cluster_homogeneity.csv", index=False)
    dispersion = pd.DataFrame(dispersion_rows)
    dispersion.to_csv(DIAGNOSTICS / "bottom20_cluster_homogeneity_raw_values.csv", index=False)

    log("Writing boxplot figures")
    plot_metrics = ["log_total_activity", "post_midnight_share", "deep_night_share", "post_midnight_persistence"]
    for k in CANDIDATE_KS:
        fig, axes = plt.subplots(1, len(plot_metrics), figsize=(4.2 * len(plot_metrics), 4.2))
        for ax, metric in zip(axes, plot_metrics):
            data = [
                dispersion[(dispersion["K"] == k) & (dispersion["cluster"] == c) & (dispersion["metric"] == metric)]["value"]
                for c in range(k)
            ]
            ax.boxplot(data, tick_labels=[f"C{c}" for c in range(k)], showfliers=False)
            ax.set_title(metric)
            ax.grid(alpha=0.2)
        fig.suptitle(f"Bottom-20%-excluded: within-cluster dispersion, K={k}")
        fig.tight_layout()
        fig.savefig(FIGURES / f"bottom20_homogeneity_boxplots_k{k}.png", dpi=160)
        plt.close(fig)

    write_report(homogeneity, grand_mean_distance, cutoff, len(Xv))
    log(str(REPORT / "CLUSTER_HOMOGENEITY_BOTTOM20.md"))


def write_report(homogeneity: pd.DataFrame, grand_mean_distance: float, cutoff: float, n_core: int) -> None:
    display_cols = [
        "K", "cluster", "n", "share", "mean_silhouette", "relative_compactness_vs_sample",
        "log_total_activity_mean", "log_total_activity_cv",
        "post_midnight_share_mean", "post_midnight_share_cv",
        "deep_night_share_mean", "deep_night_share_cv",
        "post_midnight_persistence_mean", "post_midnight_persistence_cv",
    ]
    lines = [
        "# Within-cluster homogeneity: bottom-20%-excluded K=3 and K=4",
        "",
        f"Same diagnostic as `巴士聚类错误修改/outputs/report/CLUSTER_HOMOGENEITY.md`,",
        f"computed here on the bottom-20%-by-total-activity-excluded sample "
        f"(cutoff={cutoff:.2f}, n_core={n_core}) for direct comparison against the "
        "adopted min(boardings,alightings)>=36 threshold.",
        "",
        f"Whole-sample average distance to the grand centroid: {grand_mean_distance:.4f}.",
        "`relative_compactness_vs_sample` below 1 means the cluster is tighter",
        "than the retained sample as a whole.",
        "",
        "## Summary",
        "",
        homogeneity[display_cols].to_markdown(index=False, floatfmt=".4f"),
        "",
        "Full table (std, IQR, all six raw metrics):",
        "`outputs/diagnostics/bottom20_cluster_homogeneity.csv`.",
        "Boxplots: `outputs/figures/bottom20_homogeneity_boxplots_k{3,4}.png`.",
    ]
    (REPORT / "CLUSTER_HOMOGENEITY_BOTTOM20.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
