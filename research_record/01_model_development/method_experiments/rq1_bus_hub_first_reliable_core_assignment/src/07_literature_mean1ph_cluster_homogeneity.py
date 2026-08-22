"""Within-cluster homogeneity check for the literature mean->=1/hour
threshold's K=3/K=4 candidates from 04_literature_mean1ph_k3_k4_maps.py,
computed the same way as 05_bottom20_cluster_homogeneity.py (and the
official-folder version, 巴士聚类错误修改/src/03_cluster_homogeneity.py) so
this threshold and the bottom-20% comparator are directly comparable --
05_bottom20_cluster_homogeneity.py's own docstring already says this, but
the literature_mean1ph side of it was never written.

Reuses the labels already saved by 04_literature_mean1ph_k3_k4_maps.py
(outputs/labels/literature_mean1ph_full_k{3,4}_labels.csv, which already
carries its own retained_for_fit mask) and the raw metrics already computed
in rq1_bus_hub_first_alpha_grid_screen/outputs/data/hub_first_raw_metrics.csv.
Does not refit anything.
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
METRICS_INPUT = FYP / "rq1_bus_hub_first_alpha_grid_screen" / "outputs" / "data" / "hub_first_raw_metrics.csv"

OUT = ROOT / "outputs"
DIAGNOSTICS = OUT / "diagnostics"
FIGURES = OUT / "figures"
REPORT = OUT / "report"
LABELS = OUT / "labels"

CANDIDATE_KS = [3, 4]
MIN_PER_DIRECTION = 36.0
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
    metrics = pd.read_csv(METRICS_INPUT)
    metrics["lsoa"] = metrics["lsoa"].astype(str)
    metrics = metrics.set_index("lsoa").reindex(X.index)

    all_rows = []
    dispersion_rows = []
    grand_mean_distance_by_k = {}
    for k in CANDIDATE_KS:
        label_path = LABELS / f"literature_mean1ph_full_k{k}_labels.csv"
        if not label_path.exists():
            raise FileNotFoundError(f"Missing {label_path}; run 04_literature_mean1ph_k3_k4_maps.py first")
        labels_df = pd.read_csv(label_path)
        labels_df["lsoa"] = labels_df["lsoa"].astype(str)
        labels_df = labels_df.set_index("lsoa").reindex(X.index)
        core_mask = labels_df["retained_for_fit"].fillna(False).to_numpy(dtype=bool)

        core_units = X.index[core_mask]
        X_core = X.loc[core_units]
        metrics_core = metrics.loc[core_units]
        Xv = X_core.to_numpy(dtype=float)
        grand_centroid = Xv.mean(axis=0)
        grand_mean_distance = float(np.linalg.norm(Xv - grand_centroid, axis=1).mean())
        grand_mean_distance_by_k[k] = grand_mean_distance
        labels = labels_df.loc[core_units, "cluster"].to_numpy(dtype=int)
        log(f"K={k}: n_core={len(Xv)}; grand-mean distance to overall centroid={grand_mean_distance:.4f}")

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
    homogeneity.to_csv(DIAGNOSTICS / "literature_mean1ph_cluster_homogeneity.csv", index=False)
    dispersion = pd.DataFrame(dispersion_rows)
    dispersion.to_csv(DIAGNOSTICS / "literature_mean1ph_cluster_homogeneity_raw_values.csv", index=False)

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
        fig.suptitle(f"Literature mean>=1/hour threshold: within-cluster dispersion, K={k}")
        fig.tight_layout()
        fig.savefig(FIGURES / f"literature_mean1ph_homogeneity_boxplots_k{k}.png", dpi=160)
        plt.close(fig)

    write_report(homogeneity, grand_mean_distance_by_k)
    log(str(REPORT / "CLUSTER_HOMOGENEITY_LITERATURE_MEAN1PH.md"))


def write_report(homogeneity: pd.DataFrame, grand_mean_distance_by_k: dict) -> None:
    display_cols = [
        "K", "cluster", "n", "share", "mean_silhouette", "relative_compactness_vs_sample",
        "log_total_activity_mean", "log_total_activity_cv",
        "post_midnight_share_mean", "post_midnight_share_cv",
        "deep_night_share_mean", "deep_night_share_cv",
        "post_midnight_persistence_mean", "post_midnight_persistence_cv",
    ]
    distances = "; ".join(f"K={k}: {v:.4f}" for k, v in grand_mean_distance_by_k.items())
    lines = [
        "# Within-cluster homogeneity: literature mean>=1/hour threshold, K=3 and K=4",
        "",
        "Same diagnostic as `CLUSTER_HOMOGENEITY_BOTTOM20.md` and "
        "`巴士聚类错误修改/outputs/report/CLUSTER_HOMOGENEITY.md`, computed here on the "
        f"min(boardings,alightings)>={MIN_PER_DIRECTION:.0f} sample "
        "(n_core=3,365, 93.65% retained) for direct comparison against the "
        "bottom-20%-by-total-activity comparator.",
        "",
        f"Whole-sample average distance to the grand centroid, by K: {distances}.",
        "`relative_compactness_vs_sample` below 1 means the cluster is tighter",
        "than the retained sample as a whole.",
        "",
        "## Summary",
        "",
        homogeneity[display_cols].to_markdown(index=False, floatfmt=".4f"),
        "",
        "Full table (std, IQR, all six raw metrics):",
        "`outputs/diagnostics/literature_mean1ph_cluster_homogeneity.csv`.",
        "Boxplots: `outputs/figures/literature_mean1ph_homogeneity_boxplots_k{3,4}.png`.",
    ]
    (REPORT / "CLUSTER_HOMOGENEITY_LITERATURE_MEAN1PH.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
